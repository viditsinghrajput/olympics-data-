# Olympics Data Analysis — FastAPI + Streamlit on Render

This project splits your notebook into two services:

- **`backend/`** — a FastAPI app that loads `athlete_events.csv` + `noc_regions.csv`,
  does all the pandas analysis from the notebook, and exposes it as JSON endpoints.
- **`frontend/`** — a Streamlit app that calls the FastAPI backend over HTTP and
  renders the same charts/tables the notebook produced (medal tally, overall
  analysis, country-wise analysis, athlete-wise analysis).

```
project/
├── backend/
│   ├── main.py
│   ├── helper.py
│   ├── requirements.txt
│   ├── athlete_events.csv
│   └── noc_regions.csv
├── frontend/
│   ├── app.py
│   └── requirements.txt
└── render.yaml
```

## 1. Run it locally first

```bash
# Terminal 1 - backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 2 - frontend
cd frontend
pip install -r requirements.txt
export BACKEND_URL=http://localhost:8000   # Windows: set BACKEND_URL=http://localhost:8000
streamlit run app.py
```

Open http://localhost:8501 — it should pull data from http://localhost:8000.

## 2. Push to GitHub

Create a new repo and push this whole `project/` folder (rename it whatever
you like) to GitHub. Render deploys straight from a GitHub repo.

```bash
git init
git add .
git commit -m "Olympics data analysis: FastAPI + Streamlit"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

> The CSV is ~40MB, which is well under GitHub's 100MB file limit, so a plain
> commit works fine — no Git LFS needed.

## 3. Deploy on Render

You have two options — pick whichever you prefer.

### Option A: One-click Blueprint (uses `render.yaml`)

1. Go to https://dashboard.render.com/blueprints and click **New Blueprint Instance**.
2. Connect your GitHub repo. Render will read `render.yaml` and propose two
   services: `olympics-api` and `olympics-frontend`.
3. Click **Apply** — both services will build and deploy.
4. Once `olympics-api` is live, copy its public URL (e.g.
   `https://olympics-api.onrender.com`).
5. Go to the `olympics-frontend` service → **Environment** tab → set
   `BACKEND_URL` to that URL → save (this triggers a redeploy).

### Option B: Manually create two Web Services

**Backend:**
1. Render dashboard → **New** → **Web Service** → connect your repo.
2. **Root Directory**: `backend`
3. **Runtime**: Python 3
4. **Build Command**: `pip install -r requirements.txt`
5. **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Deploy, then copy the resulting URL, e.g. `https://olympics-api.onrender.com`.

**Frontend:**
1. Render dashboard → **New** → **Web Service** → same repo.
2. **Root Directory**: `frontend`
3. **Runtime**: Python 3
4. **Build Command**: `pip install -r requirements.txt`
5. **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
6. Add an environment variable: `BACKEND_URL` = the backend URL from above.
7. Deploy.

Once both are live, open the frontend's URL — that's your deployed app.

## Notes

- Render's free tier spins services down after inactivity, so the first
  request after idling can take ~30-60s (both the API waking up and it
  re-loading the ~40MB CSV into memory).
- CORS is already enabled (`allow_origins=["*"]`) in `main.py` so the
  Streamlit app can call the API from a different Render domain. Tighten this
  to your frontend's exact URL once deployed, if you want.
- If you ever change the data files, just replace
  `backend/athlete_events.csv` / `backend/noc_regions.csv` and redeploy the
  backend — no other code changes needed.
