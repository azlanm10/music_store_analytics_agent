# Music Store Analytics Agent

A conversational Slack bot that answers natural-language questions about the **Chinook** music store database. Users ask in Slack and receive answers as text or tables; charts are supported when explicitly requested.

## Features

- **Natural-language queries** about artists, albums, tracks, revenue, playlists, invoices, and related data
- **Conversation memory** for follow-up questions (e.g. "top 3", "same for albums")
- **Context-aware resolution** so short follow-ups are expanded using the last exchange
- **Validation & guardrails**: music-store domain check, PII detection, read-only / prompt-injection safety
- **Structured output**: markdown tables for data; charts when the user asks for a "chart", "graph", or "plot"
- **Help & greetings** handled with fixed responses

## Project Structure

```
slackbot/
├── slackbot_agent/           # Main package
│   ├── main.py               # Entry point: Slack Bolt app, message handler, flow
│   ├── intake/               # Request handling
│   │   ├── context_resolver.py  # LLM-based follow-up query expansion
│   │   ├── guardrails.py        # PII and blocked-pattern checks
│   │   ├── help.py              # Greeting and help detection + responses
│   │   ├── help_response.txt    # Help text content
│   │   └── validator.py         # Music-store domain validation
│   ├── memory/               # Conversation context
│   │   └── store.py             # Per-channel turn storage (append, get_context)
│   ├── engine/               # Query execution
│   │   ├── engine.py             # Public API: get_agent, run_query
│   │   ├── orchestrator.py      # Coordinates planner and reasoner
│   │   ├── planner.py           # First turn vs follow-up (chat vs follow_up)
│   │   └── reasoner.py           # PandasAI Agent, LLM config, chat/follow_up
│   ├── semantic_layer/        # Dataset definitions for PandasAI
│   │   └── semantic_layer.py    # load_sources, schema YAML loading, pai.create/pai.load
│   └── output/               # Response formatting and sending
│       └── response_builder.py  # build_slack_message, send_to_slack, chart path→base64, table formatting
├── datasets/
│   └── chinook/              # Semantic layer YAMLs (one folder per table/view)
│       ├── album/
│       ├── artist/
│       ├── customer/
│       ├── employee/
│       ├── genre/
│       ├── invoice/
│       ├── invoice-line/
│       ├── media-type/
│       ├── music-analytics/   # View (artist + album relation)
│       ├── playlist/
│       ├── playlist-track/
│       ├── track/
│       └── ... (each with schema.yaml)
├── tests/                    # Pytest tests
├── pyproject.toml
├── poetry.lock
├── .env.example
├── PROJECT_CONTEXT.md        # Architecture and design
└── README.md                 # This file
```

## Requirements

- Python 3.10 or 3.11
- Poetry
- PostgreSQL (Chinook schema)
- Slack app with Bot Token and App-Level Token (Socket Mode)
- OpenAI API key (for PandasAI/LiteLLM and context resolver)

## Setup

1. **Clone and install**

   ```bash
   cd slackbot
   poetry install
   ```

2. **Environment**

   Copy `.env.example` to `.env` and set:

   - `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN` (and `SLACK_SIGNING_SECRET` if not using Socket Mode only)
   - `LOG_FILE` (e.g. `logs/slackbot.log`)
   - `DB_USER`, `DB_PASS`, `DB_HOST`, `DB_PORT`, `DB_NAME` for Chinook Postgres
   - `OPENAI_API_KEY`

3. **Logs directory**

   Ensure the directory for `LOG_FILE` exists (e.g. `logs/`).

4. **Charts (optional)**

   The app creates `slackbot_agent/exports/charts` at startup so PandasAI can save chart images when the user asks for a chart. The response builder reads from that directory and uploads images to Slack.

## Run

```bash
poetry run python -m slackbot_agent.main
```

Or from project root:

```bash
poetry run python slackbot_agent/main.py
```

## Run tests

```bash
poetry run pytest tests/ -v
```

## Flow (high level)

1. **Slack** → message event → **main.py** (extract text, channel).
2. **Intake**: greeting/help → fixed reply; else load **memory** context, resolve **effective query** (context_resolver if follow-up), **validate** (validator), **guardrails** (PII, blocked).
3. **Engine**: **planner** chooses `chat` or `follow_up`; **reasoner** runs PandasAI Agent with **semantic layer** sources; SQL runs against Chinook.
4. **Output**: **response_builder** normalizes chart paths (read from `exports/charts`, base64), uploads images or formats text/tables, then **sends to Slack**. **Memory** appends the turn.

See **PROJECT_CONTEXT.md** for architecture details and diagrams.
