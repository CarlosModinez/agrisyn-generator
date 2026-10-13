"""AgriSyn Generator entry point. Runs inside Blender; script arguments come after `--`.

    # compose + render (the normal pipeline)
    blender -b blender/agrisyn.blend -P main.py -- generate --leaf-count 50 --species corn --range-end 10

    # compose only: save each scene as a .blend you can open in Blender
    blender -b blender/agrisyn.blend -P main.py -- compose --leaf-count 50 --species corn --range-end 1

    # render scenes saved by `compose`
    blender -b -P main.py -- render scenes/renders_50/corn/0.blend
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy  # noqa: E402

from agrisyn import config, metadata  # noqa: E402
from agrisyn.scene import (  # noqa: E402
    compose_scene,
    configure_render,
    render_outputs,
    reset_scene,
    save_scene,
    scene_info,
)

DEFAULT_SEED = 42  # the seed used to generate the published AgriSyn dataset


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(
        prog="blender -b blender/agrisyn.blend -P main.py --",
        description="Synthetic top-down plant images with binary segmentation masks.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    def scene_options(command):
        command.add_argument(
            "--leaf-count", type=int, default=config.MAX_LEAF_COUNT, metavar="N",
            help=f"use only the first N leaf models of each species (1-{config.MAX_LEAF_COUNT}); "
                 f"output goes to renders_N/ (default: {config.MAX_LEAF_COUNT})",
        )
        command.add_argument(
            "--species", nargs="+", choices=config.SPECIES, default=config.SPECIES, metavar="SPECIES",
            help=f"one or more of {', '.join(config.SPECIES)} (default: all)",
        )
        command.add_argument("--range-start", type=int, default=0, metavar="I", help="first scene id (default: 0)")
        command.add_argument("--range-end", type=int, default=1000, metavar="J", help="last scene id, exclusive (default: 1000)")
        command.add_argument(
            "--seed", type=int, default=DEFAULT_SEED,
            help=f"base seed; scene i uses seed + i, so any range reproduces the same images (default: {DEFAULT_SEED})",
        )

    generate = commands.add_parser("generate", help="compose and render scenes: images, masks and metadata")
    scene_options(generate)
    generate.add_argument("--output-dir", default="renders", help="output root (default: renders/)")

    compose = commands.add_parser("compose", help="compose scenes and save each one as a self-contained .blend")
    scene_options(compose)
    compose.add_argument("--output-dir", default="scenes", help="output root (default: scenes/)")

    render = commands.add_parser("render", help="render .blend scenes saved by `compose`")
    render.add_argument("scenes", nargs="+", metavar="SCENE.blend")
    render.add_argument("--output-dir", default="renders", help="output root (default: renders/)")

    return parser.parse_args(argv)


def output_root(output_dir: str, leaf_count: int, species: str) -> str:
    return os.path.join(output_dir, f"renders_{leaf_count}", species)


def write_metadata(root: str, info: dict, stats: dict) -> None:
    metadata.write_row(os.path.join(root, metadata.FILENAME), {
        "image": f"{info['scene_id']}.png",
        **info,
        **stats,
        "camera_height": config.CAMERA["height"],
        "camera_x": 0.0,
        "camera_y": 0.0,
    })


def require_library_file() -> str:
    if not bpy.data.filepath:
        sys.exit("This command needs the leaf library: blender -b blender/agrisyn.blend -P main.py -- ...")
    return bpy.data.filepath


def cmd_generate(args) -> None:
    require_library_file()
    config.apply_leaf_count(args.leaf_count)
    configure_render()
    for species in args.species:
        root = output_root(args.output_dir, args.leaf_count, species)
        for scene_id in range(args.range_start, args.range_end):
            image = os.path.join(root, "images", f"{scene_id}.png")
            mask = os.path.join(root, "masks", f"{scene_id}.png")
            if os.path.exists(image) and os.path.exists(mask):
                print(f"{species} {scene_id}: already rendered, skipping")
                continue
            reset_scene()
            info = compose_scene(species, scene_id, seed=args.seed + scene_id, leaf_count=args.leaf_count)
            stats = render_outputs(root, scene_id)
            write_metadata(root, info, stats)
            print(f"{species} {scene_id}: {info['n_plants']} plant(s), {stats['plant_area_px']} plant px, "
                  f"{stats['render_time_s']} s")


def cmd_compose(args) -> None:
    library = require_library_file()
    config.apply_leaf_count(args.leaf_count)
    jobs = [(species, scene_id) for species in args.species for scene_id in range(args.range_start, args.range_end)]
    for n, (species, scene_id) in enumerate(jobs):
        if n > 0:  # save_scene drops the libraries: reload them for the next scene
            bpy.ops.wm.open_mainfile(filepath=library)
        configure_render()
        reset_scene()
        info = compose_scene(species, scene_id, seed=args.seed + scene_id, leaf_count=args.leaf_count)
        path = os.path.join(output_root(args.output_dir, args.leaf_count, species), f"{scene_id}.blend")
        save_scene(path)
        print(f"{species} {scene_id}: {info['n_plants']} plant(s) -> {path}")


def cmd_render(args) -> None:
    for path in args.scenes:
        bpy.ops.wm.open_mainfile(filepath=os.path.abspath(path))
        info = scene_info()
        configure_render()
        root = output_root(args.output_dir, info["leaf_count"], info["species"])
        stats = render_outputs(root, info["scene_id"])
        write_metadata(root, info, stats)
        print(f"{path}: {stats['plant_area_px']} plant px, {stats['render_time_s']} s -> {root}")


COMMANDS = {"generate": cmd_generate, "compose": cmd_compose, "render": cmd_render}

if __name__ == "__main__":
    arguments = parse_args()
    COMMANDS[arguments.command](arguments)
    print("done")
