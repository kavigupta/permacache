import argparse

from .cache import to_file, from_file


def cache_args(parser):
    parser.add_argument("cache_name", help="The name of the cache to export")
    parser.add_argument("zip_path", help="The path to export the zip path to")


def do_export(args):
    to_file(args.cache_name, normalize_zip(args.zip_path))


def do_import(args):
    from_file(args.cache_name, normalize_zip(args.zip_path))


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
        "import", help="Export a cache to a file", aliases=["i"]
    )
    cache_args(import_parser)
    import_parser.set_defaults(fn=do_import)

    args = parser.parse_args()
    args.fn(args)
