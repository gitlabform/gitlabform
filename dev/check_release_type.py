#!/usr/bin/env python3
import sys
from argparse import ArgumentDefaultsHelpFormatter,ArgumentParser
from packaging.version import parse

def parse_args():
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('-f', '--file', help='version filename', default='version')
    group.add_argument('-V', '--version', help='version file')
    args = parser.parse_args()

    if not args.version:
        with open(args.file, "r") as version_file:
            args.version = version_file.readline().strip()
    return args


cmdline_args = parse_args()

parsed_version = parse(cmdline_args.version)

# order matters for packaging.version.parse():
# - a dev- release can be also a pre- release
if parsed_version.is_devrelease:
    print('dev')
elif parsed_version.is_prerelease:
    print('pre')
elif parsed_version.is_postrelease:
    print('post')
else:
    print('public')
