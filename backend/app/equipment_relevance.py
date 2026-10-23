"""UX recommendations only; never electrical restrictions or demand classes."""

ROOMS = (
    "living",
    "bedroom",
    "kitchen",
    "bathroom",
    "laundry",
    "garage",
    "corridor",
    "outdoor",
    "office",
    "other",
)
BY_TYPE = {
    "lighting": ROOMS,
    "television": ("living", "bedroom", "office", "other"),
    "air_conditioner": ("living", "bedroom", "office", "other"),
    "shower": ("bathroom", "other"),
    "microwave": ("kitchen", "other"),
    "refrigeration": ("kitchen", "garage", "other"),
    "motor": ("garage", "outdoor", "other"),
    "custom": ROOMS,
}
BY_CATEGORY = {
    "Cozinha": ("kitchen", "other"),
    "Lavanderia": ("laundry", "other"),
    "Climatização": ("living", "bedroom", "office", "other"),
}
BY_ID = {
    "enel-hairdryer-small": ("bathroom", "other"),
    "enel-wall-exhaust": ("bathroom", "kitchen", "laundry", "garage", "other"),
    "enel-phone-charger": ("living", "bedroom", "office", "kitchen", "other"),
    "enel-audio": ("living", "bedroom", "other"),
    "enel-computer": ("living", "bedroom", "office", "other"),
    "loren-easy-220": ("kitchen", "laundry", "other"),
    "versatil-220": ("bathroom", "kitchen", "laundry", "other"),
}


def recommended_rooms(item):
    return list(
        BY_ID.get(
            item["id"],
            BY_TYPE.get(item["equipment_type"], BY_CATEGORY.get(item["category"], ("other",))),
        )
    )
