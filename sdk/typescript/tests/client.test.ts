import test from 'node:test';
import assert from 'node:assert';
import { ModelRouter } from '../src/index.js';
import { AuthenticationError, RateLimitError } from '../src/errors.js';

test('ModelRouter initializes with default values', () => {
  const router = new ModelRouter({ baseUrl: 'http://localhost:8000' });
  assert.strictEqual(router.baseUrl, 'http://localhost:8000');
  assert.strictEqual(router.policy, 'balanced');
});

test('ModelRouter handles headers properly', () => {
  const router = new ModelRouter({
    apiKey: 'test-key',
    workspaceId: 'ws-123',
  });
  const headers = router.getHeaders({ 'Custom-Header': 'val' });
  assert.strictEqual(headers['Authorization'], 'Bearer test-key');
  assert.strictEqual(headers['X-API-Key'], 'test-key');
  assert.strictEqual(headers['X-Workspace-ID'], 'ws-123');
  assert.strictEqual(headers['Custom-Header'], 'val');
});

test('ModelRouter route dry-run formats request correctly', async () => {
  const mockFetch: typeof fetch = async (url, init) => {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        decision_id: 'dec-1',
        request_id: 'req-1',
        selected_model: 'mock-fast',
        selected_model_name: 'Mock Fast',
        provider: 'mock',
        tier: 'FAST',
        confidence: 0.9,
        policy_used: 'balanced',
        reasons: ['Fast speed score'],
        estimated_cost_usd: 0.0,
        estimated_latency_ms: 50,
      }),
    } as Response;
  };

  const router = new ModelRouter({ fetch: mockFetch });
  const decision = await router.route({ prompt: 'Test prompt' });
  assert.strictEqual(decision.selected_model, 'mock-fast');
  assert.strictEqual(decision.confidence, 0.9);
});
