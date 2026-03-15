"""CLI for image storer."""

import argparse
import sys
from pathlib import Path

from . import storage


def cmd_add(args: argparse.Namespace) -> None:
    snap = storage.get_snapshots_dir()
    for path in args.files:
        p = Path(path)
        if not p.exists():
            print(f"Skip (not found): {p}", file=sys.stderr)
            continue
        if not p.is_file():
            print(f"Skip (not a file): {p}", file=sys.stderr)
            continue
        suf = p.suffix.lower()
        if suf not in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
            print(f"Skip (not an image): {p}", file=sys.stderr)
            continue
        with open(p, "rb") as f:
            name = storage.add_image(f, filename=p.name)
        print(f"Added: {name} <- {p}")


def cmd_list(args: argparse.Namespace) -> None:
    images = storage.list_images()
    if not images:
        print("No snapshots.")
        return
    for img in images:
        print(img["id"])


def cmd_serve(args: argparse.Namespace) -> None:
    from .server import run as run_server
    host = args.host or "127.0.0.1"
    port = args.port or 5847
    print(f"Snapshot Bucket at http://{host}:{port}")
    print("Drop images or paste (Ctrl+V). Close with Ctrl+C.")
    run_server(host=host, port=port, debug=args.debug)


def cmd_clear(args: argparse.Namespace) -> None:
    if not args.yes and input("Delete all snapshots? [y/N] ").strip().lower() != "y":
        print("Aborted.")
        return
    n = storage.clear_all()
    print(f"Removed {n} snapshot(s).")


def cmd_remove(args: argparse.Namespace) -> None:
    for image_id in args.ids:
        if storage.remove_image(image_id):
            print(f"Removed: {image_id}")
        else:
            print(f"Not found: {image_id}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="image-storer",
        description="Local scratch space for image snapshots. CLI + web UI.",
    )
    parser.add_argument(
        "--dir",
        default=None,
        help="Storage directory (default: ~/.image-storer). Env: IMAGE_STORER_DIR",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add_p = sub.add_parser("add", help="Add image file(s)")
    add_p.add_argument("files", nargs="+", help="Path(s) to image file(s)")
    add_p.set_defaults(func=cmd_add)

    list_p = sub.add_parser("list", help="List stored image IDs")
    list_p.set_defaults(func=cmd_list)

    serve_p = sub.add_parser("serve", help="Start web UI (drag-drop, paste, gallery)")
    serve_p.add_argument("--host", default=None, help="Bind host (default: 127.0.0.1)")
    serve_p.add_argument("--port", type=int, default=None, help="Port (default: 5847)")
    serve_p.add_argument("--debug", action="store_true", help="Flask debug mode")
    serve_p.set_defaults(func=cmd_serve)

    clear_p = sub.add_parser("clear", help="Delete all snapshots")
    clear_p.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    clear_p.set_defaults(func=cmd_clear)

    remove_p = sub.add_parser("remove", help="Delete one or more snapshots by ID")
    remove_p.add_argument("ids", nargs="+", help="Image ID(s) from list")
    remove_p.set_defaults(func=cmd_remove)

    args = parser.parse_args()
    if args.dir is not None:
        import os
        os.environ["IMAGE_STORER_DIR"] = args.dir
    args.func(args)


if __name__ == "__main__":
    main()
