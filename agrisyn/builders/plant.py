import math
import random
from enum import Enum

import bpy

from .. import config
from .base import Builder


class SizeEnum(Enum):
    BIG = "big"
    MEDIUM = "medium"
    SMALL = "small"


class PlantBuilder(Builder):
    """Base of every species: a plant is a stack of leaf "crosses".

    The construction is shared; each species only defines its leaf catalogue
    and the sampling constants below. Every cross is tilted around the local X
    axis of its leaves: the bottom cross lies almost flat on the ground and the
    upper crosses tilt progressively more (younger leaves are more upright).
    """

    role = "plant"

    # Lengths are in metres at real scale (see config.REAL_SCALE).
    base_z = 0.0                                                      # the first cross touches the ground
    cross_spacing_range = (0.0010 * config.REAL_SCALE, 0.0018 * config.REAL_SCALE)  # between crosses
    leaf_jitter_range = (-0.0003 * config.REAL_SCALE, 0.0004 * config.REAL_SCALE)   # per leaf, inside a cross
    min_z = 0.0                                                       # no leaf below the ground
    tilt_variation = 0.08                                             # random tilt variation per leaf (rad)
    tilt_step_deg = 5.0                                               # tilt increment per cross (degrees)

    def __init__(self, species: str):
        self.species = species
        super().__init__()
        self.library = bpy.data.collections.get(species)  # leaf models of the species

    # --- Species hooks -----------------------------------------------------------

    def _sample_n_crosses(self) -> int:
        raise NotImplementedError

    def _sample_n_leaves(self) -> int:
        raise NotImplementedError

    def _select_leaves(self, cross_index: int, n_crosses: int) -> list:
        """Leaf catalogue for the cross `cross_index` (0 = first built = top)."""
        return config.LEAVES[self.species]["all"]

    def _cross_rotation(self, cross_position: int) -> float:
        """Extra rotation (degrees) of the cross around Z."""
        return 0.0

    # --- Shared construction -------------------------------------------------------

    def build(self) -> None:
        n_crosses = self._sample_n_crosses()
        tilts = self._sample_cross_tilts(n_crosses)
        for n in range(n_crosses):
            leaves = self._select_leaves(n, n_crosses)
            cross_position = n_crosses - n - 1  # the first cross built is the highest
            self._build_cross(leaves, cross_position, tilts[cross_position])

    def _sample_cross_tilts(self, n_crosses: int) -> list:
        """Local X tilt per cross level (index 0 = bottom), always increasing upwards."""
        tilts, step_deg = [], 0.0
        for level in range(n_crosses):
            tilts.append(level * math.radians(step_deg))
            step_deg += self.tilt_step_deg / (level + 1) * random.uniform(0.8, 1.2)
        return tilts

    def _build_cross(self, leaves: list, cross_position: int, base_tilt: float) -> None:
        n_leaves = self._sample_n_leaves()
        cross_rotation = self._cross_rotation(cross_position)
        cross_z = self.base_z + cross_position * random.uniform(*self.cross_spacing_range)

        for n in range(n_leaves):
            leaf = self._copy_leaf(leaves)
            if leaf is None:
                continue
            leaf.name = f"{self.species}_cross_{cross_position}_leaf_{n}"
            self.link(leaf)

            jitter_z = random.uniform(*self.leaf_jitter_range)
            leaf.location = (0.0, 0.0, max(self.min_z, cross_z + jitter_z))

            angle = (360.0 / n_leaves) * n + random.randint(-10, 10) + cross_rotation
            leaf.rotation_euler.z = math.radians(angle)
            # Tilt around the leaf's local X axis, clamped at >= 0 so the base
            # stays on the ground and the tip always points upwards.
            tilt = max(0.0, base_tilt + random.uniform(-self.tilt_variation, self.tilt_variation))
            leaf.rotation_euler.rotate_axis("X", tilt)

    def _copy_leaf(self, leaves: list):
        name = random.choice(leaves)
        source = self.library.objects.get(name) if self.library is not None else None
        if source is None:
            source = bpy.data.objects.get(name)
        if source is None:
            print(f"Leaf object '{name}' not found for {self.species}")
            return None
        leaf = source.copy()
        leaf.data = source.data.copy()
        return leaf

    def scale(self, factor: float) -> None:
        """Uniform scale of the plant around its base (0, 0, 0).

        Call after `build()` and before `move_to()`: the leaves are still at the
        origin in XY, so scaling the objects and their height is enough.
        """
        for obj in self.target_collection.objects:
            obj.scale = tuple(v * factor for v in obj.scale)
            obj.location.z *= factor

    def move_to(self, x: float, y: float, ground=None) -> None:
        """Moves the plant to (x, y), seated on the local top of the ground relief."""
        z_offset = ground.height_at(x, y) if ground is not None else 0.0
        for obj in list(self.target_collection.objects):
            obj.location.x = x
            obj.location.y = y
            obj.location.z += z_offset
