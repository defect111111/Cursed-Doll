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

Doll placement is resolved immediately after each player's turn. The game ends as
soon as a player has no dolls remaining, and that player wins.

Run a full game with:

```bash
python cursed_doll.py 2
```

To choose the kept face yourself after each roll, decide whether to stop after
reaching 7 or more, choose between tied fullest rooms, and choose optional gifts:

```bash
python cursed_doll.py 2 --interactive
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
python cursed_doll.py 2 --seed 42
```

## Code Structure

- `dice.py`: die faces, die values, rolling helpers, and dice formatting.
- `player_turn.py`: player choices, stop rules, turn progression, and result formatting.
- `game.py`: player doll supply, doll rooms, and room placement rules.
- `cursed_doll.py`: command-line entry point.
