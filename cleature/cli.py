"""
Command-line interface for Cleature.

Provides the CLI entry point to render CHTML files into HTML,
with support for directory exclusion, refresh options, debugging,
and passing global template variables.

© CodemasterUnited 2025
"""

import argparse
import sys
from pathlib import Path
from cleature.core import render

VERSION = "0.1"


def build_parser():
    """ Build and return the argument parser. """
    parser = argparse.ArgumentParser(
        prog="cleature",
        description="Cleature: CHTML rendering engine"
    )
    parser.add_argument("--version", action="version", version=f"Cleature v{VERSION}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # render command
    render_parser = subparsers.add_parser("render", help="Render .chtml files to .html")
    render_parser.add_argument("srcdir", help="Source directory containing .chtml files")
    render_parser.add_argument("distdir", help="Output directory for rendered HTML files")
    render_parser.add_argument(
        "--refresh",
        action="store_true",
        help="Clear dist directory before rendering"
    )
    render_parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="Directories to exclude from rendering"
    )
    render_parser.add_argument("--debug", action="store_true", help="Enable debug output")
    render_parser.add_argument(
        "--variables",
        nargs="*",
        default=[],
        metavar="KEY=VALUE",
        help="Global variables to pass to templates"
    )
    render_parser.set_defaults(func=render_command)

    return parser


def render_command(args):
    """
    Handle the 'render' command.

    Parameters passed to the renderer:
    - refresh_dist: whether to clear the dist directory first
    - excluded_dirs: list of directory names to exclude
    - debug: enable debug print output
    - variables: dictionary of template variables (parsed from --variables)
    """
    src = Path(args.srcdir).resolve()

    if not src.is_dir():
        print(f"✖ Source directory does not exist: {src}", file=sys.stderr)
        sys.exit(1)

    dist = Path(args.distdir).resolve()

    # Parse --variables into a dictionary
    variables = {}
    for item in args.variables:
        if "=" in item:
            key, value = item.split("=", 1)
            variables[key.strip()] = value.strip()
        else:
            print(f"✖ Invalid variable format: {item} (expected KEY=VALUE)", file=sys.stderr)
            sys.exit(1)

    try:
        result = render(src, dist, {
            "refresh_dist": args.refresh,
            "excluded_dirs": args.exclude,
            "debug": args.debug,
            "variables": variables
        })

        print(f"\n✔ Rendered {len(result)} file{'s' if len(result) != 1 else ''}.")
    except Exception as e:  # pylint:disable=broad-exception-caught
        print(f"✖ Error: {e}", file=sys.stderr)
        sys.exit(1)


def main(argv=None):
    """ Entry point for the CLI. """
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)

if __name__ == "__main__":
    main()
