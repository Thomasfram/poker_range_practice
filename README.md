# Poker Range Practice App

A simple Python application to help you practice poker ranges. Select a position, action, and stack depth, then test yourself on whether random hands are in range or not.

## Features

- **Compact Range Notation**: Define ranges using standard poker notation like `22+`, `A2s+`, `KJo+`
- **Random Hand Generation**: Practice with randomly generated hands from all 169 possible starting hands
- **Instant Feedback**: Get immediate feedback on your answers
- **Closest Hand**: When wrong, see the closest hand that IS in range
- **Score Tracking**: Track your accuracy as you practice

## Installation & Requirements
This project uses **[uv](https://github.com/astral-sh/uv)** for high-speed dependency management.

1. Install `uv` (if not already installed):
   ```bash
   pip install uv
   ```

2. Initialize environment and dependencies:
   ```bash
   uv sync
   ```

## Usage

Start the web application using `uv`:

```bash
uv run python -m poker_range_practice
```

Open your browser to: `http://localhost:5000`

2. **Open your browser:**
   - Navigate to `http://localhost:5000`

2. Select your configuration:
   - Choose position (UTG, CO, BTN, etc.)
   - Choose action (open, 3bet, etc.)
   - Choose stack depth (100bb, 50bb, 20bb, etc.)

3. Practice:
   - You'll be shown a random hand
   - Decide if it's in range or not
   - Get feedback and see your accuracy

## Adding/Editing Ranges

Edit `ranges.json` to add or modify ranges. The structure is:

```json
{
  "POSITION": {
    "ACTION": {
      "STACK_DEPTH": "range notation"
    }
  }
}
```

### Range Notation Guide

The app supports compact poker range notation:

- **Pairs**: `22+` = all pairs from 22 to AA
- **Suited hands**: `A2s+` = A2s through AKs (all suited aces)
- **Offsuit hands**: `ATo+` = ATo, AJo, AQo, AKo
- **Specific ranges**: `K9s+` = K9s, KTs, KJs, KQs
- **Individual hands**: `AKs, AQo` = just those specific hands
- **Combinations**: Separate with commas

### Example Range

```json
{
  "BTN": {
    "open": {
      "100bb": "22+, A2s+, ATo+, K9s+, KJo+, Q9s+, QJo, J9s+, JTo, T8s+, T9o, 98s, 87s, 76s, 65s, 54s",
      "50bb": "22+, A2s+, ATo+, K9s+, KJo+, Q9s+, QJo, J9s+, JTo, T8s+",
      "20bb": "22+, A7s+, ATo+, K9s+, KJo+, QJs+"
    }
  }
}
```

This BTN opening range includes:
- All pocket pairs (22+)
- All suited aces (A2s+)
- Offsuit aces from ATo+ 
- King combos from K9s+ and KJo+
- And various other suited/offsuit combinations

## File Structure

The project follows a standard Python package layout:

- `src/` - Source code directory
  - `poker_range_practice/` - Main package
    - `__init__.py` - Flask backend and app entry point
    - `__main__.py` - Execution entry point
    - `ranges.json` - Range definitions
    - `poker_hands.py` - Core logic for hands and ranges
    - `static/` - Web assets (HTML, CSS, JS)
- `pyproject.toml` - Project configuration and dependencies
- `uv.lock` - Lockfile for reproducible builds

## Tips

- Start with ranges you're less familiar with
- The "closest hand" feature helps you learn range boundaries
- Add multiple stack depths (100bb/50bb/20bb) for the same position/action to practice different scenarios
- You can have different actions like: open, 3bet, 4bet, call, etc.


Enjoy practicing! 🃏

## Docker Deployment (Proxmox / Server)

This application is containerized and ready to deploy.

### Quick Start

1.  **Clone the project** to your server.
2.  **Run with Docker Compose**:
    ```bash
    docker compose up -d --build
    ```
3.  **Access the Application**:
    - Open your browser to `http://<your-server-ip>:5000`.

### Updating

If you modify `ranges.json` or update the code, rebuild the container:

```bash
docker compose up -d --build
```
