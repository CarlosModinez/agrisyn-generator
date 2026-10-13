import random

from .plant import PlantBuilder


class CommonBuckwheatBuilder(PlantBuilder):
    cross_spacing_range = (0.0010, 0.0018)
    leaf_jitter_range = (-0.0003, 0.0004)

    def __init__(self):
        super().__init__("common_buckwheat")

    def _sample_n_crosses(self) -> int:
        return random.randint(1, 4)

    def _sample_n_leaves(self) -> int:
        return random.randint(2, 4)
