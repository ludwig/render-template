#!/usr/bin/env python
"""
This python module generates a targets.ninja file suitable for inclusion from 'build.ninja'.

Ninja build statements

    <http://martine.github.io/ninja/manual.html#_build_statements>

Here's a somewhat informal description of the kind of yaml files this file can parse:

    <yaml> :=
        ---
        <document1>
        --
        <...>
        ---
        <documentN>
        ...

    <document> :=
        - note: <string-value>
        - rebind: <list-of-bindings>
        - <rule-name1>: <list-of-targets>

    <list-of-bindings> :=
        - <binding1>
        - <...>
        - <bindingN>

    <binding> := <binding-name>: <binding-value-as-string>

    <list-of-targets>
        - <target1>
        - <...>
        - <targetN>

    <target> := <target-as-string> | <target-as-dict>

    <target-as-string> := <target-name>

    <target-as-dict> := <target-name>: <input-list>

    <input-list> := '' | ( '[' <comma-delimited-list-of-strings> '] ) | <input-list-multiline>

    <input-list-multiline> :=
        - <input-name>: <input-value>

Example yaml file

    ---
    - note:
        Compile object files in debug mode
    - rebind:
        - cxxflags: $cxxflags -DDEBUG -g
        - ldflags: -L$HOME/opt/local/lib
    - cxx:
        - hello.g.o: hello.cpp
        - goodbye.g.o: goodbye.cpp
    - cxxlink:
        - hello-g: hello.g.o
        - goodbye-g: goodbye.g.o
    ---
    - note:
        Compile object files in optimized mode
    - rebind:
        - cxxflags: $cxxflags -O3
    - cxx:
        - hello.cpp
        - goodbye.cpp
    - cxxlink:
        - hello
        - goodbye
    ---
    - note:
        Compile GLFW3 examples
    - rebind:
        - libs: -lglfw3 -framework OpenGL -framework GLUT
    - cc:
        - glad.o: deps/glad.c
        - tinycthread.o: deps/tinycthread.c
        - heightmap.c
    - cxx:
        - simple.c
    - cclink:
        - heightmap:
            - heightmap.o
            - glad.o
    - cxxlink:
        - simple
    ...


"""

import os, sys
import yaml
import collections
import argparse

def strip_prefix(filename, prefix):
    abs_filename = os.path.abspath(filename)
    abs_prefix = os.path.abspath(prefix)
    if abs_filename.startswith(abs_prefix):
        i = len(abs_prefix)
        return abs_filename[i+1:]
    return filename

# Make a shorter alias for OrderedDict
Bind = collections.OrderedDict

def parse_yaml(filename):
    docs = []
    # XXX: capture yaml parse errors here
    with open(filename, 'r') as fp:
        for doc in yaml.load_all(fp):
            docs.append(doc)
    return docs

def usage():
    sys.stderr.write("Usage: render-template.py targets.ninja [options] <target.yaml> [...]\n")

