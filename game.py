from dice import count_dolls
from player_turn import (
    DIVIDER,
    HEADER_DIVIDER,
    choose_face_to_keep,
    format_rolls,
    output_game_state,
    roll_until_done,
    should_stop_automatically,
)


INITIAL_PLAYER_DOLLS = 10
DOLL_ROOMS = (7, 8, 9, 10, 11)
ADJUSTABLE_ROOMS = (7, 8, 9, 10)


def create_doll_rooms():
    return {
        room_number: 1 if room_number in ADJUSTABLE_ROOMS else 0
        for room_number in DOLL_ROOMS
    }


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


def fullest_adjustable_room(rooms):
    return min(
        ADJUSTABLE_ROOMS,
        key=lambda room_number: (-rooms[room_number], room_number),
    )


def fullest_adjustable_rooms(rooms):
    most_dolls = max(rooms[room_number] for room_number in ADJUSTABLE_ROOMS)
    return [
        room_number
        for room_number in ADJUSTABLE_ROOMS
        if rooms[room_number] == most_dolls
    ]


def choose_room_to_take_automatically(tied_rooms, **_context):
    return min(tied_rooms)


def choose_room_interactively(
    tied_rooms,
    player_index=None,
    turn_result=None,
    player_dolls=None,
    rooms=None,
    input_fn=input,
    output_fn=print,
):
    output_fn("")
    output_fn(HEADER_DIVIDER)
    if player_index is not None:
        output_fn(f"Player {player_index} - choose a room")
    else:
        output_fn("Choose a room")
    output_fn(DIVIDER)
    output_game_state(player_dolls, rooms, output_fn)
    if turn_result is not None:
        output_fn(f"Kept total: {turn_result['kept_total']}")
        output_fn("Total is 6 or less. Take all dolls from one fullest room.")
    output_fn(DIVIDER)
    output_fn("Tied fullest rooms:")

    choice_labels = [chr(ord("a") + index) for index in range(len(tied_rooms))]
    for label, room_number in zip(choice_labels, tied_rooms):
        output_fn(f"  [{label}] Room {room_number}: {rooms[room_number]} dolls")

    while True:
        raw_choice = input_fn("Room > ").strip().lower()
        if raw_choice in choice_labels:
            return tied_rooms[choice_labels.index(raw_choice)]
        for room_number in tied_rooms:
            if raw_choice == str(room_number):
                return room_number

        output_fn("Please enter a listed letter or room number.")


def move_extra_dolls_to_room_eleven(player_dolls, rooms):
    if player_dolls <= INITIAL_PLAYER_DOLLS:
        return {
            "overflow_dolls": 0,
            "dolls_remaining": player_dolls,
        }

    overflow_dolls = player_dolls - INITIAL_PLAYER_DOLLS
    rooms[11] += overflow_dolls
    return {
        "overflow_dolls": overflow_dolls,
        "dolls_remaining": INITIAL_PLAYER_DOLLS,
    }


def move_extra_dolls_for_all_players(player_dolls, rooms):
    overflows = {}
    for player_index in sorted(player_dolls):
        overflow = move_extra_dolls_to_room_eleven(player_dolls[player_index], rooms)
        player_dolls[player_index] = overflow["dolls_remaining"]
        if overflow["overflow_dolls"]:
            overflows[player_index] = overflow["overflow_dolls"]
    return overflows


def choose_default_gift_recipient(player_index, player_count):
    if player_count <= 1:
        return None
    if player_index == player_count:
        return 1
    return player_index + 1


def choose_gift_recipient_automatically(available_recipients, player_index=None, **context):
    player_dolls = context.get("player_dolls", {})
    player_count = len(player_dolls)
    recipient = choose_default_gift_recipient(player_index, player_count)
    if recipient in available_recipients:
        return recipient
    return available_recipients[0] if available_recipients else None


