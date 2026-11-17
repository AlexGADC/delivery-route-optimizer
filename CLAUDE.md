# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A route optimizer for deliveries with time windows (the Travelling Salesman Problem with Time Windows, TSPTW) on real street data for Brașov, Romania. It runs several optimization algorithms on the same delivery scenario, compares them, and shows the routes on a map.

It is a web app first. Mobile and desktop versions will wrap the same web app later (installable web app, then Capacitor, then Tauri), so nothing may be built in a way that only works in a desktop browser.

## Current state

The repository is being rebuilt from a small prototype. **The architecture below is the target, and most of it does not exist yet.** Create folders as described when they are first needed, and update this file whenever the structure or the commands change.

Leftovers from the prototype, to be replaced and not built upon:

- `frontend/src/App.jsx`: a single-file prototype with hardcoded results, Leaflet, and Tailwind loaded from a CDN script.
- `backend/main.py` (empty), the empty folders `backend/algorithms/`, `backend/database/`, `backend/utils/`, and `backend/venv/`.
- `requirements.txt` and the root `package-lock.json`: unrelated to this project.

## Commands

Routing engine (OSRM). Docker Desktop must be running:

```bash
docker compose up -d osrm               # start on http://localhost:5000
docker compose down                     # stop
docker compose run --rm osrm-prepare    # one-off: rebuild OSRM's files after replacing the map
```

The first-time map download is described in the comment at the top of `docker-compose.yml`. OSRM has no home page; only request paths such as `/table/v1/driving/...` answer.

Frontend, run inside `frontend/`:

```bash
npm install
npm run dev      # development server
npm run build
npm run lint
```

Backend: not set up yet. It will be a `uv` project on Python 3.14. Never use `pip install` or the old `backend/venv`. Add the run and test commands here once it exists.

## Architecture (target)

Client and server are separate, and **all optimization runs on the backend**. Every client (web, mobile, desktop) is a thin screen over one REST API, so no solver logic may live in the frontend. Solver progress reaches the client as server-sent events.

```
frontend/src/
  features/<feature>/   views and view models of one screen (planner, compare)
  models/               TypeScript types shared across features
  api/                  every call to the backend
  map/                  MapLibre components
backend/app/
  api/                  FastAPI routes and request/response schemas
  services/             one function per use case, plus the interfaces it needs
  domain/               problem model, tour evaluation, solvers/ (pure Python)
  infrastructure/       OSRM client, address search, database
backend/experiments/    command-line experiment runner and its results
backend/tests/
data/instances/         problem instances as JSON (tracked)
data/osrm/              map data and OSRM's files (ignored by git, about 1.3 GB)
```

### Backend rules

- **Dependency direction:** `api` → `services` → `domain`. Nothing in `domain/` imports FastAPI, the database, an HTTP client or `infrastructure/`. It must run from a plain script.
- **Ports and adapters:** services depend on small interfaces (`typing.Protocol`), such as a matrix provider and a scenario repository, declared next to the services. `infrastructure/` implements them, and only `api/` wires the real implementations in.
- **One evaluation function:** `evaluate(tour)` in `domain/` is the single source of truth for a route's travel time, arrival times, waiting, lateness and number of late stops. Solvers never compute cost their own way. Any faster incremental calculation must be tested against `evaluate`.
- **One file per algorithm:** each solver lives in `domain/solvers/`, implements the shared `Solver` interface (`solve(instance, params, on_progress) -> Solution`) and registers itself by name. The algorithm list the API returns comes from that registry, never from a hardcoded list.
- **Solvers are pure and repeatable:** no file or network access and no global state. Randomness comes only from a generator built from the `seed` parameter (`random.Random(seed)` or `numpy.random.default_rng(seed)`), never from the module-level `random` or `numpy.random` functions. The same instance, parameters and seed must give the same result.
- **Progress:** a solver reports through the `on_progress` callback and records its best cost after every iteration. It knows nothing about HTTP or streaming.

### Problem definition (current)

- One vehicle, starting and ending at the depot.
- Time windows are soft: arriving after a window closes adds a lateness penalty and counts as a late stop. It does not make the route invalid.
- Arriving early means waiting until the window opens.
- Each stop has a fixed service time.
- The objective is total travel time plus the lateness penalty.

Keep these choices in one place in `domain/`, so they can change without touching the solvers.

### Algorithms in scope

Simulated Annealing, Genetic Algorithm and Ant Colony Optimization, plus a simple construction method that gives them a starting route. The 2-approximation, Christofides and Clarke-Wright are set aside: do not add them unless asked. More algorithms will come later through the same `Solver` interface.

### Data conventions

- **Units inside the backend:** seconds for durations, metres for distances, seconds since midnight for times of day. Convert to minutes, kilometres or `HH:MM` only at the edges (API responses and the interface).
- **Matrices are asymmetric:** `matrix[i][j]` goes from stop `i` to stop `j`, and the two directions can differ by almost a factor of two because of one-way streets (see stops 0 and 2 in `brasov-5.json`). Never assume symmetry, and never reverse part of a route without recomputing its cost.
- **Coordinates:** models store `lat` and `lon` as separate named fields. OSRM URLs take `lon,lat`. Make that swap only inside the OSRM client.
- **Instance files** in `data/instances/` follow the shape of `brasov-5.json`.

### External services

- **OSRM:** only the local instance from `docker-compose.yml`, called only from the backend's OSRM client. `/table` gives matrices and `/route` gives street geometry. Cache matrices so the same stops are not requested twice. Its times do not include live traffic.
- **Address search (Nominatim):** only through the backend, at most one request per second, with an identifying User-Agent, on submit only (no search-as-you-type), and cached.
- **Map background:** OpenFreeMap vector tiles, loaded directly by the client.

### Frontend rules

- New code is TypeScript with `strict` on and no `any`.
- **MVVM with hooks:**
  - *Model:* types in `models/` and backend calls in `api/`.
  - *ViewModel:* one custom hook per screen or major panel, named `use<Screen>ViewModel`, returning state plus commands. It contains no markup and no map calls.
  - *View:* components that only render what the view model returns. Small components take props; do not give each one its own view model.
- Components never call `fetch` directly. Server data goes through TanStack Query hooks in `api/`, and small shared interface state goes in a Zustand store.
- A solver run is one discriminated union (`idle`, `buildingMatrix`, `solving`, `done`, `failed`), not several boolean flags.
- MapLibre is used only inside `map/`. Routes are drawn as GeoJSON sources and layers.
- Every layout must work at phone width, because the same build is wrapped for mobile.
- Interface text is in Romanian. Code, comments and commit messages are in English.

### Tests

- Tests must pass with Docker stopped and no network: use files from `data/instances/` or a fake matrix provider, never a live OSRM.
- Every solver gets the same basic checks: the route starts and ends at the depot, visits every stop exactly once, and repeats exactly for the same seed.
- `evaluate` is tested against hand-computed cases, including early arrival (waiting) and late arrival (penalty).

### Experiments

- Experiments run from the command line without the web server and can resume after being stopped.
- Every result row records the instance, algorithm, parameters, seed and git commit. Result files are generated, never edited by hand.

## Working in this repository

- The owner must be able to explain every line of solver code. Prefer plain, readable code over clever code, and give each algorithm a short docstring covering the idea, the main steps and the source it follows.
- Do not add abstractions, libraries or services beyond what the architecture above calls for without asking first.
- Do not commit or push unless asked. A commit message has a short imperative summary line, a blank line, then a description of what changed and why.
