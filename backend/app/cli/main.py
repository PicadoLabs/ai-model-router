import sys
import os
import asyncio
import httpx
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# Set UTF-8 encoding support for Windows terminals
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.config.settings import get_settings
from app.analyzer.heuristics import analyze_request_heuristics
from app.router.engine import route_request
from app.storage.database import init_db, AsyncSessionLocal
from app.storage.models import ModelRecord, RoutingPolicyRecord
from app.api.routes import db_model_to_meta
from app.fallback.handler import execute_with_fallback
from sqlalchemy import select

app = typer.Typer(help="Model Router: Intelligent LLM Request Routing Platform")
console = Console(safe_box=True)
settings = get_settings()


@app.command()
def doctor():
    """Run environment, connectivity, and dependency health checks."""
    console.print(Panel.fit("[bold cyan]Model Router Diagnostics (modelrouter doctor)[/bold cyan]"))
    
    # 1. Python Check
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    console.print(f" [green][OK][/green] Python: [bold]{py_ver}[/bold]")
    
    # 2. Database Check
    try:
        asyncio.run(init_db())
        console.print(" [green][OK][/green] SQLite Database: [bold]Initialized & Ready[/bold]")
    except Exception as exc:
        console.print(f" [red][FAIL][/red] Database Error: {exc}")

    # 3. Ollama Connectivity Check
    ollama_ok = False
    try:
        r = httpx.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=1.5)
        if r.status_code == 200:
            models = [m.get("name") for m in r.json().get("models", [])]
            console.print(f" [green][OK][/green] Ollama (Local): [bold]Connected[/bold] ({len(models)} local models found)")
            ollama_ok = True
    except Exception:
        pass
    if not ollama_ok:
        console.print(f" [yellow][!][/yellow] Ollama (Local): [dim]Not running on {settings.OLLAMA_BASE_URL} (Optional, local fallback available)[/dim]")

    # 4. Mock Engine
    console.print(" [green][OK][/green] Mock Engine: [bold]Ready (Zero API keys required)[/bold]")

    # 5. External Providers
    if settings.OPENAI_API_KEY:
        console.print(" [green][OK][/green] OpenAI Provider: [bold]API Key Configured in .env[/bold]")
    else:
        console.print(" [yellow][!][/yellow] OpenAI Provider: [dim]Not configured (Optional)[/dim]")

    if settings.ANTHROPIC_API_KEY:
        console.print(" [green][OK][/green] Anthropic Provider: [bold]API Key Configured in .env[/bold]")
    else:
        console.print(" [yellow][!][/yellow] Anthropic Provider: [dim]Not configured (Optional)[/dim]")

    if settings.GEMINI_API_KEY:
        console.print(" [green][OK][/green] Gemini Provider: [bold]API Key Configured in .env[/bold]")
    else:
        console.print(" [yellow][!][/yellow] Gemini Provider: [dim]Not configured (Optional)[/dim]")

    console.print("\n[bold green]Ready for local-first intelligent routing![/bold green]\n")


@app.command()
def models():
    """List all registered candidate models and their capability scores."""
    async def _list():
        await init_db()
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(ModelRecord).order_by(ModelRecord.tier, ModelRecord.name))
            records = res.scalars().all()
            
            table = Table(title="Model Router Registry", border_style="bright_blue")
            table.add_column("Model ID", style="cyan", no_wrap=True)
            table.add_column("Tier", style="magenta")
            table.add_column("Provider", style="green")
            table.add_column("Context", style="yellow")
            table.add_column("Quality", style="blue")
            table.add_column("Speed", style="cyan")
            table.add_column("Cost / 1K In/Out", style="white")

            for m in records:
                cost_str = f"${m.cost_per_input_token*1000:.4f} / ${m.cost_per_output_token*1000:.4f}" if m.cost_per_input_token > 0 else "Free ($0)"
                table.add_row(
                    m.id,
                    m.tier,
                    m.provider,
                    f"{m.context_window:,}",
                    f"{m.quality_score*100:.0f}%",
                    f"{m.speed_score*100:.0f}%",
                    cost_str,
                )
            console.print(table)

    asyncio.run(_list())