def choose_gift_recipient_interactively(
    available_recipients,
    gift_number,
    gift_limit,
    player_index=None,
    turn_result=None,
    player_dolls=None,
    rooms=None,
    input_fn=input,
    output_fn=print,
):
    output_fn("")
    output_fn(HEADER_DIVIDER)
    if player_index is not None:
        output_fn(f"Player {player_index} - give a doll")
    else:
        output_fn("Give a doll")
    output_fn(DIVIDER)
    output_game_state(player_dolls, rooms, output_fn)
    if turn_result is not None:
        output_fn(f"Kept ones : {turn_result['kept_dice'].count('1')}")
        output_fn(f"Gift      : {gift_number} of {gift_limit}")
    output_fn("Giving is optional. Choose a player or stop giving.")
    output_fn(DIVIDER)
    output_fn("Available choices:")

    choices = [None, *available_recipients]
    choice_labels = [chr(ord("a") + index) for index in range(len(choices))]
    for label, choice in zip(choice_labels, choices):
        if choice is None:
            output_fn(f"  [{label}] Stop giving")
        else:
            output_fn(f"  [{label}] Player {choice}")

    while True:
        raw_choice = input_fn("Gift doll > ").strip().lower()
        if raw_choice in choice_labels:
            return choices[choice_labels.index(raw_choice)]
        for recipient in available_recipients:
            if raw_choice == str(recipient):
                return recipient
        if raw_choice in ("n", "no", "skip", "stop"):
            return None

        output_fn("Please enter a listed letter, player number, or stop.")


def give_dolls_for_ones(
    turn_result,
    player_index,
    player_dolls,
    dolls_placed,
    recipient_index=None,
    choose_gift_recipient=None,
    rooms=None,
):
    ones_rolled = turn_result["kept_dice"].count("1")
    if dolls_placed <= 0 or ones_rolled == 0 or len(player_dolls) <= 1:
        return {
            "ones_rolled": ones_rolled,
            "gifted_dolls": 0,
            "gift_recipient": None,
            "gift_recipients": {},
        }

    gift_limit = min(ones_rolled, player_dolls[player_index])
    available_recipients = [
        recipient
        for recipient in sorted(player_dolls)
        if recipient != player_index
    ]
    gift_recipients = {}

    if choose_gift_recipient is None:
        if recipient_index is None:
            recipient_index = choose_default_gift_recipient(player_index, len(player_dolls))
        if recipient_index not in available_recipients:
            recipient_index = None

        if recipient_index is not None:
            gifted_dolls = gift_limit
            player_dolls[player_index] -= gifted_dolls
            player_dolls[recipient_index] += gifted_dolls
            gift_recipients[recipient_index] = gifted_dolls
    else:
        for gift_number in range(1, gift_limit + 1):
            recipient_index = choose_gift_recipient(
                available_recipients,
                gift_number=gift_number,
                gift_limit=gift_limit,
                player_index=player_index,
                turn_result=turn_result,
                player_dolls=dict(player_dolls),
                rooms=rooms,
            )
            if recipient_index is None:
                break
            if recipient_index not in available_recipients:
                continue

            player_dolls[player_index] -= 1
            player_dolls[recipient_index] += 1
            gift_recipients[recipient_index] = gift_recipients.get(recipient_index, 0) + 1
            if player_dolls[player_index] == 0:
                break

    gifted_dolls = sum(gift_recipients.values())
    gift_recipient = None
    if len(gift_recipients) == 1:
        gift_recipient = next(iter(gift_recipients))
    return {
        "ones_rolled": ones_rolled,
        "gifted_dolls": gifted_dolls,
        "gift_recipient": gift_recipient,
        "gift_recipients": gift_recipients,
    }


