# Cursed Doll

A small starting point for the game logic.

## Current Logic

Each player starts by rolling six six-sided dice.

After every roll, the player keeps all dice matching one number, then rerolls the rest.
The default strategy keeps the number that appears most often. If multiple numbers are
tied, it keeps the lowest tied number. This repeats until all six dice are kept.

Run it with:

```bash
python cursed_doll.py 2
```

For repeatable rolls while testing:

```bash
python cursed_doll.py 2 --seed 42
```
