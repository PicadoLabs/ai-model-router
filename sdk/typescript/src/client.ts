import {
  ChatCompletion,
  ChatCompletionChunk,
  ChatCompletionCreateParams,
  ModelInfo,
  ModelRouterOptions,
  RoutingDecision,
} from './types.js';
import {
  APIConnectionError,
  APIStatusError,
  AuthenticationError,
  ModelRouterError,
  RateLimitError,
} from './errors.js';

function handleErrorResponse(status: number, text: string): never {
  let body: any = text;
  let detail = text;
  try {
    body = JSON.parse(text);
    detail = body.detail || text;
  } catch {}

  if (status === 401 || status === 403) {
    throw new AuthenticationError(`Authentication failed: ${detail}`, status, body);
  } else if (status === 429) {
    throw new RateLimitError(`Rate limit exceeded: ${detail}`, status, body);
  } else {
    throw new APIStatusError(`Model Router API error (${status}): ${detail}`, status, body);
  }
}

export class Completions {
  constructor(private client: ModelRouter) {}

  async create(
    params: ChatCompletionCreateParams & { stream: true }
  ): Promise<AsyncIterable<ChatCompletionChunk>>;
  async create(
    params: ChatCompletionCreateParams & { stream?: false }
  ): Promise<ChatCompletion>;
  async create(
    params: ChatCompletionCreateParams
  ): Promise<ChatCompletion | AsyncIterable<ChatCompletionChunk>>;
  async create(
    params: ChatCompletionCreateParams
  ): Promise<ChatCompletion | AsyncIterable<ChatCompletionChunk>> {
    let prompt = params.prompt;
    if (!prompt && params.messages && params.messages.length > 0) {
      const userMsgs = params.messages.filter((m) => m.role === 'user');
      prompt = userMsgs.length > 0 ? userMsgs[userMsgs.length - 1].content : params.messages.map((m) => m.content).join('\n');
    }

    if (!prompt) {
      throw new ModelRouterError("Either 'prompt' or 'messages' must be provided.");
    }

    const payload = {
      prompt,
      policy: params.policy || this.client.policy,
      temperature: params.temperature ?? 0.7,
      max_tokens: params.max_tokens,
      stream: Boolean(params.stream),
    };

    if (params.stream) {
      return this.streamCreate(payload, params.headers);
    }

    const url = `${this.client.baseUrl.replace(/\/$/, '')}/api/route/run`;
    const headers = this.client.getHeaders(params.headers);

    let res: Response;
    try {
      res = await this.client.fetchFn(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      });
    } catch (err: any) {
      throw new APIConnectionError(`Failed to connect to Model Router: ${err.message}`);
    }

    if (!res.ok) {
      const text = await res.text();
      handleErrorResponse(res.status, text);
    }

    const data = await res.json();
    const decision = data.decision || {};
    const resp = data.response || {};
    const selectedModel = decision.selected_model || resp.model || 'unknown';

