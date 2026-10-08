import random
import datetime
from typing import Dict, Tuple, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.storage.models import ModelRewardPosteriorRecord
from app.config.settings import get_settings

settings = get_settings()


class ThompsonSamplingBandit:
    """
    Bayesian Thompson Sampling (Beta-Bernoulli Multi-Armed Bandit)
    for dynamic, feedback-driven model quality optimization per task type.
    """

    def __init__(self):
        # In-memory cache for sub-millisecond route sampling
        # Key: (task_type, model_id) -> {"alpha": float, "beta": float, "pos": int, "neg": int, "total": int}
        self._cache: Dict[Tuple[str, str], Dict[str, float]] = {}

    def _get_or_init_prior(self, task_type: str, model_id: str, base_quality: float) -> Dict[str, float]:
        key = (task_type.upper(), model_id.lower())
        if key not in self._cache:
            # Scaled informative Bayesian prior based on model's initial benchmark quality
            alpha = max(1.0, base_quality * 10.0)
            beta_val = max(1.0, (1.0 - base_quality) * 10.0)
            self._cache[key] = {
                "alpha": alpha,
                "beta": beta_val,
                "pos": 0,
                "neg": 0,
                "total": 0,
            }
        return self._cache[key]

    def sample_quality(
        self,
        task_type: str,
        model_id: str,
        base_quality: float,
        exploration_rate: Optional[float] = None,
    ) -> float:
        """
        Samples a dynamic quality reward from Beta(alpha, beta) posterior distribution.
        Blends with base quality score according to the exploration rate.
        """
        if not settings.RL_ROUTING_ENABLED:
            return base_quality

        exp_rate = exploration_rate if exploration_rate is not None else settings.RL_EXPLORATION_RATE
        if exp_rate <= 0.0:
            return base_quality

        prior = self._get_or_init_prior(task_type, model_id, base_quality)
        alpha = prior["alpha"]
        beta_val = prior["beta"]

        # Sample from Beta distribution
        try:
            sampled_theta = random.betavariate(alpha, beta_val)
        except Exception:
            sampled_theta = base_quality

        # Blended dynamic score: exploitation baseline + exploration sample
        effective_quality = ((1.0 - exp_rate) * base_quality) + (exp_rate * sampled_theta)
        return min(1.0, max(0.05, effective_quality))

    async def record_feedback(
        self,
        task_type: str,
        model_id: str,
        rating: int,
        db: AsyncSession,
    ):
        """
        Updates Beta posterior parameters based on user rating (+1 or -1)
        and persists to database.
        """
        key = (task_type.upper(), model_id.lower())
        record_id = f"mrp_{task_type.upper()}_{model_id.lower()}"

        # 1. Update in-memory state
        prior = self._get_or_init_prior(task_type, model_id, 0.80)
        if rating > 0:
            prior["alpha"] += 1.0
            prior["pos"] += 1
        else:
            prior["beta"] += 1.0
            prior["neg"] += 1
        prior["total"] += 1

        # 2. Persist to DB
        res = await db.execute(select(ModelRewardPosteriorRecord).filter_by(id=record_id))
        rec = res.scalar_one_or_none()

        if rec:
            rec.alpha = prior["alpha"]
            rec.beta_param = prior["beta"]
            rec.positive_feedback = int(prior["pos"])
            rec.negative_feedback = int(prior["neg"])
            rec.total_samples = int(prior["total"])
            rec.updated_at = datetime.datetime.now(datetime.timezone.utc)
        else:
            rec = ModelRewardPosteriorRecord(
                id=record_id,
                task_type=task_type.upper(),
                model_id=model_id.lower(),
                alpha=prior["alpha"],
                beta_param=prior["beta"],
                positive_feedback=int(prior["pos"]),
                negative_feedback=int(prior["neg"]),
                total_samples=int(prior["total"]),
            )
            db.add(rec)

        await db.commit()

    async def get_stats(self, db: AsyncSession, task_type: Optional[str] = None) -> List[Dict]:
        """
        Fetches posterior reward distributions and empirical win rates.
        """
        query = select(ModelRewardPosteriorRecord)
        if task_type:
            query = query.filter_by(task_type=task_type.upper())
        res = await db.execute(query)
        records = res.scalars().all()

        stats = []
        for r in records:
            posterior_mean = r.alpha / (r.alpha + r.beta_param)
            win_rate = (r.positive_feedback / r.total_samples) if r.total_samples > 0 else posterior_mean
            stats.append({
                "id": r.id,
                "task_type": r.task_type,
                "model_id": r.model_id,
                "alpha": round(r.alpha, 2),
                "beta": round(r.beta_param, 2),
                "posterior_mean": round(posterior_mean, 4),
                "win_rate": round(win_rate, 4),
                "positive_feedback": r.positive_feedback,
                "negative_feedback": r.negative_feedback,
                "total_samples": r.total_samples,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            })
        return stats

    def reset_cache(self):
        """Clears in-memory cache (for testing)."""
        self._cache.clear()


thompson_bandit = ThompsonSamplingBandit()
