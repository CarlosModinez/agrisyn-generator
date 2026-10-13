import random

from .plant import PlantBuilder


class MilkThistleBuilder(PlantBuilder):
    cross_spacing_range = (0.0010, 0.0018)
    leaf_jitter_range = (-0.0003, 0.0004)

    def __init__(self):
        super().__init__("milk_thistle")

    def _sample_n_crosses(self) -> int:
        return random.choice([1, 1, 1, 1, 1, 1, 1, 2])

    def _sample_n_leaves(self) -> int:
        return random.choice([1, 2, 2, 2, 2, 2, 3, 3])
