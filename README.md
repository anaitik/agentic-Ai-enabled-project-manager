# Agentic AI Enabled Project Manager

A Python skeleton for a LangGraph-based agentic project manager system.

## Setup

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create your local environment file:

   ```bash
   copy .env.example .env
   ```

4. Fill in the required values in `.env`:

   - `DEEPSEEK_API_KEY`
   - `GITHUB_TOKEN`
   - `JIRA_API_TOKEN`
   - `JIRA_BASE_URL`

   `DEEPSEEK_BASE_URL` is included in `.env.example` and defaults to `https://api.deepseek.com` if omitted.

## Project Layout

- `pm_agent/state.py` defines the shared `PMAgentState` schema.
- `pm_agent/nodes/` contains placeholder graph nodes for scoping, provisioning, story generation, and tracking.
- `pm_agent/graph.py` assembles a LangGraph `StateGraph` that runs each placeholder node in sequence.
- `pm_agent/config.py` loads required environment variables at startup and raises a clear error when any are missing.

## Running Tests

```bash
pytest
```

## Notes

This skeleton uses `langchain-openai` because DeepSeek exposes an OpenAI-compatible API. Future LLM code can pass `DEEPSEEK_API_KEY` as the API key and `DEEPSEEK_BASE_URL` as the OpenAI-compatible base URL.

The `jira` package is included as the default Python Jira client. If you choose an MCP-based Jira integration later, replace the direct Jira client usage in future provisioning/tracking code with the relevant MCP client calls.
