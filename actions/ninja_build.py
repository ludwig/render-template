#!/usr/bin/env python
"""
Creates a build.ninja file from a template string, and prints it to stdout

Note that you'll have to redirect output to a file in order to save it.

    $ render-template.py build.ninja > build.ninja

You can also specify variables in the argument list

    $ render-template.py build.ninja \
            cc=clang cxx=clang++ \
            cxxflags="-std=c++11 -Wall $(pkg-config sdl2 --cflags) $(pkg-config glfw3 --cflags)" \
            libs="$(pkg-config sdl2 --libs) $(pkg-config glfw3 --libs)" \
            home="$HOME"

"""

BUILD_NINJA_TEMPLATE = """\
# build.ninja template

# the usual variable bindings
bindir = {bindir}
builddir = {builddir}
srcdir = {srcdir}
cc = {cc}
cflags = {cflags}
cxx = {cxx}
cxxflags = {cxxflags}
ldflags = {ldflags}
libs = {libs}
{other-bindings}
rule cc
    command = $cc -MMD -MT $out -MF $out.d $cflags -c $in -o $out
    description = CC $out
    depfile = $out.d

rule cclink
    command = $cc $ldflags -o $out $in $libs
    description = CC-LINK $out

rule cxx
    command = $cxx -MMD -MT $out -MF $out.d $cxxflags -c $in -o $out
    description = CXX $out
    depfile = $out.d

rule cxxlink
    command = $cxx $ldflags -o $out $in $libs
    description = CXX-LINK $out

include targets.ninja

# EOF
"""

import sys, os
import collections

DEFAULT_VARIABLE_BINDINGS = dict(
    bindir = 'bin',
    builddir = 'build',
    srcdir = 'src',
    cc = 'gcc',
    cflags = '-Wall',
    cxx = 'g++',
    cxxflags = '-std=c++11 -Wall',
    ldflags = '',
    libs = '',
)

def build_template_context(argv):
    """
    Determine template context from environment variables and command line arguments.
    """

    ctx = DEFAULT_VARIABLE_BINDINGS.copy()
    other_bindings = collections.OrderedDict()

    # read variable bindings from environment variables.
    # we restrict ourselves to existing variables.
    for key in DEFAULT_VARIABLE_BINDINGS:
        if key in os.environ:
            ctx[key] = os.environ[key]

    # read variable bindings from command line argument list.
    # note that we can define new variables here.
    args = argv
    if len(args) > 0:
        for arg in args:
            assert '=' in arg
            i = arg.find('=')
            key, val = arg[:i], arg[i+1:]
            other_bindings[key] = val

    # merge those values into ctx
    ctx.update(other_bindings)

    # but remove default keys from other_bindings, otherwise we'll have duplicates
    # after we render the template
    for key in DEFAULT_VARIABLE_BINDINGS:
        if key in other_bindings:
            del other_bindings[key]

    # finally, build the string that will replace {other-bindings} in the template
    ctx['other-bindings'] = ''
    if other_bindings:
        ctx['other-bindings'] = '\n# other bindings\n'
        ctx['other-bindings'] += ''.join('{0} = {1}\n'.format(key,other_bindings[key]) for key in other_bindings)

    return ctx

def main(argv):
    ctx = build_template_context(argv)
    template = BUILD_NINJA_TEMPLATE.format(**ctx)
    sys.stdout.write(template)

if __name__ == '__main__':
    main(sys.argv[1:])

# EOF
