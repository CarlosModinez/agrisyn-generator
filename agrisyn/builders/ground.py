import math
import random

import bpy
from mathutils import Vector

from .. import config
from .base import Builder


class GroundBuilder(Builder):
    """Builds the ground by duplicating one of the reference planes of the "ground" collection.

    The plane in the .blend is ready to use (material, displacement modifier,
    dimensions). It is copied, placed at the origin and randomised: free rotation
    around Z and uniform scale in X/Y (Z stays 1 to preserve the relief height).
    The scale starts at the minimum that keeps the whole camera footprint inside
    the rotated plane, so no rotation ever exposes the scene background.
    """

    role = "ground"

    # Multiplicative jitter over the minimum scale: varies the apparent size of
    # the texture and relief features between scenes.
    scale_jitter_range = (1.0, 2.0)

    def __init__(self, soil_material: str):
        self.soil_material = soil_material  # plane name inside the "ground" collection
        self.plane_obj = None
        super().__init__()

    def build(self) -> None:
        source = self._source_plane()
        plane = source.copy()
        plane.data = source.data.copy()
        self.plane_obj = plane
        self.link(plane)

        angle = random.uniform(0.0, 2.0 * math.pi)

        # Minimum scale for the footprint (W x H) to fit inside the plane
        # rotated by `angle`: its bounding box in the plane frame measures
        # W|cos| + H|sin| by W|sin| + H|cos|.
        width, height = config.camera_footprint()
        dims = source.dimensions
        cos_a, sin_a = abs(math.cos(angle)), abs(math.sin(angle))
        required_x = width * cos_a + height * sin_a
        required_y = width * sin_a + height * cos_a
        min_scale = max(required_x / dims.x, required_y / dims.y)
        scale = max(1.0, min_scale) * random.uniform(*self.scale_jitter_range)

        plane.location = (0.0, 0.0, 0.0)
        plane.rotation_euler = (0.0, 0.0, angle)
        plane.scale = (scale, scale, 1.0)
        bpy.context.view_layer.update()

    def _source_plane(self):
        collection = bpy.data.collections.get(config.GROUND_COLLECTION)
        source = collection.objects.get(self.soil_material) if collection else None
        if source is None:
            raise ValueError(
                f"Ground plane '{self.soil_material}' not found in collection '{config.GROUND_COLLECTION}'"
            )
        return source

    def height_at(self, x: float, y: float, radius: float = 0.02) -> float:
        """Height (z, metres) of the top of the ground around (x, y).

        Casts rays downwards onto the evaluated mesh (modifiers applied) at the
        centre and four neighbours `radius` away and returns the highest hit, so
        a plant sits on top of stones and relief instead of being buried. The
        value can be negative where the displacement lowers the ground.
        """
        if self.plane_obj is None:
            return 0.0
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = self.plane_obj.evaluated_get(depsgraph)
        matrix_world = eval_obj.matrix_world
        matrix_inv = matrix_world.inverted()
        direction = (matrix_inv.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()

        top = None
        for dx, dy in ((0, 0), (radius, 0), (-radius, 0), (0, radius), (0, -radius)):
            origin = matrix_inv @ Vector((x + dx, y + dy, 1.0))
            hit, location, _, _ = eval_obj.ray_cast(origin, direction)
            if hit:
                z = (matrix_world @ location).z
                top = z if top is None else max(top, z)
        return top if top is not None else 0.0
