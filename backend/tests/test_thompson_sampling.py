import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from app.router.thompson_sampling import ThompsonSamplingBandit, thompson_bandit
from app.storage.database import init_db, AsyncSessionLocal
from app.config.settings import get_settings

settings = get_settings()


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()
    thompson_bandit.reset_cache()


def test_thompson_sampling_prior_and_sampling():
    bandit = ThompsonSamplingBandit()

    # Prior for model with 0.9 quality
    prior = bandit._get_or_init_prior("CODING", "gpt-4o", 0.90)
    assert prior["alpha"] == 9.0
    assert prior["beta"] == 1.0

    # Sample quality with exploration rate 0.2
    sampled = bandit.sample_quality("CODING", "gpt-4o", 0.90, exploration_rate=0.20)
    assert 0.0 <= sampled <= 1.0

    # When exploration rate is 0.0, exact base quality returned
    exact = bandit.sample_quality("CODING", "gpt-4o", 0.90, exploration_rate=0.0)
    assert exact == 0.90


@pytest.mark.asyncio
async def test_thompson_sampling_feedback_learning():
    bandit = ThompsonSamplingBandit()
    task = "DEBUGGING"
    model = "mock-power"

    async with AsyncSessionLocal() as session:
        # Initial state
        prior = bandit._get_or_init_prior(task, model, 0.70)
        initial_alpha = prior["alpha"]

        # Record 5 positive ratings
        for _ in range(5):
            await bandit.record_feedback(task, model, rating=1, db=session)

        assert prior["alpha"] == initial_alpha + 5.0
        assert prior["pos"] == 5
        assert prior["total"] == 5

        # Record 2 negative ratings
        initial_beta = prior["beta"]
        for _ in range(2):
            await bandit.record_feedback(task, model, rating=-1, db=session)

        assert prior["beta"] == initial_beta + 2.0
        assert prior["neg"] == 2
        assert prior["total"] == 7

        # Check stats method
        stats = await bandit.get_stats(session, task_type=task)
        assert len(stats) >= 1
        stat_item = next(s for s in stats if s["model_id"] == model)
        assert stat_item["positive_feedback"] == 5
        assert stat_item["negative_feedback"] == 2
        assert stat_item["total_samples"] == 7
        assert 0.0 <= stat_item["posterior_mean"] <= 1.0


@pytest.mark.asyncio
async def test_api_feedback_rl_stats_endpoint_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Generate a request to obtain a real request_id
        gen_res = await client.post(
            "/api/generate",
            json={"prompt": "Optimize this binary search tree in C++", "policy": "balanced"},
        )
        assert gen_res.status_code == 200
        req_id = gen_res.json()["request_id"]

        # 2. Submit positive feedback (+1)
        fb_res = await client.post(
            "/api/feedback",
            json={"request_id": req_id, "rating": 1, "comment": "Excellent answer"},
        )
        assert fb_res.status_code == 200
        assert fb_res.json()["status"] == "success"

        # 3. Query /api/rl/stats
        rl_res = await client.get("/api/rl/stats")
        assert rl_res.status_code == 200
        stats = rl_res.json()
        assert len(stats) >= 1
        assert any(s["positive_feedback"] >= 1 for s in stats)
