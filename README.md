# 🧪 AutoAB — Automated A/B Testing Platform

**Fully automated A/B testing with AI-powered diff analysis and LLM-generated insights.**

AutoAB eliminates manual A/B testing overhead by automatically:
- 🔍 **Crawling & diffing** your two app versions using Playwright + LLM
- 📊 **Tracking user events** via lightweight JavaScript SDK
- 📈 **Running statistical tests** (Z-test, T-test, Mann-Whitney U, Bayesian)
- 🤖 **Generating insights** using Groq API (Llama 3.1 70B) or Ollama (local)
- 🎯 **Recommending decisions** based on comprehensive analysis

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **🤖 Automatic Diff Analysis** | LLM analyzes HTML/CSS differences between versions and generates hypotheses |
| **📊 Real-time Dashboard** | React dashboard with live conversion tracking and interactive charts |
| **🎯 Statistical Rigor** | Multiple tests (frequentist + Bayesian) with power analysis |
| **⚡ Zero Setup** | Single `docker compose up` starts entire stack |
| **🆓 100% Free LLMs** | Groq API (14,400 req/day) or Ollama (local Mistral 7B) |
| **📱 Smart SDK** | Auto-tracks clicks, scrolls, rage-clicks, conversions, and session metrics |
| **🔐 Privacy-First** | Self-hosted, no data leaves your infrastructure |
| **📈 Time-Series Snapshots** | Pre-aggregated metrics every 5 minutes for fast queries |
| **🚨 Guardrail Checks** | Detects bounce rate spikes and Simpson's Paradox |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER'S BROWSER                          │
│  ┌─────────────────┐              ┌─────────────────┐          │
│  │   Version A     │              │   Version B     │          │
│  │   (Control)     │              │  (Treatment)    │          │
│  │  localhost:3001 │              │  localhost:3002 │          │
│  └────────┬────────┘              └────────┬────────┘          │
│           │    ◀── AutoAB SDK ──▶          │                   │
└───────────┼──────────────────────────────────┼─────────────────┘
            │                                  │
            └──────────────┬───────────────────┘
                           │ POST /events/batch
                           ▼
        ┌──────────────────────────────────────────────┐
        │          FastAPI Backend (8000)              │
        │  ┌─────────────────────────────────────────┐ │
        │  │  /experiments/  — CRUD + lifecycle mgmt │ │
        │  │  /events/       — event ingestion       │ │
        │  │  /analysis/     — stats + time-series   │ │
        │  └─────────────────────────────────────────┘ │
        └──────┬───────────────────────────────┬───────┘
               │                               │
               ▼                               ▼
    ┌─────────────────────┐       ┌──────────────────────┐
    │  PostgreSQL +       │       │  Redis (Celery)      │
    │  TimescaleDB        │       │  ┌─────────────────┐ │
    │  (Time-series DB)   │       │  │ Worker: Metrics │ │
    │                     │       │  │ Beat: Scheduler │ │
    └─────────────────────┘       │  └─────────────────┘ │
                                  └──────────────────────┘
                                             │
                                             ▼
                                  ┌──────────────────────┐
                                  │  Groq API / Ollama   │
                                  │  (LLM Diff + Report) │
                                  └──────────────────────┘

        ┌──────────────────────────────────────────────┐
        │       React Dashboard (5173)                 │
        │  ┌─────────────────────────────────────────┐ │
        │  │  • Experiments list & creation          │ │
        │  │  • Real-time charts (Recharts)          │ │
        │  │  • Statistical results & recommendations│ │
        │  │  • LLM diff analysis & AI reports       │ │
        │  └─────────────────────────────────────────┘ │
        └──────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Docker** + **Docker Compose** (or Podman)
