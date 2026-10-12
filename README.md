# Cursed Doll

A dice-and-doll table game with a command-line version and a playable local web
frontend.

## Version

Current version: `v2.0`

`v2.0` adds the first playable web frontend: a FastAPI backend for game state,
a Vite React table UI, local development setup, and clearer startup diagnostics.

`v1.0` is the complete command-line rule implementation with interactive choices
for dice patterns, stopping, tied rooms, and optional doll gifts.

## Current Logic

Each player starts by rolling six custom dice. The six die faces are:

- `1`
- `2`
- `3`
- `4`
- `one doll`
- `two dolls`

Only numeric faces count toward the kept total. Doll faces do not add to the total.

After every roll, the player keeps all dice matching one face, then rerolls the rest.
A player can only reserve each face once. For example, after keeping `3`, that player
cannot keep `3` again on a later roll.
If a roll has no face that the player can newly reserve, that player's turn ends.
If the kept dice total is 7 or more, the player may stop and ignore any remaining dice.
Otherwise, the player continues until no dice remain.

The default strategy first keeps a face that reaches 7 or more, then stops. If no
face reaches 7, it keeps the largest matching group.

## Doll Rooms

Each player starts the game with 10 dolls. After a player's turn, the final kept dice
produce a number total and a doll count. `one doll` counts as 1 doll, and `two dolls`
counts as 2 dolls.

There are five doll rooms: `7`, `8`, `9`, `10`, and `11`.
Rooms `7` through `10` begin with 1 doll each. Room `11` begins empty.

- If the final total is `7`, `8`, `9`, or `10`, the matching room is adjusted to
  the rolled doll count. If the room has fewer dolls, the player adds the difference.
  If the room has more dolls, the player takes the difference back.
- If the final total is `11` or more, the player puts that many rolled dolls into
  room `11`.
- If the final total is `6` or less, the player takes all dolls from the fullest
  room among `7`, `8`, `9`, and `10`. If multiple rooms are tied for most dolls,
  the lowest-numbered tied room is chosen.

Players cannot place more dolls than they have remaining.
If the player kept one or more `1` faces and placed at least one doll into a room,
the player gives one doll to another player for each kept `1`, up to the number of
dolls the player has available. The default strategy gives these dolls to the next
player in turn order. A one-player game has no valid recipient.
After every turn, any player with more than 10 dolls returns the extra dolls to
room `11`.

Doll placement is resolved immediately after each player's turn. Reaching zero
dolls does not immediately end the game. The game ends only when a player's turn
is about to start and that player has zero dolls. That player wins. A player who
reaches zero may still receive dolls from another player's optional gift before
their next turn, in which case they continue playing.

Run a full game with:

```bash
python -m cursed_doll.cli 2
```

To choose the kept face yourself after each roll, decide whether to stop after
reaching 7 or more, choose between tied fullest rooms, and choose optional gifts:

```bash
python -m cursed_doll.cli 2 --interactive
```

Interactive choices are labeled with letters like `a`, `b`, and `c` so they do not
overlap with numeric die faces. Each prompt shows the current player and the dice
that player has kept so far. It also shows every player's remaining dolls and the
current dolls in each room. Prompts and final results are separated with console
dividers so each turn is easier to scan. The prompt also counts dolls in the current
roll, where `one doll` counts as 1 and `two dolls` counts as 2. Gift prompts include
a `Stop giving` option because giving dolls for kept `1` faces is optional.

For repeatable rolls while testing:

```bash
python -m cursed_doll.cli 2 --seed 42
```

## GitHub Pages Web App

This branch is organized as a static GitHub Pages web app. The playable table
runs entirely in the browser with a small JavaScript game engine, so the public
site does not need FastAPI, Python, or a database server.

Install frontend packages:

```bash
npm install
```

Run the local web app:

```bash
npm run dev
```

Then open `http://127.0.0.1:5173`.

Build the static site:

```bash
npm run build
```

Preview the production build locally:

```bash
npm run preview
```

The Vite base path is set to `/Cursed-Doll/`, matching the expected GitHub Pages
URL:

```text
https://defect111111.github.io/Cursed-Doll/
```

GitHub Pages deployment is handled by `.github/workflows/deploy-pages.yml`.
In the GitHub repository settings, set Pages to use GitHub Actions as the source,
then push this branch or run the workflow manually.

The FastAPI backend in `web/backend.py` is still available for local experiments,
but the GitHub Pages web app does not call it.

## Turn AI Training

The first AI framework trains a small CPU-only turn optimizer. It does not try to
win the whole game. It only plays one player's turn and tries to maximize:

```text
reward = starting dolls - ending dolls
```

The AI environment randomizes the player's starting dolls and room dolls, then
lets an agent choose dice patterns, stop or continue, choose tied rooms, and give
optional dolls. Rooms `7` through `10` are sampled from a Gaussian distribution
with mean `1` and variance `1`, rounded to whole dolls and clipped at zero. Room
`11` starts at `0` and is not included in the model observation because its
existing doll count does not influence single-turn decisions. Other players are
intentionally ignored for this first model.

Install the optional CPU PyTorch dependency:

```bash
pip install -r requirements-ai.txt
```

Train a small masked PPO actor-critic policy:

```bash
python -m ai.train --updates 40 --episodes-per-update 512
```

Each run writes organized local logs under `training_runs/`, including
`config.json`, `metrics.csv`, and `summary.json`. The best model is saved to
`models/turn_policy.pt` by default.

Evaluate a saved policy against random and heuristic baselines:

```bash
python -m ai.evaluate --model-path models/turn_policy.pt --episodes 2000
```

Show a single model-controlled turn with each decision printed:

```bash
python -m ai.demo --model-path models/turn_policy.pt
```

Show a full model-controlled self-play game:

```bash
python -m ai.self_play_demo --model-path models/self_play_policy.pt
```

Evaluate a full-game self-play policy:

```bash
python -m ai.self_play_evaluate --model-path models/self_play_policy.pt --games 500
```

Train a first two-player self-play policy:

```bash
python -m ai.self_play --updates 40 --games-per-update 64 --eval-games 100 --run-name self_play_first
```

Training always uses CPU. No NVIDIA driver or CUDA installation is required.

## Code Structure

- `cursed_doll/`: core game package.
- `cursed_doll/dice.py`: die faces, die values, rolling helpers, and dice formatting.
- `cursed_doll/player_turn.py`: player choices, stop rules, turn progression, and result formatting.
- `cursed_doll/game.py`: player doll supply, doll rooms, and room placement rules.
- `cursed_doll/cli.py`: command-line entry point.
- `web/backend.py`: optional FastAPI game state API for local experiments.
- `src/`: React frontend for the playable table UI.
- `src/gameLogic.js`: browser-side game engine used by the GitHub Pages app.
- `ai/`: single-turn reinforcement-learning package.
- `ai/env.py`: turn environment with legal action masks.
- `ai/agents.py`: random and heuristic turn baselines.
- `ai/model.py`: small masked actor-critic network.
- `ai/train.py`: CPU PPO trainer.
- `ai/evaluate.py`: saved-policy evaluator.
- `ai/demo.py`: single-turn policy rollout demo.
- `ai/self_play.py`: two-player self-play trainer.
- `ai/self_play_evaluate.py`: full-game self-play evaluator.
- `ai/self_play_demo.py`: full-game self-play rollout demo.
- `tests/`: Python regression tests.
