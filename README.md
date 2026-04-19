# HappyRobot Challenge — Inbound Carrier Sales Automation

AI-powered voice agent that automates inbound carrier calls for freight brokerages. Built with HappyRobot, FastAPI, and Streamlit.

---

## Live Deployment

- **API Base URL:** https://happyrobot-challenge-production-0695.up.railway.app
- **HappyRobot Workflow:** https://workflows.platform.happyrobot.ai/hooks/8jho2yputz0m
- **Health Check:** https://happyrobot-challenge-production-0695.up.railway.app/health

---

## What it does

Carriers call in looking for loads. The agent:
1. Verifies their MC number
2. Searches available loads by lane
3. Negotiates pricing automatically (up to 3 rounds)
4. Transfers agreed deals to a sales rep
5. Logs call data and metrics to a dashboard

---

## Project Structure

```
happyrobot-challenge/
├── app/
│   └── main.py          # FastAPI backend
├── dashboard/
│   └── dashboard.py     # Streamlit dashboard
├── data/
│   ├── loads.csv        # Available loads
│   └── call_logs.csv    # Call history (auto-generated)
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Running Locally

### 1. Clone the repo
```bash
git clone https://github.com/saitgr/happyrobot-challenge.git
cd happyrobot-challenge
```

### 2. Create and activate virtual environment
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Start the API
```bash
uvicorn app.main:app --port 8000
```

### 5. Start the dashboard (new terminal)
```bash
source .venv/bin/activate
streamlit run dashboard/dashboard.py
```

- API: http://localhost:8000
- Dashboard: http://localhost:8501

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/verify-carrier` | POST | Verifies carrier eligibility by MC number |
| `/search-loads` | POST | Returns loads matching origin, destination, equipment type |
| `/evaluate-offer` | POST | Evaluates carrier counter-offer |
| `/log-call` | POST | Saves call data and outcome |
| `/loads` | GET | Returns all available loads |
| `/health` | GET | Health check |

All endpoints require the header `x-api-key: <your-key>`.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `API_KEY` | `dev-key` | API key for endpoint authentication |
| `FMCSA_API_KEY` | - | FMCSA API key for production carrier verification |

---

## Docker

### Build and run
```bash
docker build -t happyrobot .
docker run -p 8000:8000 -e API_KEY=your-key happyrobot
```

---

## Cloud Deployment (Railway)

### Access the deployment
- **URL:** https://happyrobot-challenge-production-0695.up.railway.app
- **Authentication:** add header `x-api-key: dev-key` to all requests
- **Health check:** https://happyrobot-challenge-production-0695.up.railway.app/health

### Reproduce the deployment
1. Fork this repository
2. Create an account at [railway.app](https://railway.app)
3. Click **New Project** → **Deploy from GitHub repo**
4. Select this repository
5. Add environment variable: `API_KEY=dev-key`
6. Railway detects the Dockerfile and deploys automatically
7. Go to **Settings** → **Networking** → **Generate Domain** to get your public HTTPS URL

---

## HappyRobot Configuration

- **Platform:** [happyrobot.ai](https://happyrobot.ai)
- **Workflow URL:** https://workflows.platform.happyrobot.ai/hooks/8jho2yputz0m
- **Trigger:** Web call trigger (no phone number required)
- **Tools:** `verify_carrier`, `search_loads`, `evaluate_offer`, `transfer_to_sales_rep`
- **Post-call:** `Analyze Call Details` → `POST /log-call`