# Architecture

The FastAPI API owns identity, devices, events, alerts, contacts, and AI requests. The React app communicates through a versioned REST API and a WebSocket feed. AI calls are isolated behind `AIService`; without an OpenRouter key it returns deterministic, transparent local guidance for development.
