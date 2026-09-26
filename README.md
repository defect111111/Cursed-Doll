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
If the kept dice total is 7 or more, the player may stop and ignore any remaining dice.
Otherwise, the player continues until no dice remain.

The default strategy first keeps a face that reaches 7 or more, then stops. If no
face reaches 7, it keeps the largest matching group.

Run it with:

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
that player has kept so far.

For repeatable rolls while testing:

```bash
python cursed_doll.py 2 --seed 42
```
