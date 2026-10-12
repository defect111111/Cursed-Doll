const DEFAULT_DICE_COUNT = 6;
const TARGET_KEPT_TOTAL = 7;
const INITIAL_PLAYER_DOLLS = 10;
const DOLL_ROOMS = [7, 8, 9, 10, 11];
const ADJUSTABLE_ROOMS = [7, 8, 9, 10];
const DIE_FACES = ["1", "2", "3", "4", "one doll", "two dolls"];
const FACE_VALUES = {
  1: 1,
  2: 2,
  3: 3,
  4: 4,
  "one doll": 0,
  "two dolls": 0,
};
const DOLL_COUNTS = {
  "one doll": 1,
  "two dolls": 2,
};

function normalizeSeed(seed) {
  if (seed !== null && seed !== undefined && seed !== "") {
    return Number(seed) >>> 0;
  }
  return (Date.now() ^ Math.floor(Math.random() * 0xffffffff)) >>> 0;
}

function randomUnit(game) {
  game.rng_state = (Math.imul(game.rng_state, 1664525) + 1013904223) >>> 0;
  return game.rng_state / 0x100000000;
}

function randomInt(game, minimum, maximum) {
  return minimum + Math.floor(randomUnit(game) * (maximum - minimum + 1));
}

function cloneGame(game) {
  return JSON.parse(JSON.stringify(game));
}

