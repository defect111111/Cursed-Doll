import assert from "node:assert/strict";

import { applyGameAction, createGame } from "./gameLogic.js";

const game = createGame({ playerCount: 2, seed: 42 });

assert.equal(game.phase, "ready_to_roll");
assert.ok(Array.isArray(game.roll));
assert.equal(game.roll.length, 0);

const rolled = applyGameAction(game, { action: "roll" });

assert.equal(rolled.phase, "choose_face");
assert.ok(Array.isArray(rolled.roll));
assert.equal(rolled.roll.length, rolled.remaining_dice);
assert.deepEqual(rolled.roll, rolled.current_roll);
assert.ok(rolled.choices.length > 0);

console.log("gameLogic tests passed");
