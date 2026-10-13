import bpy

from .. import config


def create_camera():
    """Nadir (top-down) camera at CAMERA["height"] above the origin.

    Lens, sensor and resolution come from the same configuration used to
    compute the camera footprint, so plants are always placed inside the frame.
    """
    cam = config.CAMERA
    data = bpy.data.cameras.new(name="Camera")
    data.lens = cam["lens_mm"]
    data.sensor_width = cam["sensor_mm"]

    camera = bpy.data.objects.new("Camera", data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = (0.0, 0.0, cam["height"])
    camera.rotation_euler = (0.0, 0.0, 0.0)

    scene = bpy.context.scene
    scene.camera = camera
    scene.render.resolution_x = cam["resolution_x"]
    scene.render.resolution_y = cam["resolution_y"]
    scene.render.resolution_percentage = 100
    return camera
