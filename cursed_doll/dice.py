from collections import Counter


DEFAULT_DICE_COUNT = 6
TARGET_KEPT_TOTAL = 7
DIE_FACES = (
    ("1", 1),
    ("2", 2),
    ("3", 3),
    ("4", 4),
    ("one doll", 0),
    ("two dolls", 0),
)
FACE_VALUES = dict(DIE_FACES)
DOLL_COUNTS = {
    "one doll": 1,
    "two dolls": 2,
}


def validate_dice_settings(dice_count):
    if dice_count < 1:
        raise ValueError("dice_count must be at least 1")


def available_faces_for_roll(roll, used_faces=None):
    if not roll:
        raise ValueError("roll must include at least one die")

    used_faces = set(used_faces or [])
    return [face for face in Counter(roll) if face not in used_faces]


def roll_dice(dice_count, rng):
    return [DIE_FACES[rng.randint(1, len(DIE_FACES)) - 1][0] for _ in range(dice_count)]


def format_dice(dice):
    return ", ".join(str(value) for value in dice)


def count_dolls(dice):
    return sum(DOLL_COUNTS.get(face, 0) for face in dice)
