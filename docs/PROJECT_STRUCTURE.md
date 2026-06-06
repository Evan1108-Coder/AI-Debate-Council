# Project Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app, REST endpoints, WebSocket handler
│   │   ├── debate.py            # DebateManager: turn selection, streaming, prompts
│   │   ├── database.py          # SQLite schema, session/debate/message CRUD
│   │   ├── model_registry.py    # MODEL_MAP, provider detection, SupportedModel
│   │   ├── schemas.py           # Pydantic request/response models
│   │   ├── config.py            # Settings from environment variables
│   │   ├── analytics.py         # 10-method debate analysis engine + session chart data
│   │   ├── costing.py           # API cost estimation and currency conversion
│   │   └── runtime_diary.py     # Event logging with automatic secret scrubbing
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_analytics.py
│   │   ├── test_costing.py
│   │   ├── test_debate_architecture.py
│   │   ├── test_model_registry.py
│   │   ├── test_session_naming.py
│   │   └── test_session_settings.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── DebateRoom.tsx       # Main debate UI: chat, stats, settings panels
│   │   ├── GlobalWorkspace.tsx  # Welcome screen, global AI memory, user training profile
│   │   └── Sidebar.tsx          # Session list sidebar
│   ├── lib/
│   │   └── api.ts               # REST and WebSocket client functions
│   ├── types/
│   │   └── index.ts             # TypeScript type definitions
│   ├── package.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── postcss.config.mjs
│   └── tsconfig.json
├── electron/
│   ├── main.js                  # Electron main process: background servers, splash screen
│   ├── package.json             # Electron + electron-builder configuration
│   └── icons/
│       ├── icon.png             # 1024x1024 PNG source icon
│       ├── icon.icns            # macOS icon
│       └── icon.ico             # Windows icon
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
├── SETUP.md
├── ENVREADME.md
├── TROUBLESHOOTING.md
└── dev.py                       # One-command local launcher for backend + frontend
```
