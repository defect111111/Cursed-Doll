from dice import count_dolls
from player_turn import (
    choose_face_to_keep,
    format_rolls,
    roll_until_done,
    should_stop_automatically,
)


INITIAL_PLAYER_DOLLS = 10
DOLL_ROOMS = (7, 8, 9, 10, 11)


def create_doll_rooms():
    return {room_number: 0 for room_number in DOLL_ROOMS}


def create_player_dolls(player_count):
    return {
        player_index: INITIAL_PLAYER_DOLLS
        for player_index in range(1, player_count + 1)
    }


def room_for_total(kept_total):
    if kept_total < 7:
        return None
    if kept_total >= 11:
        return 11
    return kept_total


def place_dolls_for_turn(turn_result, player_dolls, rooms):
    target_room = room_for_total(turn_result["kept_total"])
    dolls_rolled = turn_result.get("dolls_rolled", count_dolls(turn_result["kept_dice"]))
    dolls_to_place = 0 if target_room is None else min(player_dolls, dolls_rolled)

    if target_room is not None:
        rooms[target_room] += dolls_to_place

    return {
        "target_room": target_room,
        "dolls_rolled": dolls_rolled,
        "dolls_placed": dolls_to_place,
        "dolls_remaining": player_dolls - dolls_to_place,
    }


def play_game_turns_for_players(
    player_count,
    rng=None,
    choose_face=choose_face_to_keep,
    should_stop=should_stop_automatically,
):
    if player_count < 1:
        raise ValueError("player_count must be at least 1")

    rooms = create_doll_rooms()
    player_dolls = create_player_dolls(player_count)
    players = []

    for player_index in range(1, player_count + 1):
        turn_result = roll_until_done(
            rng=rng,
            choose_face=choose_face,
            should_stop=should_stop,
            player_index=player_index,
            player_dolls=dict(player_dolls),
            rooms=rooms,
        )
        placement = place_dolls_for_turn(turn_result, player_dolls[player_index], rooms)
        player_dolls[player_index] = placement["dolls_remaining"]
        players.append(
            {
                "turn_number": player_index,
                "player_index": player_index,
                "starting_dolls": INITIAL_PLAYER_DOLLS,
                "turn_result": turn_result,
                **placement,
            }
        )

    return {
        "rooms": rooms,
        "player_dolls": player_dolls,
        "players": players,
        "winner": None,
    }


def play_game(
    player_count,
    rng=None,
    choose_face=choose_face_to_keep,
    should_stop=should_stop_automatically,
):
    if player_count < 1:
        raise ValueError("player_count must be at least 1")

    rooms = create_doll_rooms()
    player_dolls = create_player_dolls(player_count)
    turns = []
    winner = None
    turn_number = 0

    while winner is None:
        for player_index in range(1, player_count + 1):
            turn_number += 1
            turn_result = roll_until_done(
                rng=rng,
                choose_face=choose_face,
                should_stop=should_stop,
                player_index=player_index,
                player_dolls=dict(player_dolls),
                rooms=rooms,
            )
            placement = place_dolls_for_turn(turn_result, player_dolls[player_index], rooms)
            player_dolls[player_index] = placement["dolls_remaining"]
            turn_record = {
                "turn_number": turn_number,
                "player_index": player_index,
                "starting_dolls": player_dolls[player_index] + placement["dolls_placed"],
                "turn_result": turn_result,
                **placement,
            }
            turns.append(turn_record)

            if player_dolls[player_index] == 0:
                winner = player_index
                break

    return {
        "rooms": rooms,
        "player_dolls": player_dolls,
        "turns": turns,
        "winner": winner,
    }


def format_game_result(game_result):
    turn_records = game_result["turns"] if "turns" in game_result else game_result["players"]
    turn_results = [turn["turn_result"] for turn in turn_records]
    labels = [
        f"Turn {turn.get('turn_number', index)} - Player {turn['player_index']}"
        for index, turn in enumerate(turn_records, start=1)
    ]
    lines = [format_rolls(turn_results, labels=labels), ""]
    if game_result["winner"] is not None:
        lines.append("=" * 56)
        lines.append(f"Winner: Player {game_result['winner']}")
        lines.append("-" * 56)
        lines.append("The game ended because that player has no dolls left.")
        lines.append("")

    lines.append("=" * 56)
    lines.append("Doll rooms")
    lines.append("-" * 56)
    for room_number in DOLL_ROOMS:
        lines.append(f"Room {room_number}: {game_result['rooms'][room_number]} dolls")

    lines.append("")
    lines.append("=" * 56)
    lines.append("Doll placement")
    lines.append("-" * 56)
    for turn in turn_records:
        room = turn["target_room"]
        room_label = f"room {room}" if room is not None else "no room"
        lines.append(
            f"Turn {turn.get('turn_number', '?')} - Player {turn['player_index']}: "
            f"rolled {turn['dolls_rolled']} dolls, "
            f"placed {turn['dolls_placed']} in {room_label}, "
            f"{turn['dolls_remaining']} dolls left"
        )

    return "\n".join(lines)
