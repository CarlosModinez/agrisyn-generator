from .base import Builder, RENDERS_COLLECTION, ROLE_PROPERTY
from .ground import GroundBuilder
from .plant import PlantBuilder, SizeEnum
from .sunflower import SunflowerBuilder
from .corn import CornBuilder
from .milk_thistle import MilkThistleBuilder
from .common_buckwheat import CommonBuckwheatBuilder

# Species name (as used in config.LEAVES and in the output folders) -> builder
PLANT_BUILDERS = {
    "sunflower": SunflowerBuilder,
    "corn": CornBuilder,
    "milk_thistle": MilkThistleBuilder,
    "common_buckwheat": CommonBuckwheatBuilder,
}

__all__ = [
    "Builder",
    "RENDERS_COLLECTION",
    "ROLE_PROPERTY",
    "GroundBuilder",
    "PlantBuilder",
    "SizeEnum",
    "SunflowerBuilder",
    "CornBuilder",
    "MilkThistleBuilder",
    "CommonBuckwheatBuilder",
    "PLANT_BUILDERS",
]