    return {
      id: decision.decision_id || `cmpl-${Date.now()}`,
      object: 'chat.completion',
      created: Math.floor(Date.now() / 1000),
      model: selectedModel,
      choices: [
        {
          index: 0,
          message: {
            role: 'assistant',
            content: resp.content || '',
          },
          finish_reason: 'stop',
        },
      ],
      usage: {
        prompt_tokens: resp.input_tokens || 0,
        completion_tokens: resp.output_tokens || 0,
        total_tokens: resp.total_tokens || 0,
        estimated_cost_usd: decision.estimated_cost_usd,
      },
      routing_metadata: decision,
    };
  }

  private async *streamCreate(
    payload: any,
    extraHeaders?: Record<string, string>
  ): AsyncIterable<ChatCompletionChunk> {
    const url = `${this.client.baseUrl.replace(/\/$/, '')}/api/route/stream`;
    const headers = this.client.getHeaders({
      ...extraHeaders,
      Accept: 'text/event-stream',
    });

    let res: Response;
    try {
      res = await this.client.fetchFn(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      });
    } catch (err: any) {
      throw new APIConnectionError(`Failed to connect to Model Router stream: ${err.message}`);
    }

    if (!res.ok) {
      const text = await res.text();
      handleErrorResponse(res.status, text);
    }

    if (!res.body) {
      throw new ModelRouterError('Response body is empty or streaming unsupported');
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith(':')) continue;
        if (trimmed.startsWith('data: ')) {
          const raw = trimmed.slice(6).trim();
          if (raw === '[DONE]') return;
          try {
            const parsed = JSON.parse(raw);
            const token = parsed.token || parsed.content || parsed.text || '';
            const model = parsed.model || 'routed-model';
            yield {
              id: `chatcmpl-chunk-${Date.now()}`,
              object: 'chat.completion.chunk',
              created: Math.floor(Date.now() / 1000),
              model,
              choices: [
                {
                  index: 0,
                  delta: { content: token },
                  finish_reason: null,
                },
              ],
              routing_metadata: parsed.routing_decision,
            };
          } catch {
            yield {
              id: `chatcmpl-chunk-${Date.now()}`,
              object: 'chat.completion.chunk',
              created: Math.floor(Date.now() / 1000),
              model: 'routed-model',
              choices: [
                {
                  index: 0,
                  delta: { content: raw },
                  finish_reason: null,
                },
              ],
            };
          }
        }
      }
    }
  }
}

export class Chat {
  public completions: Completions;

  constructor(client: ModelRouter) {
    this.completions = new Completions(client);
  }

  async complete(params: ChatCompletionCreateParams): Promise<ChatCompletion> {
    return (await this.completions.create(params as any)) as ChatCompletion;
  }
}

export class Models {
  constructor(private client: ModelRouter) {}

  async list(): Promise<ModelInfo[]> {
    const url = `${this.client.baseUrl.replace(/\/$/, '')}/api/models`;
    const res = await this.client.fetchFn(url, {
      method: 'GET',
      headers: this.client.getHeaders(),
    });

    if (!res.ok) {
      const text = await res.text();
      handleErrorResponse(res.status, text);
    }

    const data = await res.json();
    return data.models || data;
  }
}

export class ModelRouter {
  public apiKey?: string;
  public baseUrl: string;
  public policy: string;
  public workspaceId?: string;
  public fetchFn: typeof fetch;

  public chat: Chat;
  public models: Models;

  constructor(options: ModelRouterOptions = {}) {
    this.apiKey = options.apiKey || (typeof process !== 'undefined' ? process.env?.MODEL_ROUTER_API_KEY : undefined);
    this.baseUrl = options.baseUrl || (typeof process !== 'undefined' ? process.env?.MODEL_ROUTER_BASE_URL : undefined) || 'http://127.0.0.1:8000';
    this.policy = options.policy || 'balanced';
    this.workspaceId = options.workspaceId || (typeof process !== 'undefined' ? process.env?.MODEL_ROUTER_WORKSPACE_ID : undefined);
    this.fetchFn = options.fetch || (typeof globalThis !== 'undefined' && globalThis.fetch ? globalThis.fetch.bind(globalThis) : fetch);

    this.chat = new Chat(this);
    this.models = new Models(this);
  }

  public getHeaders(extra?: Record<string, string>): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
      headers['X-API-Key'] = this.apiKey;
    }
    if (this.workspaceId) {
      headers['X-Workspace-ID'] = this.workspaceId;
    }
    if (extra) {
      Object.assign(headers, extra);
    }
    return headers;
  }

  async route(params: { prompt: string; policy?: string }): Promise<RoutingDecision> {
    const url = `${this.baseUrl.replace(/\/$/, '')}/api/route`;
    const res = await this.fetchFn(url, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        prompt: params.prompt,
        policy: params.policy || this.policy,
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      handleErrorResponse(res.status, text);
    }

    return await res.json();
  }

  async health(): Promise<{ status: string; [key: string]: any }> {
    const url = `${this.baseUrl.replace(/\/$/, '')}/api/health`;
    const res = await this.fetchFn(url, {
      method: 'GET',
      headers: this.getHeaders(),
    });

    if (!res.ok) {
      const text = await res.text();
      handleErrorResponse(res.status, text);
    }

    return await res.json();
  }
}
