# Provider adapter conventions

Provider adapters implement the same `ModelProvider` contract and return the
shared `ProviderResponse` type. Register a provider with a lower-case stable
identifier, keep credentials in settings, and never include keys in errors or
response metadata. Add a registry test for successful lookup and a missing-key
test for the provider's failure path before exposing it through the API.

OpenAI-compatible services should share request and response normalization
where their wire format is identical; provider-specific authentication and
base URLs remain in the adapter.
