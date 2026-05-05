# DataVint Architecture Documentation

## 📁 Repository Structure

```
datavint/
├── client/                          # Vue 3 Frontend
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── main.js                  # Vue app entry
│   │   ├── App.vue                  # Root component
│   │   ├── router/
│   │   │   └── index.js             # Vue Router config
│   │   ├── views/                   # Page components
│   │   │   ├── PlaygroundView.vue   # /playground
│   │   │   ├── DataView.vue         # /data
│   │   │   └── VisualizationView.vue # /visualization
│   │   ├── components/              # Reusable components
│   │   │   ├── CodeEditor.vue
│   │   │   ├── ChatPanel.vue
│   │   │   ├── Terminal.vue
│   │   │   └── DataTable.vue
│   │   ├── services/
│   │   │   └── api.js               # Axios API client
│   │   ├── assets/
│   │   │   └── styles.css
│   │   └── utils/
│   ├── package.json
│   └── vite.config.js
│
├── server/                          # FastAPI Backend
│   ├── core/                        # DataVint SDK (renamed from datavint/)
│   │   ├── __init__.py
│   │   ├── profiling.py
│   │   ├── statistics.py
│   │   ├── issues.py
│   │   ├── manifest.py
│   │   ├── config.py
│   │   ├── types.py
│   │   └── detectors/
│   │       └── ...
│   ├── api/                         # FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI entry point
│   │   ├── routes/
│   │   │   ├── playground.py        # POST /api/playground/execute
│   │   │   ├── data.py              # /api/data/*
│   │   │   └── visualization.py     # /api/visualization/*
│   │   ├── models/
│   │   │   ├── request.py           # Pydantic request models
│   │   │   └── response.py          # Pydantic response models
│   │   ├── services/
│   │   │   └── analysis.py          # DatasetCache (in-memory storage)
│   │   └── middleware/
│   └── requirements.txt
│
├── tests/                           # Existing tests
├── examples/                        # Existing examples
├── notebooks/                       # Existing notebooks
├── playground/                      # Test data
├── demo.html                        # OLD standalone demo (deprecated)
├── README.md
└── ARCHITECTURE.md                  # This file
```

---

## 🌐 API Endpoints

### Base URL: `http://localhost:8080/api`

| Method | Endpoint | Description |
|--------|----------|-------------|
| **Playground Tab** |
| POST | `/api/playground/execute` | Execute DataVint code |
| POST | `/api/playground/validate` | Validate code syntax |
| **Raw Data Tab** |
| POST | `/api/data/upload` | Upload CSV dataset |
| GET | `/api/data/preview?dataset_id=X&limit=50` | Get dataset preview |
| GET | `/api/data/statistics?dataset_id=X` | Get dataset statistics |
| **Visualization Tab** |
| GET | `/api/visualization/issues?dataset_id=X` | Get detected issues |
| POST | `/api/visualization/manifest?dataset_id=X` | Generate manifest |

---

## 🔄 URL Routing (Client-Side)

| Route | Tab | API Endpoints Used |
|-------|-----|-------------------|
| `/` | Redirects to `/playground` | - |
| `/playground` | Playground (IDE) | `POST /api/playground/execute` |
| `/data` | Raw Data | `GET /api/data/preview`<br>`GET /api/data/statistics`<br>`POST /api/data/upload` |
| `/visualization` | Visualization Board | `GET /api/visualization/issues`<br>`POST /api/visualization/manifest` |

---

## 🚀 Running the Stack

### Backend (FastAPI)

```bash
# Install dependencies
cd server
pip install -r requirements.txt

# Run server
python -m api.main
# OR
uvicorn api.main:app --reload --port 8080
```

**Server runs on:** `http://localhost:8080`
**API docs:** `http://localhost:8080/api/docs`

### Frontend (Vue 3 + Vite)

```bash
# Install dependencies
cd client
npm install

# Run dev server
npm run dev
```

**Client runs on:** `http://localhost:5173`
**Proxy:** All `/api/*` requests proxied to `http://localhost:8080`

---

## 📊 Data Flow

