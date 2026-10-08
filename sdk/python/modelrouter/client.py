import os
import json
import time
import httpx
from typing import Optional, List, Dict, Any, Union, AsyncGenerator, Generator
from modelrouter.types import (
    ChatMessage,
    ChatCompletion,
    ChatCompletionChoice,
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    ChatCompletionChunkDelta,
    RoutingDecision,
    ModelInfo,
    Usage,
)
from modelrouter.exceptions import (
    ModelRouterError,
    AuthenticationError,
    RateLimitError,
    APIConnectionError,
    APIStatusError,
    RoutingError,
)


def _handle_error_response(status_code: int, text: str):
    try:
        body = json.loads(text)
        detail = body.get("detail", text)
    except Exception:
        body = text
        detail = text

    if status_code in (401, 403):
        raise AuthenticationError(f"Authentication failed: {detail}", status_code=status_code, response_body=body)
    elif status_code == 429:
        raise RateLimitError(f"Rate limit exceeded: {detail}", status_code=status_code, response_body=body)
    elif status_code == 422:
        raise RoutingError(f"Invalid routing request or parameter: {detail}", status_code=status_code, response_body=body)
    else:
        raise APIStatusError(f"Model Router error ({status_code}): {detail}", status_code=status_code, response_body=body)


# ---------------------------------------------------------------------------
# Sync Client
# ---------------------------------------------------------------------------

