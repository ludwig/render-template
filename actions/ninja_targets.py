#!/usr/bin/env python
"""
http://martine.github.io/ninja/manual.html#_build_statements
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

    # list of build instructions
    builds = []

    # list of yaml records, which we'll transform into a list of build instructions
    docs = []

    # default values for these three directories (will be used to strip prefix)
    srcdir = 'src'
    builddir = 'build'
    bindir = 'bin'

    # read the yaml files and fill in 'docs'
    if len(argv) == 0:
        usage()
        sys.exit(1)

    # parse options
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

    if False:
        print(strip_prefix('src/foo/bar.c','./src/'))

    if False:
        from pprint import pprint
        pprint(docs)

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

    if False:
        builds = [
            #Build('$builddir/simple.o', 'cxx', ['$srcdir/simple.c'], Bind(srcdir='.',bindir='.')),
            #Build('$bindir/simple', 'cclink', ['$builddir/simple.o']),
            #Build('$bindir/heightmap', 'cclink', ['$builddir/heightmap.o', '$builddir/glad.o'], Bind(libs='-lglfw3 -framework OpenGL -framework GLUT'))
        ]

        # finally, print out the build instructions to stdout
        for build in builds:
            sys.stdout.write('{}\n'.format(build))

if __name__ == '__main__':
    main(sys.argv[1:])

# EOF
