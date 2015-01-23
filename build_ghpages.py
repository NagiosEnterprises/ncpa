#!/usr/bin/env python

import fileinput
import subprocess
import tempfile
import os

BASEDIR = os.path.dirname(os.path.abspath(__file__))
DOCSDIR = os.path.join(BASEDIR, 'docs')
TEMPDIR = tempfile.gettempdir()


def fie(f):
    def wrapper(*args, **kwargs):
        r = f(*args, **kwargs)
        if r != 0:
            raise Exception('Failed to run function.')
        return r
    return wrapper


@fie
def build_docs():
    os.chdir(DOCSDIR)
    s = subprocess.Popen('make clean', shell=True)
    s.wait()
    r = s.returncode
    s = subprocess.Popen('make html', shell=True)
    s.wait()
    return r | s.returncode


@fie
def move_docs_to_tmp():
    os.chdir(DOCSDIR)
    s = subprocess.Popen('mv %s/_build/html %s/html' % (DOCSDIR, TEMPDIR),
                         shell=True)
    s.wait()
    return s.returncode


@fie
def move_docs_from_tmp():
    os.chdir(BASEDIR)
    s = subprocess.Popen('mv %s/html/* %s' % (TEMPDIR, BASEDIR), shell=True)
    s.wait()
    return s.returncode


@fie
def git_checkout(branch):
    print 'Checking out ' + branch
    os.chdir(BASEDIR)
    s = subprocess.Popen('git checkout %s' % branch, shell=True)
    s.wait()
    return s.returncode


@fie
def git_reset():
    os.chdir(DOCSDIR)
    s = subprocess.Popen('git reset --hard HEAD', shell=True)
    s.wait()
    return s.returncode


@fie
def transfer_master_files():
    os.chdir(BASEDIR)
    s = subprocess.Popen('cp CHANGES.rst docs/changes.rst', shell=True)
    s.wait()
    r = s.returncode
    s = subprocess.Popen('cp NEWS.rst docs/news.rst', shell=True)
    s.wait()
    return r | s.returncode


@fie
def prep_for_github():
    os.chdir(BASEDIR)
    s = subprocess.Popen('touch %s/.nojekyll' % BASEDIR, shell=True)
    s.wait()
    return s.returncode


@fie
def commit():
    os.chdir(BASEDIR)
    s = subprocess.Popen('git add *')
    s.wait()
    r = s.returncode
    s = subprocess.Popen('git commit -a -m "Committing via commitbot"')
    s.wait()
    r |= s.returncode
    s = subprocess.Popen('git push')
    s.wait()
    return r | s.returncode


def alter_rst_index():
    index_rst = os.path.join(DOCSDIR, 'index.rst')
    for line in fileinput.input(index_rst, inplace=True):
        # Currently a hack to insert our news and changes in front of the
        # introduction
        if line.strip().endswith('introduction'):
            print '   news\n   changes'
        print line,


def main():
    git_checkout('master')
    transfer_master_files()
    alter_rst_index()
    build_docs()
    move_docs_to_tmp()
    git_reset()
    git_checkout('gh-pages')
    move_docs_from_tmp()
    prep_for_github()
    commit()


if __name__ == '__main__':
    main()
