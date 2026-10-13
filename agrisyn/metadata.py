"""Per-image metadata, one `metadata.csv` per species folder."""

import csv
import os

FILENAME = "metadata.csv"

FIELDNAMES = [
    "image",
    "species",
    "n_plants",
    "plant_area_px",
    "background_area_px",
    "image_width",
    "image_height",
    "soil_material",
    "camera_height",
    "camera_x",
    "camera_y",
    "sun_tilt_deg",
    "sun_azimuth_deg",
    "sun_energy",
    "render_time_s",
    "seed",
    "plant_scales",
]


def write_row(csv_path: str, row: dict) -> None:
    """Appends a row, creating the file with a header if needed.

    A row with the same `image` is replaced, so an interrupted run can be
    resumed without duplicating the images that were already written.
    """
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    rows = []
    if os.path.exists(csv_path):
        with open(csv_path, newline="") as f:
            rows = [r for r in csv.DictReader(f) if r["image"] != row["image"]]
    rows.append({name: row.get(name, "") for name in FIELDNAMES})
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
