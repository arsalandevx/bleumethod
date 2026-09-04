# bluemethod.com — Flask site

Your site, now backed by a small Python (Flask) server. It serves the page and
handles the Contact form for real — submissions are saved to a local SQLite
database (`contacts.db`, created automatically the first time you run it).

## Project structure

```
bluemethod-site/
├── app.py              ← the backend
├── requirements.txt
├── Procfile             ← tells hosts how to start the app
├── templates/
│   └── index.html       ← your site (same design, now served by Flask)
└── contacts.db           ← created automatically, holds form submissions
```

## Run it locally

```bash
cd bluemethod-site
pip install -r requirements.txt
python app.py
```

Open **http://localhost:5000** — that's your live site, running on your machine.
Submit the contact form and it'll write a row into `contacts.db`.

To peek at submissions without opening the database file directly:

```bash
export ADMIN_TOKEN=pick-a-secret-value
python app.py
```

Then visit `http://localhost:5000/api/contacts?token=pick-a-secret-value`.

## Put it on a real, live URL

The easiest free options for a small Flask app like this are **Render** or
**Railway**. Both detect the `Procfile` automatically.

### Option A — Render.com (recommended, free tier)

1. Push this folder to a GitHub repo.
2. On [render.com](https://render.com), click **New → Web Service**, connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Deploy — Render gives you a live URL like `bluemethod.onrender.com`.
6. Later, point your real domain (`bluemethod.com`) at it under Render's
   **Settings → Custom Domain**.

### Option B — Railway.app

1. Push to GitHub, then **New Project → Deploy from GitHub repo** on
   [railway.app](https://railway.app).
2. Railway reads the `Procfile` automatically — no extra config needed.
3. Add a custom domain under the project's **Settings**.

### Option C — PythonAnywhere

Good if you want something that stays on a free tier indefinitely (no
sleep/spin-down). Follow their "Flask" quickstart and upload this folder;
point their WSGI config at `app.app`.

## One thing to know about the database

`contacts.db` is a plain SQLite file sitting next to `app.py`. That's perfect
for getting started, but most free hosts (Render, Railway free tiers) wipe
the filesystem on redeploy — so submissions won't survive a redeploy. If the
contact form becomes important to you, swap it for a hosted Postgres database
(Render and Railway both offer a free one) — say the word and I can wire that
up too.

## Environment variables you can set

| Variable      | Purpose                                              |
|---------------|-------------------------------------------------------|
| `PORT`        | Port to run on (hosts set this automatically)          |
| `ADMIN_TOKEN` | Secret needed to view `/api/contacts` — leave unset to disable that route entirely |