def place_dolls_for_turn(
    turn_result,
    player_dolls,
    rooms,
    apply_overflow=True,
    choose_room=choose_room_to_take_automatically,
    player_index=None,
    player_dolls_by_player=None,
):
    target_room = room_for_total(turn_result["kept_total"])
    dolls_rolled = turn_result.get("dolls_rolled", count_dolls(turn_result["kept_dice"]))
    dolls_placed = 0
    dolls_returned = 0

    if target_room is None:
        tied_rooms = fullest_adjustable_rooms(rooms)
        if len(tied_rooms) == 1:
            target_room = tied_rooms[0]
        else:
            target_room = choose_room(
                tied_rooms,
                player_index=player_index,
                turn_result=turn_result,
                player_dolls=player_dolls_by_player,
                rooms=rooms,
            )
        dolls_returned = rooms[target_room]
        rooms[target_room] = 0
        dolls_remaining = player_dolls + dolls_returned
    elif target_room == 11:
        dolls_placed = min(player_dolls, dolls_rolled)
        rooms[target_room] += dolls_placed
        dolls_remaining = player_dolls - dolls_placed
    else:
        current_room_dolls = rooms[target_room]
        if dolls_rolled >= current_room_dolls:
            dolls_placed = min(player_dolls, dolls_rolled - current_room_dolls)
            rooms[target_room] += dolls_placed
            dolls_remaining = player_dolls - dolls_placed
        else:
            dolls_returned = current_room_dolls - dolls_rolled
            rooms[target_room] = dolls_rolled
            dolls_remaining = player_dolls + dolls_returned

    overflow_dolls = 0
    if apply_overflow:
        overflow = move_extra_dolls_to_room_eleven(dolls_remaining, rooms)
        overflow_dolls = overflow["overflow_dolls"]
        dolls_remaining = overflow["dolls_remaining"]

    return {
        "target_room": target_room,
        "tied_rooms": tuple(tied_rooms) if room_for_total(turn_result["kept_total"]) is None else (),
        "dolls_rolled": dolls_rolled,
        "dolls_placed": dolls_placed,
        "dolls_returned": dolls_returned,
        "overflow_dolls": overflow_dolls,
        "dolls_remaining": dolls_remaining,
    }


def resolve_turn_effects(
    player_index,
    turn_result,
    player_dolls,
    rooms,
    choose_room=choose_room_to_take_automatically,
    choose_gift_recipient=None,
):
    placement = place_dolls_for_turn(
        turn_result,
        player_dolls[player_index],
        rooms,
        apply_overflow=False,
        choose_room=choose_room,
        player_index=player_index,
        player_dolls_by_player=dict(player_dolls),
    )
    player_dolls[player_index] = placement["dolls_remaining"]

    gift = give_dolls_for_ones(
        turn_result,
        player_index,
        player_dolls,
        placement["dolls_placed"],
        choose_gift_recipient=choose_gift_recipient,
        rooms=rooms,
    )
    overflows = move_extra_dolls_for_all_players(player_dolls, rooms)

    return {
        **placement,
        **gift,
        "overflow_dolls": overflows.get(player_index, 0),
        "overflow_dolls_by_player": overflows,
        "dolls_remaining": player_dolls[player_index],
    }


def play_game_turns_for_players(
    player_count,
    rng=None,
    choose_face=choose_face_to_keep,
    should_stop=should_stop_automatically,
    choose_room=choose_room_to_take_automatically,
    choose_gift_recipient=None,
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
        placement = resolve_turn_effects(
            player_index,
            turn_result,
            player_dolls,
            rooms,
            choose_room=choose_room,
            choose_gift_recipient=choose_gift_recipient,
        )
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
    choose_room=choose_room_to_take_automatically,
    choose_gift_recipient=None,
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
            starting_dolls = player_dolls[player_index]
            placement = resolve_turn_effects(
                player_index,
                turn_result,
                player_dolls,
                rooms,
                choose_room=choose_room,
                choose_gift_recipient=choose_gift_recipient,
            )
            turn_record = {
                "turn_number": turn_number,
                "player_index": player_index,
                "starting_dolls": starting_dolls,
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
        if turn.get("gifted_dolls", 0) == 0:
            gift_label = "gifted 0"
        else:
            gift_label = f"gifted {format_gift_summary(turn.get('gift_recipients', {}))}"
        overflow_label = format_overflow_summary(turn.get("overflow_dolls_by_player", {}))
        lines.append(
            f"Turn {turn.get('turn_number', '?')} - Player {turn['player_index']}: "
            f"rolled {turn['dolls_rolled']} dolls, "
            f"kept {turn.get('ones_rolled', 0)} ones, "
            f"placed {turn['dolls_placed']} in {room_label}, "
            f"got back {turn.get('dolls_returned', 0)}, "
            f"{gift_label}, "
            f"overflowed {overflow_label} to room 11, "
            f"{turn['dolls_remaining']} dolls left"
        )

    return "\n".join(lines)


def format_overflow_summary(overflows):
    if not overflows:
        return "0"
    return ", ".join(
        f"Player {player_index}: {dolls}"
        for player_index, dolls in sorted(overflows.items())
    )


def format_gift_summary(gift_recipients):
    return ", ".join(
        f"{dolls} to Player {player_index}"
        for player_index, dolls in sorted(gift_recipients.items())
    )
