# Cursed Doll

A small starting point for the game logic.

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

- If the final total is `7`, `8`, `9`, or `10`, the player puts that many rolled dolls
  into the matching room.
- If the final total is `11` or more, the player puts that many rolled dolls into
  room `11`.
- If the final total is below `7`, no dolls are placed.

Players cannot place more dolls than they have remaining.

Doll placement is resolved immediately after each player's turn. The game ends as
soon as a player has no dolls remaining, and that player wins.

Run a full game with:

```bash
python cursed_doll.py 2
```

To choose the kept face yourself after each roll, and decide whether to stop after
reaching 7 or more:

```bash
python cursed_doll.py 2 --interactive
```

Interactive choices are labeled with letters like `a`, `b`, and `c` so they do not
overlap with numeric die faces. Each prompt shows the current player and the dice
that player has kept so far. It also shows every player's remaining dolls and the
current dolls in each room. Prompts and final results are separated with console
dividers so each turn is easier to scan. The prompt also counts dolls in the current
roll, where `one doll` counts as 1 and `two dolls` counts as 2.

For repeatable rolls while testing:

```bash
python cursed_doll.py 2 --seed 42
```

## Code Structure

- `dice.py`: die faces, die values, rolling helpers, and dice formatting.
- `player_turn.py`: player choices, stop rules, turn progression, and result formatting.
- `game.py`: player doll supply, doll rooms, and room placement rules.
- `cursed_doll.py`: command-line entry point.
