# Cursed Doll

Cursed Doll is a dice-and-doll table game with a command-line implementation,
a static GitHub Pages web app, and CPU-only reinforcement-learning experiments.

Current version: `v3.0`

Live site:

```text
https://defect111111.github.io/Cursed-Doll/
```

## What Is In v3.0

`v3.0` is the static web release:

- Browser-side game engine for GitHub Pages.
- Playable React table UI with no backend requirement.
- English and Simplified Chinese UI.
- Detailed in-game rules panel on the start page and play page.
- Visible version information in the web page.
- CPU-only AI training, evaluation, and demo scripts.

## Quick Start

Install frontend packages:

```bash
npm install
```

Run the web app locally:

```bash
npm run dev
```

Run the command-line game:

```bash
python -m cursed_doll.cli 2 --interactive
```

Run the test suite:

```bash
npm run test:js
python -m pytest -q
```

Build the checked-in GitHub Pages files:

```bash
npm run build:pages
```

## Game Rules

### Goal

Each player starts with 10 dolls. Rooms `7`, `8`, `9`, and `10` each start with
1 doll. Room `11` starts empty.

The goal is to get rid of your dolls. A player wins only when their own turn is
about to begin and they have 0 dolls. Reaching 0 dolls during a turn does not win
immediately.

### Dice

The six die faces are:

- `1`
- `2`
- `3`
- `4`
- `one doll`
- `two dolls`

Only numeric faces count toward the kept total. Doll faces do not add to the
total; they only count how many dolls were rolled this turn.

### Reserving Dice

At the start of a turn, the player rolls 6 dice. After each roll, the player
chooses one face to reserve. All dice showing that face are kept together, and
the rest can be rolled later.

Each face can be reserved only once per turn. For example, after keeping `3`,
that player cannot keep `3` again on a later roll in the same turn.

If a roll has no face that can be newly reserved, the turn ends immediately.

### Stopping

If the kept numeric total is below 7, the player must continue whenever there are
dice left and an available face to reserve.

If the kept numeric total is 7 or higher, the player may stop and ignore all
unkept dice. If the player continues, they roll the remaining dice.

### Room Effects

After the turn ends, the kept dice produce a final numeric total and a rolled
doll count. `one doll` counts as 1 rolled doll, and `two dolls` counts as 2
rolled dolls.

- Final totals `7`, `8`, `9`, and `10` adjust the matching room to exactly the
  rolled doll count. If the room has fewer dolls, the player adds the difference
  from hand. If the room has more dolls, the player takes the difference back.
- A final total of `11` or higher adds the rolled doll count into room `11`.
  Room `11` is never adjusted downward.
- A final total of `6` or lower makes the player take all dolls from one fullest
  room among `7`, `8`, `9`, and `10`. If several rooms tie for most dolls, the
  player chooses one tied room.

Players cannot place more dolls than they have remaining.

### Gifts And Overflow

If the player added at least 1 doll to any room this turn and kept any `1` faces,
they may give 1 doll to another player for each kept `1`. Giving is optional and
happens one doll at a time.

After every turn, every player checks their hand. Any player with more than 10
dolls moves the extra dolls above 10 into room `11`.

## Web App

The public web app is static. It runs entirely in the browser and does not need
FastAPI, Python, a database, or a server runtime on GitHub Pages.

Run locally:

```bash
npm run dev
```

Build normally:

```bash
npm run build
```

Build and sync the root files used by branch-root GitHub Pages:

```bash
npm run build:pages
```

Preview the production build locally:

```bash
npm run preview
```

The Vite base path is `/Cursed-Doll/`, matching the GitHub Pages URL.

GitHub Pages deployment is handled by `.github/workflows/deploy-pages.yml`.
The checked-in root `index.html` and `assets/` files are also refreshed by
`npm run build:pages` because this repository previously served Pages from the
branch root.

The FastAPI backend in `web/backend.py` remains available for local experiments,
but the current GitHub Pages app does not call it.

## Command-Line Game

Run a full game:

```bash
python -m cursed_doll.cli 2
```

Run the interactive version:

```bash
python -m cursed_doll.cli 2 --interactive
```

Use a fixed seed while testing:

```bash
python -m cursed_doll.cli 2 --seed 42
```

Interactive choices are labeled with letters so they do not overlap with numeric
die faces. Prompts show the current player, kept dice, current room dolls, player
doll counts, rolled doll count, tied-room choices, and optional gift choices.

## AI Training

The AI code is CPU-only. No NVIDIA driver or CUDA installation is required.

Install optional AI dependencies:

```bash
pip install -r requirements-ai.txt
```

Train a single-turn masked PPO actor-critic policy:

```bash
python -m ai.train --updates 40 --episodes-per-update 512
```

Evaluate a saved turn policy:

```bash
python -m ai.evaluate --model-path models/turn_policy.pt --episodes 2000
```

Show one model-controlled turn:

```bash
python -m ai.demo --model-path models/turn_policy.pt
```

Train a two-player self-play policy:

```bash
python -m ai.self_play --updates 40 --games-per-update 64 --eval-games 100 --run-name self_play_first
```

Evaluate a self-play policy:

```bash
python -m ai.self_play_evaluate --model-path models/self_play_policy.pt --games 500
```

Show a self-play rollout:

```bash
python -m ai.self_play_demo --model-path models/self_play_policy.pt
```

Training runs write organized logs under `training_runs/`, including
`config.json`, `metrics.csv`, and `summary.json`.

## Project Structure

- `cursed_doll/`: core Python game package.
- `cursed_doll/dice.py`: die faces, die values, rolling helpers, and formatting.
- `cursed_doll/player_turn.py`: player choices, stop rules, and turn progression.
- `cursed_doll/game.py`: player doll supply, rooms, placement, gifts, and wins.
- `cursed_doll/cli.py`: command-line entry point.
- `src/`: React frontend for the browser table.
- `src/gameLogic.js`: browser-side game engine used by GitHub Pages.
- `src/gameLogic.test.mjs`: JavaScript regression tests.
- `web/backend.py`: optional FastAPI game state API for local experiments.
- `ai/`: reinforcement-learning tools.
- `tests/`: Python regression tests.
- `scripts/sync-pages-root.mjs`: copies Vite output to the repository root for
  branch-root Pages publishing.

## Version History

- `v3.0`: static GitHub Pages web app, bilingual UI, detailed rules panel, visible
  web version, and organized AI tooling.
- `v2.0`: first playable web frontend and local web development setup.
- `v1.0`: complete command-line rule implementation with interactive choices.