```
┌─────────────── FRONTEND (localhost:5173) ───────────────┐
│                                                          │
│  User Action (Click "Run Code")                         │
│           ↓                                              │
│  Vue Component (PlaygroundView.vue)                     │
│           ↓                                              │
│  API Client (services/api.js)                           │
│           ↓                                              │
│  axios.post('/api/playground/execute', { code })        │
│                                                          │
└──────────────────────┬───────────────────────────────────┘
                       │ HTTP (proxied by Vite)
                       │
┌──────────────────────▼─── BACKEND (localhost:8080) ─────┐
│                                                          │
│  FastAPI Router (routes/playground.py)                  │
│           ↓                                              │
│  Execute code with server.core SDK                      │
│           ↓                                              │
│  Return { success, output, statistics, issues }         │
│                                                          │
└──────────────────────┬───────────────────────────────────┘
                       │ JSON Response
                       │
┌──────────────────────▼─────────────────────────────────┐
│                                                          │
│  Vue Component receives data                            │
│           ↓                                              │
│  Update Terminal with output                            │
│  Update Raw Data tab with statistics                    │
│  Update Visualization with issues                       │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 🎨 Frontend Tech Stack

- **Framework:** Vue 3 (Composition API)
- **Build Tool:** Vite
- **Router:** Vue Router 4
- **HTTP Client:** Axios
- **Code Editor:** Monaco Editor (@monaco-editor/loader)
- **Charts:** Chart.js
- **Styling:** CSS (Atom One Dark theme)

---

## 🔧 Backend Tech Stack

- **Framework:** FastAPI
- **Server:** Uvicorn (ASGI)
- **Validation:** Pydantic
- **Core SDK:** server.core (DataVint SDK)
- **Storage:** In-memory cache (DatasetCache) - no database yet

---

## 🔐 Security & CORS

CORS is enabled for local development:
- `http://localhost:5173` (Vite dev server)
- `http://localhost:8000` (Old demo server)

**Production:** Update `allow_origins` in `server/api/main.py`

---

## 🗂️ State Management

### Frontend
- **No global state manager** (Pinia/Vuex not needed yet)
- Component-level state with Vue 3 `ref()` and `reactive()`
- API responses cached in component state

### Backend
- **DatasetCache:** In-memory dictionary
- **TTL:** 1 hour (auto-cleanup)
- **Shared across routes** via singleton pattern

---

## 📦 Migration from demo.html

| Old (demo.html) | New (Vue) | Location |
|-----------------|-----------|----------|
| Inline HTML/CSS/JS | Separate components | `client/src/` |
| Vanilla JS tabs | Vue Router | `client/src/router/` |
| Simulated API | Real FastAPI | `server/api/routes/` |
| Syntax highlighting (custom) | Monaco Editor | `@monaco-editor/loader` |
| Static data | Dynamic API calls | `services/api.js` |

---

## 🧪 Testing

### Backend
```bash
cd server
pytest tests/
```

### Frontend
```bash
cd client
npm run test  # (TODO: Add Vitest)
```

---

## 🚧 TODO / Future Enhancements

- [ ] Add Pinia for global state (if needed)
- [ ] Add Vitest for frontend testing
- [ ] Add authentication (JWT)
- [ ] Add PostgreSQL database (replace DatasetCache)
- [ ] Add WebSocket for real-time terminal output
- [ ] Add file persistence (S3/local storage)
- [ ] Add Docker Compose for one-command setup
- [ ] Add CI/CD pipeline

---

## 📝 Development Workflow

1. **Start backend:** `cd server && python -m api.main`
2. **Start frontend:** `cd client && npm run dev`
3. **Open browser:** `http://localhost:5173`
4. **API docs:** `http://localhost:8080/api/docs`

---

## 📖 Import Changes

**OLD (confusing):**
```python
import datavint as dv  # Which datavint?
```

**NEW (clear):**
```python
from server.core import generate_statistics, detect_issues
# OR in FastAPI routes:
from server.core import *
```

---

**Last Updated:** 2024-05-05
**Version:** 0.2.0
