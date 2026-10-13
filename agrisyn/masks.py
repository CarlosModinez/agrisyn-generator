"""Binary masks: thresholds a rendered mask and writes it as an 8-bit grayscale PNG (0 = ground, 255 = plant)."""

import struct
import zlib

import bpy
import numpy as np

# Threshold on the brightest RGB channel of the rendered mask. Plants are
# rendered with a white emission material and the ground with a black one, so
# any value well above zero is plant.
THRESHOLD = 0.05
PLANT = 255
BACKGROUND = 0


def binarize(rendered_path: str, output_path: str) -> dict:
    """Converts the rendered mask into a binary PNG and returns pixel counts."""
    image = bpy.data.images.load(rendered_path)
    try:
        width, height = image.size
        pixels = np.empty(len(image.pixels), dtype=np.float32)
        image.pixels.foreach_get(pixels)
        plant = pixels.reshape(height, width, 4)[:, :, :3].max(axis=2) > THRESHOLD
    finally:
        bpy.data.images.remove(image)

    plant = plant[::-1]  # Blender stores rows bottom-up; PNG rows are top-down
    write_png_gray(output_path, np.where(plant, PLANT, BACKGROUND).astype(np.uint8))

    plant_area = int(plant.sum())
    return {
        "plant_area_px": plant_area,
        "background_area_px": width * height - plant_area,
        "image_width": width,
        "image_height": height,
    }


def write_png_gray(path: str, array: np.ndarray) -> None:
    """Writes a 2-D uint8 array as an 8-bit grayscale PNG (no external dependency)."""
    height, width = array.shape
    raw = b"".join(b"\x00" + array[row].tobytes() for row in range(height))  # filter byte 0 per row

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)  # bit depth 8, colour type 0 (grayscale)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", header))
        f.write(chunk(b"IDAT", zlib.compress(raw, 9)))
        f.write(chunk(b"IEND", b""))