- **Node.js 18+** (for frontend and demo apps)
- **Python 3.11+** (for Locust simulator)
- **(Optional)** [Groq API key](https://console.groq.com) for cloud LLM (free tier)

### 1. Clone & Setup

```bash
cd "c:\Nandini Kushwah\My\AB Testing and Uplifting Model\autoab"

# Copy environment variables
cp .env.example .env

# (Optional) Add your Groq API key for cloud LLM
# nano .env  →  GROQ_API_KEY=gsk_...
```

### 2. Start Backend Services

```bash
docker compose up --build -d
```

This starts 5 containers:
- `db` — PostgreSQL + TimescaleDB (port 5432)
- `redis` — Redis for Celery (port 6379)
- `backend` — FastAPI server (port 8000)
- `worker` — Celery worker (metric snapshots)
- `beat` — Celery Beat (scheduled tasks)

Check health:
```bash
curl http://localhost:8000/health/
# Expected: {"status": "healthy"}
```

### 3. Start Demo Apps

```bash
cd demo-apps
python serve.py
```

This serves:
- **Version A (control)** → http://localhost:3001
- **Version B (treatment)** → http://localhost:3002

### 4. Start Frontend Dashboard

```bash
cd frontend
npm install
npm run dev
```

Dashboard available at **http://localhost:5173**

### 5. Create Your First Experiment

1. Open http://localhost:5173
2. Click **"New Experiment"**
3. Fill in:
   - Name: `Red vs Blue CTA Test`
   - URL A: `http://localhost:3001`
   - URL B: `http://localhost:3002`
   - Primary metric: `conversion_rate`
   - Duration: `14` days
4. Submit → LLM will analyze differences in background
5. Click **"Start Experiment"** when ready

### 6. Generate Traffic with Locust

```bash
cd simulator
pip install -r requirements.txt

# Replace <EXPERIMENT_ID> with UUID from dashboard
EXPERIMENT_ID=<uuid> locust -f locustfile.py --headless \
  -u 100 -r 10 --run-time 5m --host http://localhost:8000
```

This simulates:
- **100 concurrent users** (50 control, 50 treatment)
- **8% conversion rate** for control
- **12% conversion rate** for treatment (50% relative uplift)
- Realistic journeys: page_view → scroll → click → convert → session_end

### 7. View Results

Navigate to your experiment in the dashboard:
- **Overview tab** — Real-time conversion rates, time-series chart
- **Results tab** — Statistical tests, p-values, recommendation
- **LLM Diff Analysis tab** — AI-detected changes and hypotheses
- **AI Report tab** (after stopping) — Final LLM verdict

---

## 📁 Project Structure

```
autoab/
├── backend/                # FastAPI application
│   ├── main.py             # Entry point, CORS, routers
│   ├── database.py         # SQLAlchemy engines
│   ├── config.py           # Pydantic settings
│   ├── Dockerfile          # Container with Playwright
│   ├── requirements.txt
│   ├── models/             # DB models (Experiment, Event, MetricSnapshot)
│   ├── routers/            # API routes (experiments, events, analysis)
│   ├── services/           # Business logic (stats_engine, llm_diff, llm_report)
│   └── workers/            # Celery tasks (metric snapshots, auto-stop)
│
├── frontend/               # React dashboard
│   ├── src/
│   │   ├── api/            # API client wrapper
│   │   ├── components/     # Layout + UI components (shadcn-style)
│   │   ├── pages/          # ExperimentsList, CreateExperiment, ExperimentDetail
│   │   └── lib/            # Utilities (cn, formatters)
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
├── sdk/                    # JavaScript tracking SDK
│   └── autoab-sdk.js       # Auto-tracks page_view, click, scroll, conversion
│
├── demo-apps/              # Example A/B test apps
│   ├── version-a/          # Control (blue CTA)
│   │   └── index.html
│   ├── version-b/          # Treatment (red CTA + urgency)
│   │   └── index.html
│   └── serve.py            # Serves both on :3001 and :3002
│
├── simulator/              # Locust traffic generator
│   ├── locustfile.py       # Realistic user journey simulation
│   └── requirements.txt
│
├── docker-compose.yml      # Orchestrates all services
├── .env.example            # Environment template
└── README.md               # This file
```

---

## 🧠 How It Works

### 1. **Experiment Creation**
   - User provides URLs for Version A and Version B
   - Backend triggers `llm_diff.py`:
     - Crawls both pages with Playwright (headless Chromium)
     - Extracts visible text content
     - Computes unified diff (max 250 lines)
     - Sends to Groq API / Ollama with structured prompt
     - LLM returns JSON: `changes_detected`, `hypotheses`, `recommended_metrics`, `risk_factors`
   - Stores diff in `Experiment.llm_diff` (JSONB column)

### 2. **Event Tracking**
   - JavaScript SDK embedded in both apps
   - Auto-tracks:
     - `page_view` — on load
     - `click` — buttons, links
     - `scroll_depth` — max scroll percentage
     - `rage_click` — 3+ clicks in 1 second (frustration signal)
     - `form_submit` — form submissions
     - `conversion` — manual trigger via `window.autoab.convert(value)`
     - `session_end` — on page unload with duration + scroll
   - Batches events every 5 seconds → `POST /events/batch`
   - Events stored in `Event` table (PostgreSQL + TimescaleDB)

### 3. **Metric Aggregation**
   - **Celery Beat** schedules `compute_metric_snapshots` every 5 minutes
   - Worker queries `Event` table, computes per-group metrics:
     - `users_count` — unique `session_id`
     - `conversion_rate` — conversions / users
     - `avg_revenue` — SUM(value) / conversions
     - `ctr` — clicks / users
     - `avg_session_duration` — AVG(duration)
     - `bounce_rate` — single-page sessions / users
     - `avg_scroll_depth` — AVG(scroll_depth)
   - Stores in `MetricSnapshot` table (fast for time-series queries)

### 4. **Statistical Analysis**
   - Frontend requests `GET /analysis/{id}/results`
   - `stats_engine.py` runs 5 tests:
     1. **Z-test** (proportions) — conversion, CTR, bounce
     2. **Welch T-test** — revenue, session duration (unequal variance)
     3. **Mann-Whitney U** — non-parametric fallback
     4. **Bayesian Beta-Binomial** — `P(B wins | data)`
     5. **Power analysis** — current power, % progress to target
   - Recommendation logic:
     - `SHIP_B` — significant improvement, guardrails pass
     - `KEEP_A` — significant decline
     - `CONTINUE` — not significant, need more data
     - `INVESTIGATE` — guardrail violation (bounce rate spike)

### 5. **AI Report Generation**
   - User clicks "Generate AI Report" (or auto-triggers on experiment end)
   - `llm_report.py`:
     - Combines: experiment config, diff analysis, statistical results
     - Sends to Groq API / Ollama with structured prompt
     - LLM returns JSON:
       - `verdict` — SHIP_B / KEEP_A / CONTINUE / INVESTIGATE
       - `confidence` — 0.0 to 1.0
       - `headline` — One-sentence summary
       - `what_changed` — Plain English diff summary
       - `what_happened` — User behavior analysis
       - `risks_to_consider` — Edge cases, segments
       - `recommendation` — Action steps
       - `next_steps` — Follow-up tests
   - Stores in `Experiment.llm_report` (JSONB column)

### 6. **Auto-Stop**
   - **Celery Beat** schedules `check_experiment_completion` every 15 minutes
   - If `days_elapsed >= duration_days`:
     - Updates `status` → `ANALYSIS`
     - Frontend shows "Generate AI Report" button

---

## 🧪 Demo App Differences (Version A vs B)

| Aspect | Version A (Control) | Version B (Treatment) |
|--------|---------------------|------------------------|
| **Primary Color** | Blue (`#2563eb`) | Red (`#dc2626`) |
| **Headline** | "Store, Sync & Share Your Files Everywhere" | "Your Files Are One Crash Away From Gone" |
| **CTA Copy** | "Get Started for Free" | "🚀 Protect My Files Now" |
| **Urgency Banner** | ❌ None | ✅ Countdown timer "50% off for 10:00" |
| **Social Proof** | ❌ None | ✅ Logo strip (5 fake companies) |
| **Testimonials** | ❌ None | ✅ 3 customer reviews with star ratings |
| **Tone** | Informational, calm | Fear-based, urgent |

The LLM diff analyser automatically detects these changes and generates hypotheses like:
- "Red button may increase urgency perception"
- "Fear-based headline could improve conversion but risk brand damage"
- "Countdown timer creates FOMO"

---

## 📊 Statistical Tests Explained

### Z-Test (Proportions)
- **When:** Conversion rate, CTR, bounce rate
- **Null Hypothesis:** No difference between groups
- **Output:** p-value, z-statistic
- **Decision:** Reject H0 if `p < α` (typically 0.05)

### Welch T-Test
- **When:** Continuous metrics (revenue, session duration)
- **Advantage:** Doesn't assume equal variance
- **Output:** p-value, t-statistic, degrees of freedom

### Mann-Whitney U
- **When:** Non-parametric fallback (skewed distributions)
- **Advantage:** Robust to outliers
- **Output:** p-value, U-statistic

### Bayesian Beta-Binomial
- **When:** Conversion/binary outcome
- **Advantage:** Direct probability interpretation
- **Output:** `P(B > A | data)` — e.g., 94% chance treatment is better
- **Priors:** Uniform `Beta(1,1)` (uninformative)

### Power Analysis
- **Current Power** = `1 - β` = probability of detecting true effect
- **Progress** = `(current_n / required_n) * 100%`
- **Required Sample Size** = calculated from α, power, MDE using statsmodels

---

## 🔒 Security & Privacy

- ✅ **Self-hosted** — All data stays on your infrastructure
- ✅ **No external tracking** — SDK only sends to your backend
- ✅ **Anonymized sessions** — Session IDs are UUIDs, no PII required
- ✅ **Environment isolation** — Docker Compose network isolation
- ✅ **CORS configured** — Only allows your frontend origin (edit in `main.py`)

### Production Hardening

1. **Change database credentials** in `.env`
2. **Enable HTTPS** — Use reverse proxy (Nginx, Caddy)
3. **Rate limiting** — Add to FastAPI middleware
4. **API authentication** — Add JWT tokens if exposing publicly
5. **DB backups** — Schedule `pg_dump` via cron

---

## 🐛 Troubleshooting

### Backend won't start

```bash
# Check logs
docker compose logs backend

# Common issues:
# - Port 8000 already in use → edit docker-compose.yml
# - DB not ready → wait 10s and restart backend
```

### Frontend can't connect to API

```bash
# Verify backend is running
curl http://localhost:8000/experiments/

# Check Vite proxy in vite.config.js
# For production, set VITE_API_BASE_URL in .env
```

### LLM diff analysis not working

```bash
# If using Groq: check API key in .env
GROQ_API_KEY=gsk_...

# If using Ollama (local):
# Start Ollama server first:
ollama serve
ollama pull mistral

# Verify in .env:
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
```

### Celery worker not processing tasks

```bash
# Check worker logs
docker compose logs worker

# Restart services
docker compose restart worker beat
```

### No metrics showing in dashboard

```bash
# 1. Verify events are being received
docker compose exec db psql -U autoab -d autoab_db -c "SELECT COUNT(*) FROM events;"

# 2. Check metric snapshots
docker compose exec db psql -U autoab -d autoab_db -c "SELECT * FROM metric_snapshots ORDER BY snapshot_at DESC LIMIT 5;"

# 3. Manually trigger snapshot computation
docker compose exec backend python -c "from workers.metric_tasks import compute_metric_snapshots; compute_metric_snapshots.delay()"
```

---

## 🚀 Deployment

### Docker Compose (Simple)

Already configured! Just deploy the entire folder to a VPS:

```bash
scp -r autoab/ user@your-server:/opt/
ssh user@your-server
cd /opt/autoab
docker compose up -d
```

### Kubernetes

See `autoab/k8s/` (create manifests for each service)

### Cloud Platforms

- **AWS:** ECS + RDS + ElastiCache
- **GCP:** Cloud Run + Cloud SQL + Memorystore
- **Azure:** Container Instances + Azure DB for PostgreSQL

---

## 📈 Roadmap

- [x] Backend API (FastAPI)
- [x] Database models (PostgreSQL + TimescaleDB)
- [x] JavaScript SDK
- [x] Celery workers (metrics, auto-stop)
- [x] LLM diff analysis (Groq + Ollama)
- [x] Statistical tests (Z, T, Mann-Whitney, Bayesian)
- [x] React dashboard
- [x] Demo apps (A/B versions)
- [x] Locust traffic simulator
- [ ] WebSocket live updates (Phase 3)
- [ ] Multi-armed bandit optimization (Phase 4)
- [ ] Sequential testing (always-valid inference)
- [ ] Segment-level analysis (automatic cohort detection)
- [ ] Experiment templates library
- [ ] Slack/email notifications
- [ ] Experiment versioning & rollback

---

## 🤝 Contributing

1. Fork the repo
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feature/amazing-feature`
5. Open Pull Request

---

## 📝 License

MIT License — see LICENSE file for details

---

## 🙏 Acknowledgements

- **Groq** — Free Llama 3.1 70B API (14,400 req/day)
- **Ollama** — Local LLM runtime
- **shadcn/ui** — Beautiful React components
- **Recharts** — Composable charting library
- **FastAPI** — Modern Python web framework
- **TimescaleDB** — Time-series PostgreSQL extension

---

## 📬 Support

- **Issues:** [GitHub Issues](https://github.com/your-repo/autoab/issues)
- **Documentation:** See `backend/README.md`, `frontend/README.md`, `sdk/README.md`

---

**Built with ❤️ as a fully automated, AI-powered A/B testing platform**

🚀 **Star this repo if you find it useful!**
