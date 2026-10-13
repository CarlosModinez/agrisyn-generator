import math
import random

import bpy


def add_sun(energy: float):
    """Sun lamp with the given energy, a random angular size in [0.004, 0.05] rad
    (hard to soft shadows), inclination 45-75 degrees from the zenith and a free azimuth."""
    data = bpy.data.lights.new(name="Sun", type="SUN")
    data.energy = energy
    data.angle = random.uniform(0.004, 0.05)
    data.use_shadow = True

    sun = bpy.data.objects.new(name="Sun", object_data=data)
    bpy.context.scene.collection.objects.link(sun)
    sun.location = (0.0, 0.0, 10.0)
    sun.rotation_euler = (
        math.radians(random.uniform(45.0, 75.0)),
        0.0,
        random.uniform(-math.pi, math.pi),
    )
    return sun


def set_nishita_sky():
    """Nishita sky as the world background: natural ambient light instead of a flat
    colour. Sun elevation in [35, 65] degrees, strength in [0.2, 0.5] so the sun
    shadows are not washed out. Does not affect the mask (emission materials)."""
    scene = bpy.context.scene
    if scene.world is None:
        scene.world = bpy.data.worlds.new("World")
    world = scene.world
    world.use_nodes = True
    nodes, links = world.node_tree.nodes, world.node_tree.links

    output = next((n for n in nodes if n.type == "OUTPUT_WORLD"), None) or nodes.new("ShaderNodeOutputWorld")
    background = next((n for n in nodes if n.type == "BACKGROUND"), None) or nodes.new("ShaderNodeBackground")
    sky = next((n for n in nodes if n.type == "TEX_SKY"), None) or nodes.new("ShaderNodeTexSky")

    sky.sky_type = "NISHITA"
    sky.sun_elevation = math.radians(random.uniform(35.0, 65.0))
    sky.sun_rotation = random.uniform(-math.pi, math.pi)
    for name, value in (("Air", 1.0), ("Dust", 0.1), ("Ozone", 0.3)):
        if name in sky.inputs:
            sky.inputs[name].default_value = value

    if not background.inputs["Color"].is_linked:
        links.new(sky.outputs["Color"], background.inputs["Color"])
    if not output.inputs["Surface"].is_linked:
        links.new(background.outputs["Background"], output.inputs["Surface"])
    background.inputs["Strength"].default_value = random.uniform(0.2, 0.5)
    return world


def remove_lights() -> None:
    for obj in [o for o in bpy.data.objects if o.type == "LIGHT"]:
        bpy.data.objects.remove(obj, do_unlink=True)
