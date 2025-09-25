import argparse
import os
import sys

from .cache import from_file, to_file
from .locked_shelf import LockedShelf


def cache_args(parser):
    parser.add_argument("cache_name", help="The name of the cache to export")
    parser.add_argument("zip_path", help="The path to export the zip path to")


def count_args(parser):
    parser.add_argument("cache_name", help="The name of the cache to count keys in")


def do_export(args):
    to_file(args.cache_name, normalize_zip(args.zip_path))


def do_import(args):
    from_file(args.cache_name, normalize_zip(args.zip_path))


def count_keys_in_cache(cache_path):
    """Count the number of keys in a cache directory."""
    if not os.path.exists(cache_path):
        raise RuntimeError(f"Cache does not exist: {cache_path}")

    # Use LockedShelf for combined-file cache
    with LockedShelf(cache_path) as shelf:
        return len(list(shelf.items()))


def do_count(args):
    from appdirs import user_cache_dir

    cache_dir = user_cache_dir("permacache")
    cache_path = os.path.join(cache_dir, args.cache_name)

    try:
        count = count_keys_in_cache(cache_path)
        print(f"Cache '{args.cache_name}' contains {count} keys")
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def normalize_zip(path):
    if path.endswith(".zip"):
        path = path[:-4]
    return path


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd")
    subparsers.required = True
    export_parser = subparsers.add_parser(
        "export", help="Export a cache to a file", aliases=["e"]
    )
    cache_args(export_parser)
    export_parser.set_defaults(fn=do_export)
    import_parser = subparsers.add_parser(
        "import", help="Import a cache from a file", aliases=["i"]
    )
    cache_args(import_parser)
    import_parser.set_defaults(fn=do_import)
    count_parser = subparsers.add_parser(
        "count", help="Count the number of keys in a cache", aliases=["c"]
    )
    count_args(count_parser)
    count_parser.set_defaults(fn=do_count)

    args = parser.parse_args()
    args.fn(args)
