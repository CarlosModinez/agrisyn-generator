import random

from .. import config
from .plant import PlantBuilder, SizeEnum


class SunflowerBuilder(PlantBuilder):
    """The only species with size categories: the crosses built first (top) use
    small/medium leaves and the last ones (bottom) use the big leaves."""

    cross_spacing_range = (0.0012 * config.REAL_SCALE, 0.0022 * config.REAL_SCALE)
    leaf_jitter_range = (-0.0004 * config.REAL_SCALE, 0.0006 * config.REAL_SCALE)

    def __init__(self):
        super().__init__("sunflower")

    def _sample_n_crosses(self) -> int:
        return random.choice([1, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 4])

    def _sample_n_leaves(self) -> int:
        return random.randint(2, 4)

    def _cross_rotation(self, cross_position: int) -> float:
        return cross_position * 90.0

    def _select_leaves(self, cross_index: int, n_crosses: int) -> list:
        if cross_index / n_crosses <= 0.5:
            is_medium = random.choice([True, False, False, False])
            size = SizeEnum.MEDIUM if is_medium else SizeEnum.SMALL
        elif cross_index / n_crosses <= 0.67:
            is_medium = random.choice([True, True, True, False])
            size = SizeEnum.MEDIUM if is_medium else SizeEnum.BIG
        else:
            size = SizeEnum.BIG
        return config.LEAVES["sunflower"][size.value]
