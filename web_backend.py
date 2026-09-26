from collections import Counter
import random
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dice import (
    DEFAULT_DICE_COUNT,
    FACE_VALUES,
    TARGET_KEPT_TOTAL,
    available_faces_for_roll,
    count_dolls,
    roll_dice,
)
from game import (
    ADJUSTABLE_ROOMS,
    DOLL_ROOMS,
    create_doll_rooms,
    create_player_dolls,
    fullest_adjustable_rooms,
    move_extra_dolls_for_all_players,
    place_dolls_for_turn,
    room_for_total,
)


app = FastAPI(title="Cursed Doll API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GAMES = {}


class NewGameRequest(BaseModel):
    player_count: int = 2
    seed: int | None = None


class ActionRequest(BaseModel):
    action: str
    face: str | None = None
    stop: bool | None = None
    room: int | None = None
    recipient: int | None = None


def new_turn(game):
    game["turn_number"] += 1
    game["remaining_dice"] = DEFAULT_DICE_COUNT
    game["kept_dice"] = []
    game["kept_total"] = 0
    game["used_faces"] = []
    game["turn_rolls"] = []
    game["current_roll"] = []
    game["pending_placement"] = None
    game["gift_remaining"] = 0
    game["gift_limit"] = 0
    game["gift_recipients"] = {}
    roll_for_choice(game)


def roll_for_choice(game):
    game["current_roll"] = roll_dice(game["remaining_dice"], game["rng"])
    choices = available_faces_for_roll(game["current_roll"], game["used_faces"])
    if not choices:
        game["turn_rolls"].append(
            {
                "roll": list(game["current_roll"]),
                "kept_face": None,
                "kept_dice": [],
                "kept_total": game["kept_total"],
                "remaining_dice": game["remaining_dice"],
                "can_stop": game["kept_total"] >= TARGET_KEPT_TOTAL,
                "stopped": True,
                "ended_because_no_pattern": True,
            }
        )
        finish_turn(game, stopped=True, ended_because_no_pattern=True)
        return

    game["phase"] = "choose_face"


def pattern_choices(game):
    roll = game["current_roll"]
    counts = Counter(roll)
    faces = sorted(
        available_faces_for_roll(roll, game["used_faces"]),
        key=lambda face: (FACE_VALUES[face], face),
    )
    return [
        {
            "face": face,
            "count": counts[face],
            "adds": FACE_VALUES[face] * counts[face],
            "projected_total": game["kept_total"] + FACE_VALUES[face] * counts[face],
        }
        for face in faces
    ]


def choose_face(game, face):
    if game["phase"] != "choose_face":
        raise HTTPException(400, "It is not time to choose a dice pattern.")
    if face not in available_faces_for_roll(game["current_roll"], game["used_faces"]):
        raise HTTPException(400, "That pattern is not available.")

    kept_count = game["current_roll"].count(face)
    kept_this_turn = [face] * kept_count
    game["kept_dice"].extend(kept_this_turn)
    game["used_faces"].append(face)
    game["kept_total"] += FACE_VALUES[face] * kept_count
    game["remaining_dice"] -= kept_count
    can_stop = game["kept_total"] >= TARGET_KEPT_TOTAL
    stopped = can_stop and game["remaining_dice"] == 0
    game["turn_rolls"].append(
        {
            "roll": list(game["current_roll"]),
            "kept_face": face,
            "kept_dice": kept_this_turn,
            "kept_total": game["kept_total"],
            "remaining_dice": game["remaining_dice"],
            "can_stop": can_stop,
            "stopped": stopped,
            "ended_because_no_pattern": False,
        }
    )

    if game["remaining_dice"] == 0:
        finish_turn(game, stopped=stopped, ended_because_no_pattern=False)
    elif can_stop:
        game["phase"] = "stop_check"
    else:
        roll_for_choice(game)


def choose_stop(game, stop):
    if game["phase"] != "stop_check":
        raise HTTPException(400, "It is not time to decide whether to stop.")
    if stop:
        game["turn_rolls"][-1]["stopped"] = True
        finish_turn(game, stopped=True, ended_because_no_pattern=False)
    else:
        roll_for_choice(game)


def current_turn_result(game, stopped=False, ended_because_no_pattern=False):
    return {
        "turns": list(game["turn_rolls"]),
        "kept_dice": list(game["kept_dice"]),
        "kept_total": game["kept_total"],
        "dolls_rolled": count_dolls(game["kept_dice"]),
        "ignored_dice": (
            game["remaining_dice"]
            if stopped and not ended_because_no_pattern
            else 0
        ),
        "stopped": stopped,
        "ended_because_no_pattern": ended_because_no_pattern,
    }


def finish_turn(game, stopped=False, ended_because_no_pattern=False):
    turn_result = current_turn_result(
        game,
        stopped=stopped,
        ended_because_no_pattern=ended_because_no_pattern,
    )
    game["pending_turn_result"] = turn_result
    target_room = room_for_total(turn_result["kept_total"])

    if target_room is None:
        tied_rooms = fullest_adjustable_rooms(game["rooms"])
        if len(tied_rooms) > 1:
            game["phase"] = "choose_room"
            game["tied_rooms"] = tied_rooms
            return

    apply_placement(game, target_room if target_room is not None else tied_rooms[0])


def apply_placement(game, chosen_room):
    turn_result = game["pending_turn_result"]

    def choose_room(_tied_rooms, **_context):
        return chosen_room

    placement = place_dolls_for_turn(
        turn_result,
        game["player_dolls"][game["current_player"]],
        game["rooms"],
        apply_overflow=False,
        choose_room=choose_room,
        player_index=game["current_player"],
        player_dolls_by_player=dict(game["player_dolls"]),
    )
    game["player_dolls"][game["current_player"]] = placement["dolls_remaining"]
    game["pending_placement"] = placement
    game["gift_remaining"] = min(
        turn_result["kept_dice"].count("1"),
        game["player_dolls"][game["current_player"]],
    )
    game["gift_limit"] = game["gift_remaining"]
    game["gift_recipients"] = {}

    if (
        placement["dolls_placed"] > 0
        and game["gift_remaining"] > 0
        and len(game["player_dolls"]) > 1
    ):
        game["phase"] = "gift"
    else:
        complete_turn(game)


def choose_room(game, room):
    if game["phase"] != "choose_room":
        raise HTTPException(400, "It is not time to choose a room.")
    if room not in game["tied_rooms"]:
        raise HTTPException(400, "Choose one of the tied fullest rooms.")
    apply_placement(game, room)


def choose_gift(game, recipient):
    if game["phase"] != "gift":
        raise HTTPException(400, "It is not time to give dolls.")
    current_player = game["current_player"]

    if recipient is None:
        complete_turn(game)
        return
    if recipient == current_player or recipient not in game["player_dolls"]:
        raise HTTPException(400, "Choose another player or stop giving.")

    if game["gift_remaining"] <= 0 or game["player_dolls"][current_player] <= 0:
        complete_turn(game)
        return

    game["player_dolls"][current_player] -= 1
    game["player_dolls"][recipient] += 1
    game["gift_recipients"][recipient] = game["gift_recipients"].get(recipient, 0) + 1
    game["gift_remaining"] -= 1

    if game["gift_remaining"] <= 0 or game["player_dolls"][current_player] <= 0:
        complete_turn(game)


def complete_turn(game):
    overflows = move_extra_dolls_for_all_players(game["player_dolls"], game["rooms"])
    placement = dict(game["pending_placement"])
    gift_recipients = dict(game["gift_recipients"])
    turn_record = {
        "turn_number": game["turn_number"],
        "player_index": game["current_player"],
        "starting_dolls": game["starting_dolls"],
        "turn_result": game["pending_turn_result"],
        **placement,
        "ones_rolled": game["pending_turn_result"]["kept_dice"].count("1"),
        "gifted_dolls": sum(gift_recipients.values()),
        "gift_recipient": (
            next(iter(gift_recipients)) if len(gift_recipients) == 1 else None
        ),
        "gift_recipients": gift_recipients,
        "overflow_dolls": overflows.get(game["current_player"], 0),
        "overflow_dolls_by_player": overflows,
        "dolls_remaining": game["player_dolls"][game["current_player"]],
    }
    game["last_turn"] = turn_record
    game["turn_history"].append(turn_record)

    if game["player_dolls"][game["current_player"]] == 0:
        game["winner"] = game["current_player"]
        game["phase"] = "game_over"
        return

    game["phase"] = "turn_summary"


def next_turn(game):
    if game["phase"] != "turn_summary":
        raise HTTPException(400, "The current turn is not complete.")
    if game["winner"] is not None:
        game["phase"] = "game_over"
        return

    game["current_player"] += 1
    if game["current_player"] > game["player_count"]:
        game["current_player"] = 1
    game["starting_dolls"] = game["player_dolls"][game["current_player"]]
    new_turn(game)


def public_state(game):
    available_recipients = [
        player
        for player in sorted(game["player_dolls"])
        if player != game["current_player"]
    ]
    return {
        "id": game["id"],
        "player_count": game["player_count"],
        "current_player": game["current_player"],
        "turn_number": game["turn_number"],
        "phase": game["phase"],
        "rooms": game["rooms"],
        "player_dolls": game["player_dolls"],
        "winner": game["winner"],
        "roll": game["current_roll"],
        "choices": pattern_choices(game) if game["phase"] == "choose_face" else [],
        "remaining_dice": game["remaining_dice"],
        "kept_dice": game["kept_dice"],
        "kept_total": game["kept_total"],
        "dolls_rolled": count_dolls(game["kept_dice"]),
        "used_faces": game["used_faces"],
        "can_stop": game["phase"] == "stop_check",
        "tied_rooms": game.get("tied_rooms", []),
        "gift_remaining": game["gift_remaining"],
        "gift_limit": game["gift_limit"],
        "gift_recipients": game["gift_recipients"],
        "available_recipients": available_recipients,
        "turn_rolls": game["turn_rolls"],
        "last_turn": game["last_turn"],
        "turn_history": game["turn_history"][-12:],
        "room_numbers": list(DOLL_ROOMS),
        "adjustable_rooms": list(ADJUSTABLE_ROOMS),
    }


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/")
def root():
    return {
        "name": "Cursed Doll API",
        "health": "/api/health",
        "docs": "/docs",
    }


@app.post("/api/games")
def create_game(request: NewGameRequest):
    if request.player_count < 1:
        raise HTTPException(400, "player_count must be at least 1")

    game_id = str(uuid4())
    game = {
        "id": game_id,
        "player_count": request.player_count,
        "rng": random.Random(request.seed) if request.seed is not None else random.Random(),
        "rooms": create_doll_rooms(),
        "player_dolls": create_player_dolls(request.player_count),
        "current_player": 1,
        "turn_number": 0,
        "phase": "setup",
        "winner": None,
        "turn_history": [],
        "last_turn": None,
        "starting_dolls": 10,
    }
    GAMES[game_id] = game
    game["starting_dolls"] = game["player_dolls"][game["current_player"]]
    new_turn(game)
    return public_state(game)


@app.get("/api/games/{game_id}")
def get_game(game_id: str):
    return public_state(require_game(game_id))


@app.post("/api/games/{game_id}/actions")
def apply_action(game_id: str, request: ActionRequest):
    game = require_game(game_id)
    if request.action == "choose_face":
        choose_face(game, request.face)
    elif request.action == "stop":
        choose_stop(game, bool(request.stop))
    elif request.action == "choose_room":
        choose_room(game, request.room)
    elif request.action == "gift":
        choose_gift(game, request.recipient)
    elif request.action == "next_turn":
        next_turn(game)
    else:
        raise HTTPException(400, "Unknown action.")
    return public_state(game)


def require_game(game_id):
    if game_id not in GAMES:
        raise HTTPException(404, "Game not found.")
    return GAMES[game_id]
