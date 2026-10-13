import random

from .plant import PlantBuilder


class CornBuilder(PlantBuilder):
    cross_spacing_range = (0.0002, 0.0020)
    leaf_jitter_range = (-0.0003, 0.0003)

    def __init__(self):
        super().__init__("corn")

    def _sample_n_crosses(self) -> int:
        return random.randint(1, 2)

    def _sample_n_leaves(self) -> int:
        return random.choice([2, 2, 2, 3])
