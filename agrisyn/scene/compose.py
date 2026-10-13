"""Scene composition: ground + plants + camera + light, and saving a composed scene to a .blend."""

import math
import os
import random

import bpy

from .. import config
from ..builders import PLANT_BUILDERS, RENDERS_COLLECTION, GroundBuilder
from .camera import create_camera
from .light import add_sun, set_nishita_sky

# ID property of the Blender scene that stores the description of the composed
# scene, so a saved .blend can be rendered later with the right metadata.
SCENE_PROPERTY = "agrisyn"


def reset_scene() -> None:
    """Removes everything built for the previous scene: the objects and
    sub-collections of "renders", the camera and the lights. Libraries are untouched."""
    renders = bpy.data.collections.get(RENDERS_COLLECTION)
    if renders is not None:
        for collection in [renders, *renders.children_recursive]:
            for obj in list(collection.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
        for child in list(renders.children_recursive):
            bpy.data.collections.remove(child)
    for obj in [o for o in bpy.data.objects if o.type in ("CAMERA", "LIGHT")]:
        bpy.data.objects.remove(obj, do_unlink=True)


def compose_scene(species: str, scene_id: int, seed: int, leaf_count: int) -> dict:
    """Builds one scene of a single species and returns its description.

    All randomness comes from `random` seeded with `seed`, so the same
    (species, scene_id, seed, leaf_count) always gives the same scene.
    """
    random.seed(seed)

    soil = config.SOIL_MATERIALS[scene_id % len(config.SOIL_MATERIALS)]
    ground = GroundBuilder(soil)
    ground.build()

    profile = config.PLANT_DISTRIBUTION[species]
    n_plants = random.choices(range(1, len(profile["n_plants"]) + 1), weights=profile["n_plants"])[0]
    width, height = config.camera_footprint()
    lo, hi = profile["scale"]

    scales = []
    for _ in range(n_plants):
        plant = PLANT_BUILDERS[species]()
        plant.build()
        factor = math.exp(random.uniform(math.log(lo), math.log(hi)))
        plant.scale(factor)
        scales.append(round(factor, 3))
        plant.move_to(random.uniform(-width / 2, width / 2), random.uniform(-height / 2, height / 2), ground=ground)

    create_camera()
    sun_energy = random.uniform(3.0, 6.0)
    sun = add_sun(sun_energy)
    set_nishita_sky()

    info = {
        "species": species,
        "scene_id": scene_id,
        "seed": seed,
        "leaf_count": leaf_count,
        "n_plants": n_plants,
        "soil_material": soil,
        "sun_tilt_deg": round(math.degrees(sun.rotation_euler.x), 2),
        "sun_azimuth_deg": round(math.degrees(sun.rotation_euler.z), 2),
        "sun_energy": round(sun_energy, 2),
        "plant_scales": ";".join(map(str, scales)),
    }
    bpy.context.scene[SCENE_PROPERTY] = info
    return info


def scene_info() -> dict:
    """Description stored by `compose_scene` in the current Blender scene."""
    stored = bpy.context.scene.get(SCENE_PROPERTY)
    if stored is None:
        raise ValueError("The current .blend has no composed scene (run `compose` first)")
    return stored.to_dict()


def save_scene(filepath: str) -> None:
    """Saves the composed scene as a self-contained .blend.

    The leaf and ground libraries are dropped first (the scene only keeps its
    own copies), so the file is small and can be opened in Blender or rendered
    later with `render`. Reopen the library file before composing another scene.
    """
    renders = bpy.data.collections.get(RENDERS_COLLECTION)
    keep_collections = {c.name for c in [renders, *renders.children_recursive]}
    keep_objects = {o.name for o in renders.all_objects}
    keep_objects |= {o.name for o in bpy.data.objects if o.type in ("CAMERA", "LIGHT")}

    for obj in list(bpy.data.objects):
        if obj.name not in keep_objects:
            bpy.data.objects.remove(obj, do_unlink=True)
    for collection in list(bpy.data.collections):
        if collection.name not in keep_collections:
            bpy.data.collections.remove(collection)
    for _ in range(3):
        bpy.data.orphans_purge(do_recursive=True)

    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(filepath), copy=True, compress=True)