class SyncCompletions:
    def __init__(self, client: "ModelRouter"):
        self._client = client

    def create(
        self,
        messages: Optional[List[Union[ChatMessage, Dict[str, str]]]] = None,
        prompt: Optional[str] = None,
        policy: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        headers: Optional[Dict[str, str]] = None,
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        # Normalize prompt from messages or prompt
        if prompt is None:
            if not messages:
                raise ValueError("Either 'prompt' or 'messages' must be provided.")
            # Extract last user message or concat messages
            user_msgs = [m["content"] if isinstance(m, dict) else m.content for m in messages if (m["role"] if isinstance(m, dict) else m.role) == "user"]
            prompt = user_msgs[-1] if user_msgs else "\n".join(m["content"] if isinstance(m, dict) else m.content for m in messages)

        eff_policy = policy or self._client.policy
        req_payload = {
            "prompt": prompt,
            "policy": eff_policy,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        if stream:
            return self._stream_create(req_payload, headers=headers)
        
        url = f"{self._client.base_url.rstrip('/')}/api/route/run"
        req_headers = self._client._get_headers(headers)

        try:
            with httpx.Client(timeout=self._client.timeout) as http_client:
                res = http_client.post(url, json=req_payload, headers=req_headers)
        except httpx.ConnectError as exc:
            raise APIConnectionError(f"Failed to connect to Model Router at {self._client.base_url}: {exc}")
        except httpx.TimeoutException as exc:
            raise APIConnectionError(f"Request to Model Router timed out after {self._client.timeout}s: {exc}")

        if res.status_code != 200:
            _handle_error_response(res.status_code, res.text)

        data = res.json()
        decision = data.get("decision", {})
        resp = data.get("response", {})
        selected_m = decision.get("selected_model", resp.get("model", "unknown"))

        return ChatCompletion(
            id=decision.get("decision_id", f"cmpl-{int(time.time()*1000)}"),
            created=int(time.time()),
            model=selected_m,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=resp.get("content", "")),
                    finish_reason="stop",
                )
            ],
            usage=Usage(
                prompt_tokens=resp.get("input_tokens", 0),
                completion_tokens=resp.get("output_tokens", 0),
                total_tokens=resp.get("total_tokens", 0),
                estimated_cost_usd=decision.get("estimated_cost_usd"),
            ),
            routing_metadata=decision,
        )

    def _stream_create(self, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Generator[ChatCompletionChunk, None, None]:
        url = f"{self._client.base_url.rstrip('/')}/api/route/stream"
        req_headers = self._client._get_headers(headers)
        req_headers["Accept"] = "text/event-stream"

        try:
            with httpx.Client(timeout=self._client.timeout) as http_client:
                with http_client.stream("POST", url, json=payload, headers=req_headers) as response:
                    if response.status_code != 200:
                        _handle_error_response(response.status_code, response.read().decode())

                    chunk_id = f"chatcmpl-chunk-{int(time.time()*1000)}"
                    for line in response.iter_lines():
                        if not line or line.startswith(":"):
                            continue
                        if line.startswith("data: "):
                            raw_data = line[6:].strip()
                            if raw_data == "[DONE]":
                                break
                            try:
                                parsed = json.loads(raw_data)
                                text_delta = parsed.get("token") or parsed.get("content") or parsed.get("text", "")
                                sel_model = parsed.get("model", "routed-model")
                                yield ChatCompletionChunk(
                                    id=chunk_id,
                                    created=int(time.time()),
                                    model=sel_model,
                                    choices=[
                                        ChatCompletionChunkChoice(
                                            index=0,
                                            delta=ChatCompletionChunkDelta(content=text_delta),
                                        )
                                    ],
                                    routing_metadata=parsed.get("routing_decision"),
                                )
                            except json.JSONDecodeError:
                                yield ChatCompletionChunk(
                                    id=chunk_id,
                                    created=int(time.time()),
                                    model="routed-model",
                                    choices=[
                                        ChatCompletionChunkChoice(
                                            index=0,
                                            delta=ChatCompletionChunkDelta(content=raw_data),
                                        )
                                    ],
                                )
        except httpx.ConnectError as exc:
            raise APIConnectionError(f"Failed to connect to Model Router stream: {exc}")


class SyncChat:
    def __init__(self, client: "ModelRouter"):
        self.completions = SyncCompletions(client)

    def complete(self, *args, **kwargs) -> ChatCompletion:
        """Convenience helper for client.chat.complete()"""
        return self.completions.create(*args, **kwargs)


class SyncModels:
    def __init__(self, client: "ModelRouter"):
        self._client = client

    def list(self) -> List[ModelInfo]:
        url = f"{self._client.base_url.rstrip('/')}/api/models"
        try:
            with httpx.Client(timeout=self._client.timeout) as http_client:
                res = http_client.get(url, headers=self._client._get_headers())
        except Exception as exc:
            raise APIConnectionError(f"Failed to fetch models from {self._client.base_url}: {exc}")

        if res.status_code != 200:
            _handle_error_response(res.status_code, res.text)

        items = res.json().get("models", res.json())
        return [ModelInfo(**m) for m in items]


class ModelRouter:
    """
    Synchronous Model Router Client for intelligent LLM routing.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        policy: str = "balanced",
        workspace_id: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or os.getenv("MODEL_ROUTER_API_KEY")
        self.base_url = base_url or os.getenv("MODEL_ROUTER_BASE_URL", "http://127.0.0.1:8000")
        self.policy = policy
        self.workspace_id = workspace_id or os.getenv("MODEL_ROUTER_WORKSPACE_ID")
        self.timeout = timeout

        self.chat = SyncChat(self)
        self.models = SyncModels(self)

    def _get_headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["X-API-Key"] = self.api_key
        if self.workspace_id:
            headers["X-Workspace-ID"] = self.workspace_id
        if extra:
            headers.update(extra)
        return headers

    def route(self, prompt: str, policy: Optional[str] = None) -> RoutingDecision:
        """Dry-run prompt analysis and model selection without executing inference."""
        url = f"{self.base_url.rstrip('/')}/api/route"
        payload = {"prompt": prompt, "policy": policy or self.policy}
        try:
            with httpx.Client(timeout=self.timeout) as http_client:
                res = http_client.post(url, json=payload, headers=self._get_headers())
        except Exception as exc:
            raise APIConnectionError(f"Failed to route request to {self.base_url}: {exc}")

        if res.status_code != 200:
            _handle_error_response(res.status_code, res.text)

        return RoutingDecision(**res.json())

    def health(self) -> Dict[str, Any]:
        """Check connection health of the Model Router gateway."""
        url = f"{self.base_url.rstrip('/')}/api/health"
        try:
            with httpx.Client(timeout=self.timeout) as http_client:
                res = http_client.get(url, headers=self._get_headers())
            return res.json()
        except Exception as exc:
            raise APIConnectionError(f"Health check failed for {self.base_url}: {exc}")


# ---------------------------------------------------------------------------
# Async Client
# ---------------------------------------------------------------------------

class AsyncCompletions:
    def __init__(self, client: "AsyncModelRouter"):
        self._client = client

    async def create(
        self,
        messages: Optional[List[Union[ChatMessage, Dict[str, str]]]] = None,
        prompt: Optional[str] = None,
        policy: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        headers: Optional[Dict[str, str]] = None,
    ) -> Union[ChatCompletion, AsyncGenerator[ChatCompletionChunk, None]]:
        if prompt is None:
            if not messages:
                raise ValueError("Either 'prompt' or 'messages' must be provided.")
            user_msgs = [m["content"] if isinstance(m, dict) else m.content for m in messages if (m["role"] if isinstance(m, dict) else m.role) == "user"]
            prompt = user_msgs[-1] if user_msgs else "\n".join(m["content"] if isinstance(m, dict) else m.content for m in messages)

        eff_policy = policy or self._client.policy
        req_payload = {
            "prompt": prompt,
            "policy": eff_policy,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        if stream:
            return self._stream_create(req_payload, headers=headers)

        url = f"{self._client.base_url.rstrip('/')}/api/route/run"
        req_headers = self._client._get_headers(headers)

        try:
            async with httpx.AsyncClient(timeout=self._client.timeout) as http_client:
                res = await http_client.post(url, json=req_payload, headers=req_headers)
        except httpx.ConnectError as exc:
            raise APIConnectionError(f"Failed to connect to Model Router at {self._client.base_url}: {exc}")
        except httpx.TimeoutException as exc:
            raise APIConnectionError(f"Request timed out after {self._client.timeout}s: {exc}")

        if res.status_code != 200:
            _handle_error_response(res.status_code, res.text)

        data = res.json()
        decision = data.get("decision", {})
        resp = data.get("response", {})
        selected_m = decision.get("selected_model", resp.get("model", "unknown"))

        return ChatCompletion(
            id=decision.get("decision_id", f"cmpl-{int(time.time()*1000)}"),
            created=int(time.time()),
            model=selected_m,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=resp.get("content", "")),
                    finish_reason="stop",
                )
            ],
            usage=Usage(
                prompt_tokens=resp.get("input_tokens", 0),
                completion_tokens=resp.get("output_tokens", 0),
                total_tokens=resp.get("total_tokens", 0),
                estimated_cost_usd=decision.get("estimated_cost_usd"),
            ),
            routing_metadata=decision,
        )

    async def _stream_create(self, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> AsyncGenerator[ChatCompletionChunk, None]:
        url = f"{self._client.base_url.rstrip('/')}/api/route/stream"
        req_headers = self._client._get_headers(headers)
        req_headers["Accept"] = "text/event-stream"

        try:
            async with httpx.AsyncClient(timeout=self._client.timeout) as http_client:
                async with http_client.stream("POST", url, json=payload, headers=req_headers) as response:
                    if response.status_code != 200:
                        body = await response.aread()
                        _handle_error_response(response.status_code, body.decode())

                    chunk_id = f"chatcmpl-chunk-{int(time.time()*1000)}"
                    async for line in response.aiter_lines():
                        if not line or line.startswith(":"):
                            continue
                        if line.startswith("data: "):
                            raw_data = line[6:].strip()
                            if raw_data == "[DONE]":
                                break
                            try:
                                parsed = json.loads(raw_data)
                                text_delta = parsed.get("token") or parsed.get("content") or parsed.get("text", "")
                                sel_model = parsed.get("model", "routed-model")
                                yield ChatCompletionChunk(
                                    id=chunk_id,
                                    created=int(time.time()),
                                    model=sel_model,
                                    choices=[
                                        ChatCompletionChunkChoice(
                                            index=0,
                                            delta=ChatCompletionChunkDelta(content=text_delta),
                                        )
                                    ],
                                    routing_metadata=parsed.get("routing_decision"),
                                )
                            except json.JSONDecodeError:
                                yield ChatCompletionChunk(
                                    id=chunk_id,
                                    created=int(time.time()),
                                    model="routed-model",
                                    choices=[
                                        ChatCompletionChunkChoice(
                                            index=0,
                                            delta=ChatCompletionChunkDelta(content=raw_data),
                                        )
                                    ],
                                )
        except httpx.ConnectError as exc:
            raise APIConnectionError(f"Failed to connect to Model Router stream: {exc}")


class AsyncChat:
    def __init__(self, client: "AsyncModelRouter"):
        self.completions = AsyncCompletions(client)

    async def complete(self, *args, **kwargs) -> ChatCompletion:
        """Convenience async helper for client.chat.complete()"""
        return await self.completions.create(*args, **kwargs)


class AsyncModels:
    def __init__(self, client: "AsyncModelRouter"):
        self._client = client

    async def list(self) -> List[ModelInfo]:
        url = f"{self._client.base_url.rstrip('/')}/api/models"
        try:
            async with httpx.AsyncClient(timeout=self._client.timeout) as http_client:
                res = await http_client.get(url, headers=self._client._get_headers())
        except Exception as exc:
            raise APIConnectionError(f"Failed to fetch models from {self._client.base_url}: {exc}")

        if res.status_code != 200:
            _handle_error_response(res.status_code, res.text)

        items = res.json().get("models", res.json())
        return [ModelInfo(**m) for m in items]


class AsyncModelRouter:
    """
    Asynchronous Model Router Client for non-blocking high-throughput intelligent LLM routing.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        policy: str = "balanced",
        workspace_id: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or os.getenv("MODEL_ROUTER_API_KEY")
        self.base_url = base_url or os.getenv("MODEL_ROUTER_BASE_URL", "http://127.0.0.1:8000")
        self.policy = policy
        self.workspace_id = workspace_id or os.getenv("MODEL_ROUTER_WORKSPACE_ID")
        self.timeout = timeout

        self.chat = AsyncChat(self)
        self.models = AsyncModels(self)

    async def close(self) -> None:
        """Close client resources (HTTP clients currently close per request)."""

    async def __aenter__(self) -> "AsyncModelRouter":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    def _get_headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["X-API-Key"] = self.api_key
        if self.workspace_id:
            headers["X-Workspace-ID"] = self.workspace_id
        if extra:
            headers.update(extra)
        return headers

    async def route(self, prompt: str, policy: Optional[str] = None) -> RoutingDecision:
        """Dry-run prompt analysis and model selection without executing inference."""
        url = f"{self.base_url.rstrip('/')}/api/route"
        payload = {"prompt": prompt, "policy": policy or self.policy}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as http_client:
                res = await http_client.post(url, json=payload, headers=self._get_headers())
        except Exception as exc:
            raise APIConnectionError(f"Failed to route request to {self.base_url}: {exc}")

        if res.status_code != 200:
            _handle_error_response(res.status_code, res.text)

        return RoutingDecision(**res.json())

    async def health(self) -> Dict[str, Any]:
        """Check connection health of the Model Router gateway."""
        url = f"{self.base_url.rstrip('/')}/api/health"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as http_client:
                res = await http_client.get(url, headers=self._get_headers())
            return res.json()
        except Exception as exc:
            raise APIConnectionError(f"Health check failed for {self.base_url}: {exc}")
