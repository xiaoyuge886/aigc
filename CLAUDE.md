# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AIGC Intelligent Agent Platform - A full-stack AI application platform based on Claude AI, supporting custom skill ecosystems and scenario-based AI solutions. Uses FastAPI (Python) backend and React (TypeScript) frontend.

## Development Commands

### Backend (Python/FastAPI)

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY

# Run development server
python main.py
# Runs on http://localhost:8000
# API docs at http://localhost:8000/docs

# Run tests
pytest                           # All tests
pytest tests/test_api.py         # Single test file
pytest tests/test_api.py::test_health -v  # Single test function
pytest -v --tb=short             # Verbose with short traceback
```

### Frontend (React/TypeScript)

```bash
cd frontend/aigc-frontend

# Install dependencies
npm install

# Run development server
npm run dev
# Runs on http://localhost:5173 (or 8888 via start.sh)

# Build for production
npm run build
```

### Combined Startup

```bash
# Start both backend and frontend
./scripts/start.sh

# Stop all services
./scripts/stop.sh

# Or use Docker deployment
cd deploy
./deploy.sh dev      # Development
./deploy.sh prod     # Production
./deploy.sh stop     # Stop services
```

## Architecture Overview

### Backend Structure (`backend/`)

```
backend/
├── main.py                 # FastAPI app entry point
├── api/v1/                 # API routes
│   ├── endpoints.py        # Main agent/chat endpoints
│   ├── platform.py         # Scenario/platform config API
│   ├── auth.py             # Authentication endpoints
│   └── github_skills.py    # GitHub skills integration
├── services/               # Business logic layer
│   ├── agent_service.py    # Core Claude Agent SDK integration
│   ├── session_manager.py  # Multi-session management
│   ├── scenario_matcher.py # Scenario matching engine
│   └── database.py         # Database operations
├── models/                 # Data models
│   ├── database.py         # SQLAlchemy ORM models
│   ├── schemas.py          # Pydantic validation schemas
│   └── platform.py         # Platform/scenario models
├── tools/                  # Custom MCP tools
│   └── custom_tools.py     # Tool definitions
├── core/config.py          # Settings management
└── tests/                  # Test suite
```

### Frontend Structure (`frontend/aigc-frontend/`)

```
frontend/aigc-frontend/
├── components/             # React components
│   ├── ChatInterface.tsx   # Main chat UI with streaming
│   ├── SkillGalaxy.tsx     # Skill mind-map visualization
│   ├── SkillMarketNexus.tsx# Skill marketplace
│   ├── AdminDashboard.tsx  # Admin control panel
│   └── ScenarioEditor.tsx  # Scenario configuration
├── services/api.ts         # API client
└── App.tsx                 # Application entry
```

### Key Architecture Patterns

**Agent Service Modes** (`backend/services/agent_service.py`):
- `query_once()` - Stateless single query, no conversation context
- `query_in_session()` - Stateful multi-turn conversation with session management

**Scenario Matching** (`backend/services/scenario_matcher.py`):
- Automatically matches user intent to configured scenarios
- Each scenario has its own system prompt, tools, and model settings

**Session Management** (`backend/services/session_manager.py`):
- Maintains ClaudeSDKClient instances across HTTP requests
- Handles session timeout and cleanup

### Skills System (`.claude/skills/`)

Custom skills extend Claude's capabilities. Each skill is a directory containing:
- `skill.md` - Skill definition and instructions
- Supporting scripts or configurations

Built-in skills include: `data-analysis`, `echarts_chart`, `frontend-design`, `pptx`, `meta_agent`, `x_agent_skill`, `smart_query_analyzer`, `whodb`, `minio_uploader`, `docs-management`.

## Configuration

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Claude API key (required) |
| `DEFAULT_MODEL` | Default model (default: `sonnet`) |
| `MAX_TURNS` | Max conversation turns (default: `100`) |
| `JWT_SECRET_KEY` | JWT secret (change in production) |

### Working Directories

- `work_dir/` - Production environment file operations
- `debug_work_dir/` - Debug/test environment file operations

### Key Settings (`backend/core/config.py`)

- `permission_mode` - Tool permission mode (default: `acceptEdits`)
- `enable_security_control` - Runtime security protection (default: `true`)
- `allowed_tools` - Comma-separated list of permitted tools

## API Structure

Base path: `/api/v1/`

- `/agent/query` - Single query (no session)
- `/agent/query/stream` - Streaming query
- `/session/create` - Create new session
- `/session/query` - Query within session
- `/auth/login` - User authentication
- `/skills/` - Skill marketplace
- `/github-skills/` - GitHub skills integration
- `/platform/` - Scenario configuration

## Testing

Tests use pytest with async support. Key test files:
- `test_api.py` - API endpoint tests
- `test_agent_service.py` - Agent service tests
- `test_streaming_simple.py` - Streaming tests
- `test_tools.py` - Tool tests

Run tests from `backend/` directory after activating virtual environment.