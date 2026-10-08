# Model Router TypeScript & JavaScript SDK (`@picadolabs/modelrouter-sdk`)

Lightweight, zero-dependency TypeScript/JavaScript client for the **AI Model Router** platform. Works seamlessly in Node.js 18+, Bun, Deno, and modern browser environments.

## Installation

```bash
npm install @picadolabs/modelrouter-sdk
```

## Quickstart

### Standard Chat Completion (OpenAI Drop-In)

```typescript
import { ModelRouter } from '@picadolabs/modelrouter-sdk';

const router = new ModelRouter({
  apiKey: 'mr_live_...',
  baseUrl: 'http://localhost:8000',
  policy: 'balanced', // 'balanced' | 'cost_optimized' | 'speed_optimized' | 'quality_first'
});

// Create completion
const response = await router.chat.completions.create({
  messages: [
    { role: 'user', content: 'Explain Dijkstra\'s shortest path algorithm in simple terms.' }
  ]
});

console.log('Selected Model:', response.model);
console.log('Response:', response.choices[0].message.content);
console.log('Estimated Cost ($):', response.usage.estimated_cost_usd);
```

### Real-Time Streaming Responses

```typescript
const stream = await router.chat.completions.create({
  prompt: 'Write a Python function to parse JSON files safely.',
  stream: true,
});

for await (const chunk of stream) {
  const text = chunk.choices[0]?.delta?.content;
  if (text) {
    process.stdout.write(text);
  }
}
```

### Dry-Run Route Inspector

```typescript
const decision = await router.route({
  prompt: 'Design a microservice architecture in Go'
});

console.log(`Routed to ${decision.selected_model_name} with ${decision.confidence * 100}% confidence.`);
console.log('Reasons:', decision.reasons);
```
