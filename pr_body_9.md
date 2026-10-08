## Summary
Closes #9.

This PR implements Bayesian Thompson Sampling (Beta-Bernoulli Multi-Armed Bandit) reinforcement learning to automatically tune model quality scores based on live user feedback ratings (+1 / -1) per task type.

## Changes

### 1. Thompson Sampling Engine (backend/app/router/thompson_sampling.py)
- Maintained Beta posterior reward distributions (\Beta(alpha, beta)\) per \(task_type, model_id)\.
- Initialized informative Bayesian priors scaled from model benchmark quality ratings.
- Implemented sub-millisecond dynamic quality sampling blended with base exploitation scores based on configurable exploration rate (\RL_EXPLORATION_RATE = 0.15\).

### 2. Candidate Model Scoring Integration (backend/app/router/scoring.py)
- Integrated Thompson Sampling dynamic sampled quality directly into candidate model ranking.
- High-performing models receiving consistent positive ratings automatically gain routing priority for specific task types.

### 3. Feedback Loop & Observability (backend/app/api/routes.py)
- Updated \POST /api/feedback\ to automatically update Bayesian posteriors upon rating submission.
- Added \GET /api/rl/stats\ endpoint to monitor empirical win rates, posterior means, sample counts, and learned distributions.

### 4. Database Schema & Migration (backend/app/storage/models.py)
- Added \ModelRewardPosteriorRecord\ table.
- Added Alembic migration \e274a67cfc61_add_model_reward_posteriors_table.py\.

### 5. Automated Tests (backend/tests/test_thompson_sampling.py)
- Added comprehensive unit and end-to-end integration tests for prior initialization, feedback adaptation, exploration blending, and API endpoints.
- All 46 tests passing.