def main(argv):

    if len(argv) == 0:
        usage()
        sys.exit(1)

    # list of build instructions (currently unused)
    builds = []

    # list of yaml records, which we'll transform into a list of build instructions
    docs = []

    # default values for these three directories (will be used to strip file prefixes on the source files)
    srcdir = 'src'
    builddir = 'build'
    bindir = 'bin'

    # parse command line options
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs='+', help="list of .yaml build specs, or .c/.cpp source files")
    parser.add_argument("--srcdir", help="location of source directory")
    parser.add_argument("--builddir", help="location of build directory")
    parser.add_argument("--bindir", help="location of bin directory (for linked apps from $buildddir)")
    args = parser.parse_args(argv)

    if args.srcdir:
        srcdir = args.srcdir
        assert os.path.exists(srcdir)

    if args.builddir:
        builddir = args.builddir

    if args.bindir:
        bindir = args.bindir

    # parse the yaml files and whatever else we get in args.files
    for filename in args.files:
        assert os.path.exists(filename)
        root, ext = os.path.splitext(filename)
        if ext == '.yaml':
            docs.extend(doc for doc in parse_yaml(filename))
        elif ext.lower() == '.c':
            obj = '{}.o'.format(root)
            exe = root
            docs.append([{'note': filename}, {'cc': [filename]}, {'cclink': [{exe: obj}]}])
        elif ext.lower() in ('.cc', '.cpp', '.cxx'):
            obj = '{}.o'.format(root)
            exe = root
            docs.append([{'note': filename}, {'cxx': [filename]}, {'cxxlink': [{exe: obj}]}])

    def srcpath(filename):
        filename = strip_prefix(filename, srcdir)
        return '$srcdir/{}'.format(filename)

    def buildpath(filename):
        filename = strip_prefix(filename, builddir)
        return '$builddir/{}'.format(filename)

    def binpath(filename):
        filename = strip_prefix(filename, bindir)
        return '$bindir/{}'.format(filename)

    for doc in docs:
        note = None
        rebind = {}
        rebind_as_str = ''
        print('# ---')
        for stmt in doc:
            #print(stmt)
            if stmt.has_key('note'):
                note = stmt['note'].rstrip().replace('\n','\n# ')
                sys.stdout.write("# {}\n".format(note))
            elif stmt.has_key('rebind'):
                for d in stmt['rebind']:
                    rebind.update(d)
                if rebind:
                    rebind_as_str += '\n'
                    rebind_as_str += '\n'.join('    {} = {}'.format(k,v) for k,v in rebind.items())
            else:
                # assume it's a set of rules...dispatch on the name
                for rule in stmt:
                    build_stmts = stmt[rule]
                    #print rule, build_stmts
                    for build_stmt in build_stmts:
                        #print rule, build_stmt
                        if isinstance(build_stmt, dict):
                            for target in build_stmt:
                                inputs = build_stmt[target]
                                if inputs is None:
                                    # try to deduce it from the rule..
                                    targetbase, ext = os.path.splitext(target)
                                    if rule == 'cc':
                                        input_ext = '.c'
                                    elif rule == 'cxx':
                                        input_ext = '.cpp'
                                    elif rule.endswith('link'):
                                        input_ext = '.o'
                                    inputs = ['{targetbase}{ext}'.format(targetbase=targetbase, ext=input_ext)]
                                elif isinstance(inputs, basestring):
                                    inputs = [inputs]
                                # fix the file paths
                                if rule in ('cc', 'cxx'):
                                    target = buildpath(target)
                                    inputs = [srcpath(f) for f in inputs]
                                elif rule == 'ar':
                                    target = buildpath(target)
                                    inputs = [buildpath(f) for f in inputs]
                                elif rule.endswith('link'):
                                    target = binpath(target)
                                    inputs = [buildpath(f) for f in inputs]
                                # ok, output the rule
                                inputs_as_str = ' '.join(inputs)
                                sys.stdout.write("build {target}: {rule} {inputs}{more}\n".format(
                                    target = target,
                                    rule = rule,
                                    inputs = inputs_as_str,
                                    more = rebind_as_str,
                                ))
                        elif isinstance(build_stmt, basestring):
                            inputs = []
                            if rule in ('cc','cxx'):
                                # in this case, we are given a source file and
                                # want to compile it into an object file..
                                targetbase, ext = os.path.splitext(build_stmt)
                                assert ext.lower() in ('.c', '.cpp', '.cxx', '.cc')
                                target = buildpath("{}.o".format(targetbase))
                                inputs = [srcpath(build_stmt)]
                            elif rule == 'ar':
                                # XXX: simplify this process!
                                if isinstance(build_stmts, dict):
                                    target = buildpath(build_stmt)
                                    inputs = build_stmts[build_stmt]
                                    if isinstance(inputs, basestring):
                                        inputs = [buildpath(inputs)]
                                    elif isinstance(inputs, list):
                                        inputs = [buildpath(f) for f in inputs]
                            elif rule.endswith('link'):
                                # in this case, we are given the name of the
                                # binary, and want to link the
                                target = binpath(build_stmt)
                                inputs = [buildpath("{}.o".format(build_stmt))]
                            inputs_as_str = ' '.join(inputs)
                            sys.stdout.write("build {target}: {rule} {inputs}{more}\n".format(
                                target = target,
                                rule = rule,
                                inputs = inputs_as_str,
                                more = rebind_as_str,
                            ))
    print('# ...')

    # XXX: not currently used (fix this!)
    for build in builds:
        sys.stdout.write('{}\n'.format(build))

    return

if __name__ == '__main__':
    main(sys.argv[1:])

# EOF
