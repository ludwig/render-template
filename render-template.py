#!/usr/bin/env python

import os, sys, imp
import importlib
from collections import namedtuple, OrderedDict


skeldir = os.path.dirname(os.path.realpath(sys.argv[0]))
sys.path.insert(1, os.path.join(skeldir, 'actions'))

def cat(filename):
    """
    Writes filename to stdout
    """
    with open(os.path.join(skeldir, 'templates', filename)) as fp:
        sys.stdout.write(fp.read())

SkelInfo = namedtuple('SkelInfo', 'action,desc')
SKELETONS = OrderedDict([
    ('Makefile.ninja', SkelInfo(cat, 'Prints out a sample Makefile that uses the ninja build system')),
    ('build.ninja', SkelInfo('ninja_build', 'Creates a sample build.ninja file')),
    ('targets.ninja', SkelInfo('ninja_targets', 'Creates targets.ninja from a targets.yaml build spec file')),
    ('targets.yaml', SkelInfo(cat, 'Prints out a sample targets.yaml file')),
    ('CMakeLists.txt', SkelInfo(cat, 'Prints out a cmake configuration file')),
])

def usage():
    sys.stderr.write("Usage: {} <template> [ <template-options> ]\n".format(sys.argv[0]))
    sys.stderr.write("\nWhere <template> is one of:\n\n")
    for skel in SKELETONS:
        desc = SKELETONS[skel].desc
        sys.stderr.write('    {0} - {1}\n'.format(skel, SKELETONS[skel].desc))
    sys.stderr.write('\n')

def main():

    if len(sys.argv) == 1:
        usage()
        sys.exit(1)

    skel = sys.argv[1]
    info = SKELETONS.get(skel)

    if not info:
        usage()
        sys.exit(2)
    elif callable(info.action):
        info.action(skel)
    else:
        modname = info.action
        mod = importlib.import_module(modname)
        mod.main(sys.argv[2:])

    return

if __name__ == '__main__':
    main()

# EOF