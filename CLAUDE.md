# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A route optimizer for deliveries with time windows (the Travelling Salesman Problem with Time Windows, TSPTW) on real street data for Brașov, Romania. It runs several optimization algorithms on the same delivery scenario, compares them, and shows the routes on a map.

It is a web app first. Mobile and desktop versions will wrap the same web app later (installable web app, then Capacitor, then Tauri), so nothing may be built in a way that only works in a desktop browser.

## Current state

The repository is being rebuilt from a small prototype. **The architecture below is the target, and parts of it do not exist yet.** Create folders as described when they are first needed, and update this file whenever the structure or the commands change.

What exists today:

- **Backend solver core** in `backend/app/`: the problem model, `evaluate`, the solver interface and registry, a brute-force solver and a command-line runner. There is no API, database or OSRM client yet.
- **Routing engine:** OSRM through `docker-compose.yml`.
- **Frontend:** still the prototype. `frontend/src/App.jsx` is a single file with hardcoded results, Leaflet, and Tailwind loaded from a CDN script. It is to be replaced, not built upon.

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

Backend, run inside `backend/`. It is a `uv` project on Python 3.14; never use `pip install`:

```bash
uv sync                                   # create backend/.venv and install dependencies
uv run pytest                             # all tests
uv run pytest tests/test_evaluation.py    # one file
uv run pytest tests/test_evaluation.py::test_brasov_route_in_the_prototype_order   # one test
uv run python -m app.cli algorithms       # list the available algorithms
uv run python -m app.cli solve ../data/instances/brasov-5.json --algorithm brute-force
uv add <package>                          # add a dependency (uv add --dev for test tools)
```

## Architecture (target)

Client and server are separate, and **all optimization runs on the backend**. Every client (web, mobile, desktop) is a thin screen over one REST API, so no solver logic may live in the frontend. Solver progress reaches the client as server-sent events.

```
frontend/src/
  features/<feature>/   views and view models of one screen (planner, compare)
  models/               TypeScript types shared across features
  api/                  every call to the backend
  map/                  MapLibre components
backend/app/
  cli.py                command line: solve one instance file and print the route
  api/                  FastAPI routes and request/response schemas
  services/             one function per use case, plus the interfaces it needs
  domain/               problem model, tour evaluation, solvers/ (pure Python)
  infrastructure/       instance files, OSRM client, address search, database
backend/experiments/    command-line experiment runner and its results
backend/tests/
data/instances/         problem instances as JSON (tracked)
data/osrm/              map data and OSRM's files (ignored by git, about 1.3 GB)
```

### Backend rules

- **Dependency direction:** `api` → `services` → `domain`. Nothing in `domain/` imports FastAPI, the database, an HTTP client or `infrastructure/`, and nothing in it reads files: instance files are read by `infrastructure/instance_files.py`. `cli.py`, like `api/`, only wires the other layers together.
- **Ports and adapters:** services depend on small interfaces (`typing.Protocol`), such as a matrix provider and a scenario repository, declared next to the services. `infrastructure/` implements them, and only `api/` wires the real implementations in.
- **One evaluation function:** `evaluate(instance, tour)` in `domain/evaluation.py` is the single source of truth for a route's travel time, arrival times, waiting, lateness and number of late stops. Solvers never compute cost their own way. Any faster incremental calculation must be tested against `evaluate`.
- **One file per algorithm:** each solver lives in `domain/solvers/`, implements the shared `Solver` interface from `base.py` (`solve(instance, params, on_progress) -> Solution`) and is added to the registry in `domain/solvers/__init__.py`. The command line and the API get their algorithm list from that registry, never from a hardcoded list.
- **Solvers are pure and repeatable:** no file or network access and no global state. Randomness comes only from a generator built from the `seed` parameter (`random.Random(seed)` or `numpy.random.default_rng(seed)`), never from the module-level `random` or `numpy.random` functions. The same instance, parameters and seed must give the same result.
- **Progress:** each time a solver finds a better route, it calls `on_progress` and adds a `TracePoint` (iteration, cost) to the solution's trace. It knows nothing about HTTP or streaming.

### Problem definition (current)

- One vehicle. It leaves the depot when the depot opens and ends there.
- Time windows are soft: arriving after a window closes adds a lateness penalty and counts as a late stop. It does not make the route invalid. Returning after the depot closes adds lateness too.
- Arriving early means waiting until the window opens. Waiting itself costs nothing.
- Each customer has the same fixed service time (default 5 minutes).
- The objective is total travel time plus `lateness_weight` × total lateness (default weight 10: one second late costs like ten seconds of driving).

The rules live in `domain/evaluation.py` and the two numbers are fields of `Instance` (`domain/instance.py`), settable per instance file or from the command line. Solvers must not restate any of this.

### Algorithms in scope

Simulated Annealing, Genetic Algorithm and Ant Colony Optimization, plus a simple construction method that gives them a starting route. The 2-approximation, Christofides and Clarke-Wright are set aside: do not add them unless asked. More algorithms will come later through the same `Solver` interface.

`brute-force` already exists. It is exact but limited to 9 customers, so use it in tests as the reference answer for other solvers on small instances.

### Data conventions

- **Units inside the backend:** seconds for durations, metres for distances, seconds since midnight for times of day. Convert to minutes, kilometres or `HH:MM` only at the edges (API responses and the interface).
- **Matrices are asymmetric:** `matrix[i][j]` goes from stop `i` to stop `j`, and the two directions can differ by almost a factor of two because of one-way streets (see stops 0 and 2 in `brasov-5.json`). Never assume symmetry, and never reverse part of a route without recomputing its cost.
- **Coordinates:** models store `lat` and `lon` as separate named fields. OSRM URLs take `lon,lat`. Make that swap only inside the OSRM client.
- **Stops and tours:** a stop is identified by its position in `instance.stops`. A tour is the customers in visiting order as those positions, without the depot, which is implied at both ends. For `brasov-5` the tour `(2, 1, 3, 4)` means depot, Gara, Coresi, Piața Sfatului, Astra, depot.
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
