/**
 * Model Router TypeScript SDK Quickstart Example.
 */

import { ModelRouter } from '../sdk/typescript/src/index.js';

async function main() {
  const router = new ModelRouter({
    baseUrl: 'http://localhost:8000',
    policy: 'balanced',
  });

  console.log('--- 1. Route Dry Run ---');
  const decision = await router.route({
    prompt: 'Implement a quicksort algorithm in TypeScript',
  });
  console.log(`Routed to: ${decision.selected_model_name} (${decision.provider})`);
  console.log(`Reasons: ${decision.reasons.join(', ')}`);

  console.log('\n--- 2. Chat Completion ---');
  const response = await router.chat.completions.create({
    messages: [
      { role: 'user', content: 'What is the speed of light in vacuum in m/s?' },
    ],
  });
  console.log(`Response: ${response.choices[0].message.content}`);
  console.log(`Model: ${response.model}`);
}

main().catch(console.error);
