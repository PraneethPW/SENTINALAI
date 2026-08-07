# Architecture

The FastAPI API owns identity, devices, events, alerts, contacts, and AI requests. The React app communicates through a versioned REST API and a WebSocket feed. AI calls are isolated behind `AIService`. By default it uses OpenRouter's `openrouter/free` router with a free API key; if a free provider is unavailable or no key is configured, it returns deterministic, transparent local guidance rather than failing the request.
