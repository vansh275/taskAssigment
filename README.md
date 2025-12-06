# 📌 Message to the Reviewers

Thank you for reviewing this project. Since this is my first backend project using Python and FastAPI, I learned Python and built the project simultaneously. This demonstrates my ability to learn quickly, improve continuously, and stay dedicated while working with new technologies.

Because of this learning curve, I haven't deployed the project on Vercel yet. Deployment is still fully achievable: the backend can run on any standard server, the database can connect to any managed PostgreSQL service, and the storage layer can be integrated with any cloud storage provider.

If given more time, I can complete the remaining refinements and fully deploy the application.

## Table of contents

* [About](#about)
* [Tech stack](#tech-stack)
* [Features](#features)
* [Repository structure](#repository-structure)
* [Requirements](#requirements)
* [Quick start (development)](#quick-start-development)

  * [Backend (Python/FastAPI)](#backend-pythonfastapi)
  * [Frontend (static)](#frontend-static)
* [API Endpoints (example)](#api-endpoints-example)
* [Deployment notes](#deployment-notes)
* [Contributing](#contributing)
* [License](#license)
* [Contact](#contact)

---

## About

A simple web app that lets you upload, manage, and play audio tracks. The backend handles file uploads and APIs, while the frontend provides a clean interface for listening to tracks.

---

## Tech stack

* Backend: Python (FastAPI / Uvicorn).
* Frontend: HTML, CSS, JavaScript (served from `static/`).
* Audio assets: stored under `tracks/`.

---

## Features (assumed / common patterns)

* Upload audio tracks via API.
* Serve a web UI to browse and play tracks.
* Playlist generation endpoint (e.g. `/api/playlist/generate`).
* Static file serving for frontend and audio tracks.


---

## Repository structure

```
taskAssigment/
├─ backend/         # Python backend (API + static file serving)
├─ static/          # Frontend files (index.html, app.js, styles)
├─ tracks/          # Audio files used by the app
├─ .gitignore
└─ structure.txt    # (project structure summary)
```

---

## Requirements

Recommended developer tools:

* Python 3.10+ (3.11 recommended)
* pip
* A virtual environment (venv)
* Node.js (optional, only if you plan to use tooling for the frontend)

---

## Quick start (development)

> **Note:** these are standard commands. If your project uses a different entrypoint, replace the commands accordingly.

### Backend (Python / FastAPI)

1. Create and activate a virtual environment:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

2. Install dependencies

```bash
pip install -r backend/requirements.txt
```

3. Run the server with Uvicorn (adjust the import path to your app):

```bash
# example paths — change as needed, can skip --host and --port ,then open valid link
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

4. Open the frontend in your browser (if backend serves static files) at:

```
http://127.0.0.1:8000/
```

Or, open `static/index.html` directly in the browser while testing.

### Frontend (static)

* The `static/` folder contains the client. If backend serves it (e.g. `app.mount('/static', ...)`), visiting the server root will show the UI.
* Alternatively, open `static/index.html` locally while developing.

---

## API Endpoints (example)

Below are example endpoints commonly used in this type of project. Replace or extend them with the real routes from your backend code.

* `POST /api/track/upload` - Upload a track (multipart/form-data). Field name: `file`.
* `GET  /api/tracks` - List available tracks.
* `GET  /tracks/<filename>` - Serve an audio file.
* `POST /api/playlist/generate` - Generate a playlist from a prompt (JSON body).

---