function createGameId() {
  if (crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `game-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
}

function createDollRooms() {
  return DOLL_ROOMS.reduce((rooms, room) => {
    rooms[room] = ADJUSTABLE_ROOMS.includes(room) ? 1 : 0;
    return rooms;
  }, {});
}

function createPlayerDolls(playerCount) {
  const playerDolls = {};
  for (let player = 1; player <= playerCount; player += 1) {
    playerDolls[player] = INITIAL_PLAYER_DOLLS;
  }
  return playerDolls;
}

function countFace(dice, face) {
  return dice.filter((die) => die === face).length;
}

function countDolls(dice) {
  return dice.reduce((total, die) => total + (DOLL_COUNTS[die] || 0), 0);
}

function rollDice(count, game) {
  return Array.from(
    { length: count },
    () => DIE_FACES[randomInt(game, 0, DIE_FACES.length - 1)],
  );
}

function availableFacesForRoll(roll, usedFaces = []) {
  const used = new Set(usedFaces);
  return [...new Set(roll)].filter((face) => !used.has(face));
}

function roomForTotal(keptTotal) {
  if (keptTotal < 7) return null;
  if (keptTotal >= 11) return 11;
  return keptTotal;
}

function fullestAdjustableRooms(rooms) {
  const mostDolls = Math.max(...ADJUSTABLE_ROOMS.map((room) => rooms[room]));
  return ADJUSTABLE_ROOMS.filter((room) => rooms[room] === mostDolls);
}

function moveExtraDollsToRoomEleven(playerDolls, rooms) {
  if (playerDolls <= INITIAL_PLAYER_DOLLS) {
    return {
      overflow_dolls: 0,
      dolls_remaining: playerDolls,
    };
  }

  const overflowDolls = playerDolls - INITIAL_PLAYER_DOLLS;
  rooms[11] += overflowDolls;
  return {
    overflow_dolls: overflowDolls,
    dolls_remaining: INITIAL_PLAYER_DOLLS,
  };
}

function moveExtraDollsForAllPlayers(playerDolls, rooms) {
  const overflows = {};
  Object.keys(playerDolls)
    .map(Number)
    .sort((left, right) => left - right)
    .forEach((player) => {
      const overflow = moveExtraDollsToRoomEleven(playerDolls[player], rooms);
      playerDolls[player] = overflow.dolls_remaining;
      if (overflow.overflow_dolls > 0) {
        overflows[player] = overflow.overflow_dolls;
      }
    });
  return overflows;
}

function patternChoices(game) {
  const roll = game.current_roll;
  return availableFacesForRoll(roll, game.used_faces)
    .sort((left, right) => {
      const valueDelta = FACE_VALUES[left] - FACE_VALUES[right];
      return valueDelta || left.localeCompare(right);
    })
    .map((face) => {
      const count = countFace(roll, face);
      const adds = FACE_VALUES[face] * count;
      return {
        face,
        count,
        adds,
        projected_total: game.kept_total + adds,
      };
    });
}

function currentTurnResult(game, stopped = false, endedBecauseNoPattern = false) {
  return {
    turns: [...game.turn_rolls],
    kept_dice: [...game.kept_dice],
    kept_total: game.kept_total,
    dolls_rolled: countDolls(game.kept_dice),
    ignored_dice: stopped && !endedBecauseNoPattern ? game.remaining_dice : 0,
    stopped,
    ended_because_no_pattern: endedBecauseNoPattern,
  };
}

function placeDollsForTurn(turnResult, playerDolls, rooms, chosenRoom) {
  let targetRoom = roomForTotal(turnResult.kept_total);
  let tiedRooms = [];
  const dollsRolled = turnResult.dolls_rolled ?? countDolls(turnResult.kept_dice);
  let dollsPlaced = 0;
  let dollsReturned = 0;
  let dollsRemaining = playerDolls;

  if (targetRoom === null) {
    tiedRooms = fullestAdjustableRooms(rooms);
    targetRoom = chosenRoom ?? tiedRooms[0];
    dollsReturned = rooms[targetRoom];
    rooms[targetRoom] = 0;
    dollsRemaining = playerDolls + dollsReturned;
  } else if (targetRoom === 11) {
    dollsPlaced = Math.min(playerDolls, dollsRolled);
    rooms[targetRoom] += dollsPlaced;
    dollsRemaining = playerDolls - dollsPlaced;
  } else {
    const currentRoomDolls = rooms[targetRoom];
    if (dollsRolled >= currentRoomDolls) {
      dollsPlaced = Math.min(playerDolls, dollsRolled - currentRoomDolls);
      rooms[targetRoom] += dollsPlaced;
      dollsRemaining = playerDolls - dollsPlaced;
    } else {
      dollsReturned = currentRoomDolls - dollsRolled;
      rooms[targetRoom] = dollsRolled;
      dollsRemaining = playerDolls + dollsReturned;
    }
  }

  return {
    target_room: targetRoom,
    tied_rooms: tiedRooms,
    dolls_rolled: dollsRolled,
    dolls_placed: dollsPlaced,
    dolls_returned: dollsReturned,
    overflow_dolls: 0,
    dolls_remaining: dollsRemaining,
  };
}

function publicState(game) {
  const availableRecipients = Object.keys(game.player_dolls)
    .map(Number)
    .filter((player) => player !== game.current_player)
    .sort((left, right) => left - right);

  return {
    ...game,
    choices: game.phase === "choose_face" ? patternChoices(game) : [],
    can_stop: game.phase === "stop_check",
    dolls_rolled: countDolls(game.kept_dice),
    available_recipients: availableRecipients,
    turn_history: game.turn_history.slice(-12),
    room_numbers: DOLL_ROOMS,
    adjustable_rooms: ADJUSTABLE_ROOMS,
  };
}

function rollForChoice(game) {
  game.current_roll = rollDice(game.remaining_dice, game);
  const choices = availableFacesForRoll(game.current_roll, game.used_faces);
  if (choices.length === 0) {
    game.turn_rolls.push({
      roll: [...game.current_roll],
      kept_face: null,
      kept_dice: [],
      kept_total: game.kept_total,
      remaining_dice: game.remaining_dice,
      can_stop: game.kept_total >= TARGET_KEPT_TOTAL,
      stopped: true,
      ended_because_no_pattern: true,
    });
    finishTurn(game, true, true);
    return;
  }

  game.phase = "choose_face";
}

function newTurn(game) {
  game.turn_number += 1;
  game.remaining_dice = DEFAULT_DICE_COUNT;
  game.kept_dice = [];
  game.kept_total = 0;
  game.used_faces = [];
  game.turn_rolls = [];
  game.current_roll = [];
  game.pending_placement = null;
  game.pending_turn_result = null;
  game.gift_remaining = 0;
  game.gift_limit = 0;
  game.gift_recipients = {};
  game.tied_rooms = [];
  rollForChoice(game);
}

function chooseFace(game, face) {
  if (game.phase !== "choose_face") {
    throw new Error("It is not time to choose a dice pattern.");
  }
  if (!availableFacesForRoll(game.current_roll, game.used_faces).includes(face)) {
    throw new Error("That pattern is not available.");
  }

  const keptCount = countFace(game.current_roll, face);
  const keptThisTurn = Array.from({ length: keptCount }, () => face);
  game.kept_dice.push(...keptThisTurn);
  game.used_faces.push(face);
  game.kept_total += FACE_VALUES[face] * keptCount;
  game.remaining_dice -= keptCount;
  const canStop = game.kept_total >= TARGET_KEPT_TOTAL;
  const stopped = canStop && game.remaining_dice === 0;
  game.turn_rolls.push({
    roll: [...game.current_roll],
    kept_face: face,
    kept_dice: keptThisTurn,
    kept_total: game.kept_total,
    remaining_dice: game.remaining_dice,
    can_stop: canStop,
    stopped,
    ended_because_no_pattern: false,
  });

  if (game.remaining_dice === 0) {
    finishTurn(game, stopped, false);
  } else if (canStop) {
    game.phase = "stop_check";
  } else {
    rollForChoice(game);
  }
}

function chooseStop(game, stop) {
  if (game.phase !== "stop_check") {
    throw new Error("It is not time to decide whether to stop.");
  }
  if (stop) {
    game.turn_rolls[game.turn_rolls.length - 1].stopped = true;
    finishTurn(game, true, false);
  } else {
    rollForChoice(game);
  }
}

function finishTurn(game, stopped = false, endedBecauseNoPattern = false) {
  const turnResult = currentTurnResult(game, stopped, endedBecauseNoPattern);
  game.pending_turn_result = turnResult;
  const targetRoom = roomForTotal(turnResult.kept_total);

  if (targetRoom === null) {
    const tiedRooms = fullestAdjustableRooms(game.rooms);
    if (tiedRooms.length > 1) {
      game.phase = "choose_room";
      game.tied_rooms = tiedRooms;
      return;
    }
    applyPlacement(game, tiedRooms[0]);
    return;
  }

  applyPlacement(game, targetRoom);
}

function applyPlacement(game, chosenRoom) {
  const currentPlayer = game.current_player;
  const placement = placeDollsForTurn(
    game.pending_turn_result,
    game.player_dolls[currentPlayer],
    game.rooms,
    chosenRoom,
  );
  game.player_dolls[currentPlayer] = placement.dolls_remaining;
  game.pending_placement = placement;
  game.gift_remaining = Math.min(
    countFace(game.pending_turn_result.kept_dice, "1"),
    game.player_dolls[currentPlayer],
  );
  game.gift_limit = game.gift_remaining;
  game.gift_recipients = {};

  if (
    placement.dolls_placed > 0 &&
    game.gift_remaining > 0 &&
    Object.keys(game.player_dolls).length > 1
  ) {
    game.phase = "gift";
  } else {
    completeTurn(game);
  }
}

function chooseRoom(game, room) {
  if (game.phase !== "choose_room") {
    throw new Error("It is not time to choose a room.");
  }
  const selectedRoom = Number(room);
  if (!game.tied_rooms.includes(selectedRoom)) {
    throw new Error("Choose one of the tied fullest rooms.");
  }
  applyPlacement(game, selectedRoom);
}

function chooseGift(game, recipient) {
  if (game.phase !== "gift") {
    throw new Error("It is not time to give dolls.");
  }

  const currentPlayer = game.current_player;
  const selectedRecipient = recipient === null ? null : Number(recipient);
  if (selectedRecipient === null) {
    completeTurn(game);
    return;
  }
  if (
    selectedRecipient === currentPlayer ||
    game.player_dolls[selectedRecipient] === undefined
  ) {
    throw new Error("Choose another player or stop giving.");
  }

  if (game.gift_remaining <= 0 || game.player_dolls[currentPlayer] <= 0) {
    completeTurn(game);
    return;
  }

  game.player_dolls[currentPlayer] -= 1;
  game.player_dolls[selectedRecipient] += 1;
  game.gift_recipients[selectedRecipient] =
    (game.gift_recipients[selectedRecipient] || 0) + 1;
  game.gift_remaining -= 1;

  if (game.gift_remaining <= 0 || game.player_dolls[currentPlayer] <= 0) {
    completeTurn(game);
  }
}

function completeTurn(game) {
  const overflows = moveExtraDollsForAllPlayers(game.player_dolls, game.rooms);
  const giftRecipients = { ...game.gift_recipients };
  const turnRecord = {
    turn_number: game.turn_number,
    player_index: game.current_player,
    starting_dolls: game.starting_dolls,
    turn_result: game.pending_turn_result,
    ...game.pending_placement,
    ones_rolled: countFace(game.pending_turn_result.kept_dice, "1"),
    gifted_dolls: Object.values(giftRecipients).reduce(
      (total, count) => total + count,
      0,
    ),
    gift_recipient:
      Object.keys(giftRecipients).length === 1
        ? Number(Object.keys(giftRecipients)[0])
        : null,
    gift_recipients: giftRecipients,
    overflow_dolls: overflows[game.current_player] || 0,
    overflow_dolls_by_player: overflows,
    dolls_remaining: game.player_dolls[game.current_player],
  };
  game.last_turn = turnRecord;
  game.turn_history.push(turnRecord);
  game.phase = "turn_summary";
}

function nextTurn(game) {
  if (game.phase !== "turn_summary") {
    throw new Error("The current turn is not complete.");
  }
  if (game.winner !== null) {
    game.phase = "game_over";
    return;
  }

  game.current_player += 1;
  if (game.current_player > game.player_count) {
    game.current_player = 1;
  }
  game.starting_dolls = game.player_dolls[game.current_player];
  if (game.starting_dolls === 0) {
    game.winner = game.current_player;
    game.phase = "game_over";
    return;
  }
  newTurn(game);
}

export function createGame({ playerCount = 2, seed = null } = {}) {
  const normalizedPlayerCount = Math.max(1, Number(playerCount) || 2);
  const game = {
    id: createGameId(),
    player_count: normalizedPlayerCount,
    seed: seed === "" ? null : seed,
    rng_state: normalizeSeed(seed),
    rooms: createDollRooms(),
    player_dolls: createPlayerDolls(normalizedPlayerCount),
    current_player: 1,
    turn_number: 0,
    phase: "setup",
    winner: null,
    turn_history: [],
    last_turn: null,
    starting_dolls: INITIAL_PLAYER_DOLLS,
    remaining_dice: 0,
    kept_dice: [],
    kept_total: 0,
    used_faces: [],
    turn_rolls: [],
    current_roll: [],
    pending_placement: null,
    pending_turn_result: null,
    gift_remaining: 0,
    gift_limit: 0,
    gift_recipients: {},
    tied_rooms: [],
  };
  game.starting_dolls = game.player_dolls[game.current_player];
  newTurn(game);
  return publicState(game);
}

export function applyGameAction(game, request) {
  const nextGame = cloneGame(game);
  if (request.action === "choose_face") {
    chooseFace(nextGame, request.face);
  } else if (request.action === "stop") {
    chooseStop(nextGame, Boolean(request.stop));
  } else if (request.action === "choose_room") {
    chooseRoom(nextGame, request.room);
  } else if (request.action === "gift") {
    chooseGift(nextGame, request.recipient ?? null);
  } else if (request.action === "next_turn") {
    nextTurn(nextGame);
  } else {
    throw new Error("Unknown action.");
  }
  return publicState(nextGame);
}

export function getFaceNames() {
  return DIE_FACES;
}
