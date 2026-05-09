# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run the app (dev mode with auto-reload)
uv run python -m poker_range_practice

# Run tests
uv run pytest

# Run a single test file
uv run pytest path/to/test_file.py

# Docker (production / server deployment)
docker compose up -d --build
```

The app runs at `http://localhost:5000`.

## Architecture

This is a **FastAPI** web app for practicing GTO poker ranges. The backend serves a JSON API; the frontend is vanilla JS/HTML/CSS served as static files.

### Entry points

- [src/poker_range_practice/__init__.py](src/poker_range_practice/__init__.py) — `create_app()` factory that wires all API routes, then mounts static files last (so `/api/*` routes take precedence). `main()` launches uvicorn with reload.
- [src/poker_range_practice/__main__.py](src/poker_range_practice/__main__.py) — calls `main()` when invoked as `python -m poker_range_practice`.

### Core modules

| Module | Role |
|---|---|
| [poker_hands.py](src/poker_range_practice/poker_hands.py) | `Hand` class (canonical `AKs`/`T9o`/`AA` notation), range notation parser (`22+`, `A2s+`, `KJo-KTo`, etc.), `find_closest_hand_in_range`, `find_bottom_of_range_category` |
| [range_manager.py](src/poker_range_practice/range_manager.py) | Loads `ranges.json`; returns `{Hand: action_str}` dicts. Handles both simple string ranges (binary in/fold) and complex dict ranges (multi-action: 3bet/call/fold). |
| [flop/](src/poker_range_practice/flop/) | Flop strategy sub-package (see below) |

### Range data format (`ranges.json`)

```json
{
  "_scenario_labels": { "BTN/vs BB": "BTN vs BB cbet" },
  "BTN": {
    "open": {
      "100bb": "22+, AKs, ...",
      "50bb": { "3bet": "QQ+, AKs", "call": "TT-99, AQs" }
    },
    "vs BB": { "100bb": "..." }
  }
}
```

- `_scenario_labels` is a metadata key used for labeling scenarios in **eval mode**.
- A range value can be a **string** (all listed hands map to `"in_range"`) or a **dict** (each key is an action label mapping to a range string).
- `RangeManager.get_range()` always returns `{Hand: action_str}` regardless of which format is used.

### Flop sub-package (`flop/`)

Routing logic lives in [flop/strategy.py](src/poker_range_practice/flop/strategy.py) — `get_cbet_recommendation()` dispatches to the right module based on hero/villain positions:

| Module | Scenario |
|---|---|
| `cbet_vs_bb.py` | IP raiser (BTN/CO) c-bets vs BB |
| `cbet_vs_sb.py` | BTN c-bets vs SB |
| `cbet_bvb.py` | SB raises vs BB (BvB) |
| `cbet_limp_sb.py` | SB limp-raises vs BB |
| `bb_defense.py` | BB defends vs IP c-bet |
| `hand_eval.py` | `evaluate_hand()` → `HandStrength` enum; `Card` dataclass |

Board texture classification (`classify_board_vs_bb`) lives in `cbet_vs_bb.py` and is reused elsewhere; it returns one of `EXTRA_DRY / INTERMEDIAIRE / DRAWY`.

### Practice modes (frontend ↔ API)

1. **Range quiz** (`index.html` / `app.js`) — user picks position/action/stack, gets random hands, answers in/fold (or sub-actions for complex ranges). Session stored server-side via Starlette `SessionMiddleware`.
2. **Eval mode** — cross-scenario quiz: randomly picks from multiple positions/stack depths and all available scenarios. Uses `/api/eval/*` routes.
3. **Flop mode** (`flop.js`) — deals a concrete flop + hands, quizzes c-bet decision (size + bet/check) and BB defense. Uses `/api/flop/*` routes. Hero hands are always drawn from the appropriate preflop range.

### Session state

Sessions are cookie-based (Starlette `SessionMiddleware`). Two independent session keys are used:
- `"config"` — active range quiz session (position/action/stack_depth)
- `"eval_config"` — active eval session (list of combos)

### Adding/editing ranges

Edit `src/poker_range_practice/ranges.json`. Range notation supports: `22+`, `A2s+`, `KJo+`, `K9s-KQs`, individual hands, comma-separated combos. Position keys must match exactly what the frontend sends.
