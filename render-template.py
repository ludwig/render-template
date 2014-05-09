#!/usr/bin/env python

import os, sys, imp
import importlib
from collections import namedtuple, OrderedDict

templateroot = os.path.dirname(os.path.realpath(sys.argv[0]))
sys.path.insert(1, os.path.join(templateroot, 'actions'))

Template = namedtuple('TemplateInfo', 'action,description')

TEMPLATES = OrderedDict([
    ('Makefile.ninja', Template(None, 'Prints out a sample Makefile that uses the ninja build system')),
    ('build.ninja', Template('ninja_build', 'Creates a sample build.ninja file')),
    ('targets.ninja', Template('ninja_targets', 'Creates targets.ninja from a targets.yaml build spec file')),
    ('targets.yaml', Template(None, 'Prints out a sample targets.yaml file')),
    ('CMakeLists.txt', Template(None, 'Prints out a cmake configuration file')),
])

def cat(filename):
    """Writes filename to stdout"""
    with open(os.path.join(templateroot, 'templates', filename), 'r') as fp:
        sys.stdout.write(fp.read())

def usage():
    sys.stderr.write("Usage: {} <template> [ <template-options> ]\n".format(sys.argv[0]))
    sys.stderr.write("\nWhere <template> is one of:\n\n")
    for name, tmpl in TEMPLATES.items():
        sys.stderr.write('    {0} - {1}\n'.format(name, tmpl.description))
    sys.stderr.write('\n')

def main():

    if len(sys.argv) == 1:
        usage()
        sys.exit(1)

    name = sys.argv[1]
    tmpl = TEMPLATES.get(name)

    if not tmpl:
        usage()
        sys.exit(2)
    elif not tmpl.action:
        cat(name)
    elif callable(tmpl.action):
        info.action(sys.argv[1:])
    else:
        modname = tmpl.action
        mod = importlib.import_module(modname)
        mod.main(sys.argv[2:])

    return

if __name__ == '__main__':
    main()

# EOF