@app.command()
def route(
    prompt: str = typer.Argument(..., help="Prompt text to route"),
    policy: str = typer.Option("balanced", "--policy", "-p", help="Routing policy to use"),
):
    """Analyze prompt and explain why the optimal model was selected (Dry Run)."""
    async def _route():
        await init_db()
        analysis = analyze_request_heuristics(prompt)
        
        async with AsyncSessionLocal() as db:
            res_m = await db.execute(select(ModelRecord).filter_by(is_active=True))
            models = [db_model_to_meta(m) for m in res_m.scalars().all()]
            
            res_p = await db.execute(select(RoutingPolicyRecord).filter_by(id=policy))
            pol = res_p.scalar_one_or_none()
            weights = {
                "quality_weight": pol.quality_weight if pol else 0.35,
                "cost_weight": pol.cost_weight if pol else 0.25,
                "speed_weight": pol.speed_weight if pol else 0.20,
                "capability_weight": pol.capability_weight if pol else 0.15,
                "reliability_weight": pol.reliability_weight if pol else 0.05,
            }

            decision = route_request(
                analysis=analysis,
                available_models=models,
                policy_weights=weights,
                policy_name=policy,
            )

            console.print(Panel.fit(
                f"[bold white]Prompt:[/bold white] \"{prompt}\"\n"
                f"[bold cyan]Task Type:[/bold cyan] {analysis.task_type.value} | [bold cyan]Complexity:[/bold cyan] {analysis.complexity_label.value} ({analysis.complexity:.2f})\n"
                f"[bold green]Selected Model:[/bold green] [bold yellow]{decision.selected_model_name}[/bold yellow] ({decision.selected_model})\n"
                f"[bold magenta]Confidence:[/bold magenta] {decision.confidence * 100:.0f}%\n"
                f"[bold blue]Estimated Latency:[/bold blue] {decision.estimated_latency_ms:.0f}ms | [bold blue]Estimated Cost:[/bold blue] ${decision.estimated_cost_usd:.6f}",
                title="ROUTING DECISION",
                border_style="bright_blue",
            ))

            console.print("[bold cyan]Why this model?[/bold cyan]")
            for r in decision.reasons:
                console.print(f"  [green]+[/green] {r}")

            if decision.rejected_candidates:
                console.print("\n[bold red]Rejected Candidates:[/bold red]")
                for cid, reason in decision.rejected_candidates.items():
                    console.print(f"  [dim]- {cid}: {reason}[/dim]")

    asyncio.run(_route())


@app.command()
def run(
    prompt: str = typer.Argument(..., help="Prompt to route and execute"),
    policy: str = typer.Option("balanced", "--policy", "-p", help="Routing policy to use"),
):
    """Route request and execute inference through the chosen provider."""
    async def _run():
        await init_db()
        analysis = analyze_request_heuristics(prompt)
        
        async with AsyncSessionLocal() as db:
            res_m = await db.execute(select(ModelRecord).filter_by(is_active=True))
            models = [db_model_to_meta(m) for m in res_m.scalars().all()]
            
            decision = route_request(
                analysis=analysis,
                available_models=models,
                policy_weights={"quality_weight": 0.35, "cost_weight": 0.25, "speed_weight": 0.20, "capability_weight": 0.15, "reliability_weight": 0.05},
                policy_name=policy,
            )

            console.print(f"[bold cyan]Routing to:[/bold cyan] {decision.selected_model} via provider: {decision.provider}...")
            
            resp, fallback_used, orig_m, fb_reason = await execute_with_fallback(
                prompt=prompt,
                selected_model_id=decision.selected_model,
                selected_provider_id=decision.provider,
                all_models=models,
            )

            console.print(Panel(
                resp.content,
                title=f"RESPONSE from {resp.model} ({'FALLBACK: ' + orig_m if fallback_used else 'PRIMARY'})",
                subtitle=f"Latency: {resp.provider_latency_ms:.0f}ms | Tokens: {resp.total_tokens}",
                border_style="green" if not fallback_used else "yellow",
            ))

    asyncio.run(_run())


@app.command()
def traffic(limit: int = 10):
    """View recent routed traffic log."""
    async def _traffic():
        await init_db()
        from app.storage.models import RequestRecord
        from sqlalchemy import desc
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(RequestRecord).order_by(desc(RequestRecord.timestamp)).limit(limit))
            records = res.scalars().all()
            
            table = Table(title="Recent Routed Traffic Feed", border_style="bright_blue")
            table.add_column("Time", style="dim")
            table.add_column("Task", style="cyan")
            table.add_column("Selected Model", style="green")
            table.add_column("Latency", style="yellow")
            table.add_column("Cost", style="magenta")
            table.add_column("Prompt Sample", style="white")

            for r in records:
                t_str = r.timestamp.strftime("%H:%M:%S") if r.timestamp else "N/A"
                table.add_row(
                    t_str,
                    r.task_type,
                    r.selected_model,
                    f"{r.total_latency_ms:.0f}ms",
                    f"${r.estimated_cost:.5f}",
                    r.prompt[:40] + ("..." if len(r.prompt) > 40 else ""),
                )
            console.print(table)

    asyncio.run(_traffic())


@app.command()
def analytics():
    """Display system-wide routing performance and cost savings analytics."""
    async def _analytics():
        await init_db()
        from app.analytics.service import get_system_analytics
        async with AsyncSessionLocal() as db:
            data = await get_system_analytics(db)
            console.print(Panel.fit(
                f"[bold cyan]Total Routed Requests:[/bold cyan] {data['total_requests']}\n"
                f"[bold green]Average Latency:[/bold green] {data['avg_latency_ms']}ms (Routing overhead: {data['avg_routing_latency_ms']}ms)\n"
                f"[bold yellow]Total Cost:[/bold yellow] ${data['total_cost_usd']:.6f}\n"
                f"[bold magenta]Cost Saved vs Baseline:[/bold magenta] ${data['savings']['cost_saved_usd']:.6f} ({data['savings']['savings_percentage']}%)\n"
                f"[bold blue]Fallback Rate:[/bold blue] {data['fallback_rate_percent']}%\n",
                title="MODEL ROUTER ANALYTICS OVERVIEW",
                border_style="bright_blue",
            ))

    asyncio.run(_analytics())


if __name__ == "__main__":
    app()
