import assert from "node:assert/strict";

import { createGame } from "./gameLogic.js";

const game = createGame({ playerCount: 2, seed: 42 });

assert.ok(Array.isArray(game.roll));
assert.equal(game.roll.length, game.remaining_dice);
assert.deepEqual(game.roll, game.current_roll);

console.log("gameLogic tests passed");
