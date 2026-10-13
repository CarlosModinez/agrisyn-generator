"""Cycles setup and rendering of the RGB image and the binary mask of a composed scene."""

import os
import time

import bpy

from .. import config, masks
from ..builders import RENDERS_COLLECTION, ROLE_PROPERTY
from .light import remove_lights

# Mask materials by object role: flat emission, so the mask does not depend on lighting.
MASK_MATERIALS = {
    "plant": ("agrisyn_mask_plant", (1.0, 1.0, 1.0, 1.0)),
    "ground": ("agrisyn_mask_ground", (0.0, 0.0, 0.0, 1.0)),
}

GPU_BACKENDS = ("METAL", "OPTIX", "CUDA", "HIP", "ONEAPI")


def configure_render() -> None:
    """Global render settings; call once per Blender session (and after reopening a file)."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.render.use_persistent_data = True  # keeps BVH/textures between the image and mask renders
    scene.cycles.use_denoising = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    _enable_gpu()


def _enable_gpu() -> None:
    """Uses the first available GPU backend; falls back to CPU rendering."""
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for backend in GPU_BACKENDS:
        try:
            prefs.compute_device_type = backend
        except (TypeError, ValueError):
            continue
        prefs.get_devices()
        gpus = [d for d in prefs.devices if d.type == backend]
        if gpus:
            for device in prefs.devices:
                device.use = device.type == backend
            bpy.context.scene.cycles.device = "GPU"
            print(f"Cycles: GPU rendering ({backend}, {len(gpus)} device(s))")
            return
    bpy.context.scene.cycles.device = "CPU"
    print("Cycles: no GPU backend available, rendering on CPU")


def _render(filepath: str, samples: int) -> None:
    scene = bpy.context.scene
    scene.cycles.samples = samples
    scene.render.filepath = filepath
    bpy.ops.render.render(write_still=True)


def _mask_material(name: str, color: tuple):
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
        material.use_nodes = True
        nodes, links = material.node_tree.nodes, material.node_tree.links
        for node in list(nodes):
            nodes.remove(node)
        output = nodes.new("ShaderNodeOutputMaterial")
        emission = nodes.new("ShaderNodeEmission")
        emission.inputs["Color"].default_value = color
        links.new(emission.outputs["Emission"], output.inputs["Surface"])
    return material


def apply_mask_materials() -> None:
    """Replaces every material of the scene objects by the flat mask material of their role."""
    renders = bpy.data.collections.get(RENDERS_COLLECTION)
    for obj in renders.all_objects:
        role = obj.get(ROLE_PROPERTY)
        if obj.type != "MESH" or role not in MASK_MATERIALS:
            continue
        material = _mask_material(*MASK_MATERIALS[role])
        if obj.data.materials:
            for i in range(len(obj.data.materials)):
                obj.data.materials[i] = material
        else:
            obj.data.materials.append(material)


def render_outputs(output_root: str, scene_id: int) -> dict:
    """Renders `images/{scene_id}.png` (RGB) and `masks/{scene_id}.png` (binary) under `output_root`.

    The scene is modified in place (mask materials, lights removed): compose a
    new scene or reopen the file before rendering again.
    """
    image_path = os.path.join(output_root, "images", f"{scene_id}.png")
    mask_path = os.path.join(output_root, "masks", f"{scene_id}.png")
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    os.makedirs(os.path.dirname(mask_path), exist_ok=True)

    start = time.time()
    _render(image_path, config.RENDER["samples"])
    render_time = time.time() - start

    apply_mask_materials()
    remove_lights()
    bpy.context.view_layer.update()
    raw_mask = mask_path + ".raw.png"
    _render(raw_mask, config.RENDER["mask_samples"])
    stats = masks.binarize(raw_mask, mask_path)
    os.remove(raw_mask)

    return {**stats, "render_time_s": round(render_time, 2)}
