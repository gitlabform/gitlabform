#!/usr/bin/env python3
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from packaging.version import parse


def parse_args():
    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        description="""
        Print out the release type (public or pre) based on input
        from a file or directly through -V parameter.
        """,
    )

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("-V", "--version", help="Package version")
    group.add_argument(
        "-f", "--file", help="Pile name to read version from", default="version"
    )
    args = parser.parse_args()

    if not args.version:
        with open(args.file, "r") as version_file:
            args.version = version_file.readline().strip()
    return args


cmdline_args = parse_args()
parsed_version = parse(cmdline_args.version)

if parsed_version.is_prerelease:
    print("pre")
else:
    # post- and standard releases
    print("public")
