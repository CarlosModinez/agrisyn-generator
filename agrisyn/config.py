"""Central configuration: ground planes, camera optics, leaf catalogue and plant distribution.

Everything that depends on the content of the Blender file (object and collection
names) lives here. Leaf names are generated programmatically from the naming
pattern used in `blender/agrisyn.blend`.
"""

# --- Ground ------------------------------------------------------------------

# Collection of the .blend that holds one ready-made ground plane per soil
# texture (material, displacement and dimensions already set).
GROUND_COLLECTION = "ground"

# Object names inside GROUND_COLLECTION. Scene i uses SOIL_MATERIALS[i % len].
SOIL_MATERIALS = [
    "brown_mud_dry_disp_4k",
    "coast_sand_02_diff_4k",
    "forest_ground_04_diff_4k",
    "forest_ground_05_diff_4k.jpg",
    "forest_ground_06_diff_4k",
    "gravelly_sand_diff_4k",
    "red_laterite_soil_stones_diff_4k",
    "red_mud_stones_diff_4k",
    "rocks_ground_02_col_4k",
    "sandy_gravel_02_diff_4k",
]

# --- Camera ------------------------------------------------------------------

# Nadir camera. The footprint on the ground follows from the optics:
# width = height * sensor / lens (13.3 x 9.5 cm). The scene is a ~1:4.8 scale
# model of the WE3DS acquisition geometry (camera ~90 cm above the ground).
CAMERA = {
    "height": 0.185,        # metres above the ground
    "lens_mm": 50.0,
    "sensor_mm": 36.0,
    "resolution_x": 1600,
    "resolution_y": 1144,
}

# --- Render ------------------------------------------------------------------

RENDER = {
    "samples": 64,          # Cycles samples for the RGB image
    "mask_samples": 1,      # flat emission materials: one sample is enough
}

# --- Leaf catalogue ----------------------------------------------------------

# Every species has a collection in the .blend named after it, holding the leaf
# objects listed below. The sunflower library is split into size categories.
SUNFLOWER_TOTALS = {"big": 12, "medium": 18, "small": 20}


def _leaf_names(prefix: str, count: int, pad: int = 3, start: int = 0) -> list:
    return [f"{prefix}_{i:0{pad}d}" for i in range(start, start + count)]


LEAVES = {
    "sunflower": {
        "big": _leaf_names("sunflower_big", SUNFLOWER_TOTALS["big"], pad=2, start=1),
        "medium": _leaf_names("sunflower_medium", SUNFLOWER_TOTALS["medium"], pad=2, start=1),
        "small": _leaf_names("sunflower_small", SUNFLOWER_TOTALS["small"], pad=2, start=1),
    },
    "corn": {"all": _leaf_names("corn", 49, pad=1, start=1)},
    "milk_thistle": {"all": _leaf_names("milk_thistle", 50)},
    "common_buckwheat": {"all": _leaf_names("common_buckwheat", 50)},
}

SPECIES = list(LEAVES)
MAX_LEAF_COUNT = 50

# --- Plant distribution --------------------------------------------------------

# Calibrated on the WE3DS training split (the test split is never used):
#   n_plants: weights of 1, 2, 3, ... plants per image, from the histogram of
#             connected components (> 0.05 % of the image) in the real masks;
#   scale:    (min, max) of a uniform scale factor applied PER PLANT, drawn in
#             log space, tuned so that the plant area in the mask (10th-90th
#             percentiles) approaches the real one.
PLANT_DISTRIBUTION = {
    "sunflower":        {"n_plants": [61, 28, 10, 1],    "scale": (0.30, 2.00)},
    "corn":             {"n_plants": [68, 28, 3, 1],     "scale": (0.33, 1.90)},
    "milk_thistle":     {"n_plants": [45, 32, 17, 4, 2], "scale": (0.63, 2.33)},
    "common_buckwheat": {"n_plants": [44, 32, 16, 6, 1], "scale": (0.26, 1.49)},
}


# --- Helpers -----------------------------------------------------------------

def camera_footprint() -> tuple:
    """(width, height) in metres of the ground area seen by the camera."""
    width = CAMERA["height"] * CAMERA["sensor_mm"] / CAMERA["lens_mm"]
    height = width * CAMERA["resolution_y"] / CAMERA["resolution_x"]
    return width, height


def _sunflower_size_counts(leaf_count: int) -> dict:
    """Splits `leaf_count` proportionally between the sunflower size categories."""
    total = sum(SUNFLOWER_TOTALS.values())
    big = min(SUNFLOWER_TOTALS["big"], round(leaf_count * SUNFLOWER_TOTALS["big"] / total))
    medium = min(SUNFLOWER_TOTALS["medium"], round(leaf_count * SUNFLOWER_TOTALS["medium"] / total))
    small = min(SUNFLOWER_TOTALS["small"], leaf_count - big - medium)
    return {"big": big, "medium": medium, "small": small}


def apply_leaf_count(leaf_count: int) -> None:
    """Restricts every species to its first `leaf_count` leaf models.

    Call once, before building any plant. This is what the `renders_{N}`
    variants of the dataset differ in.
    """
    if not 1 <= leaf_count <= MAX_LEAF_COUNT:
        raise ValueError(f"leaf_count must be between 1 and {MAX_LEAF_COUNT}, got {leaf_count}")
    for species, catalogue in LEAVES.items():
        if species == "sunflower":
            for size, count in _sunflower_size_counts(leaf_count).items():
                catalogue[size] = catalogue[size][:count]
        else:
            catalogue["all"] = catalogue["all"][:leaf_count]
