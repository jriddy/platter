# -*- coding: utf-8 -*-

"""
Re-Pack `Wheel` to a PYC-Only One

Original Author: https://github.com/tanbro
https://gist.github.com/tanbro/0b624569dcd47ee8c92a2b1cf1d1487a
"""

from __future__ import print_function, unicode_literals

import argparse
import compileall
import stat
import os
import shutil
import sys
import zipfile

__version__ = '1.0'

_IS_PY2 = bool(sys.version_info[0] < 3)
_PY_TAG = '{0[0]}{0[1]}'.format(sys.version_info)


def _retag_package(basename):
    """Retag the wheel with the python version created.

    Args:
        basename (str): basename of wheel file w/o extension
    Returns:
        (str) new filename

    See https://www.python.org/dev/peps/pep-0427/#file-name-convention
    """
    # TODO: technically can have a "build tag" that messes this algorithm up
    parts = basename.split('-', 2)
    name, ver, tags = parts
    tags_parts = tags.split('-', 2)
    # There could be more tag prefixes than this
    pytypetag = 'cp' if tags_parts[0].startswith('cp') else 'py'
    tags_parts[0] = pytypetag + _PY_TAG
    return '-'.join([name, ver] + tags_parts) + '.whl'


def pack(whl_fname, dst_dir, ensure_executable_scripts=True):
    """
    Un-pack original whl, compile all to pyc, then make a new whl
    """
    whl_tmp_dir = whl_bname = os.path.basename(whl_fname).rsplit('.', 1)[0]

    print('creating {!r} ...'.format(whl_tmp_dir))
    os.mkdir(whl_tmp_dir)
    try:
        print('opening {!r} ...'.format(whl_fname))
        whl_zipfile = zipfile.ZipFile(whl_fname)
        print('extracting {!r} => {!r} ...'.format(whl_fname, whl_tmp_dir))
        whl_zipfile.extractall(whl_tmp_dir)

        for root, dirs, files in os.walk(whl_tmp_dir):
            if ensure_executable_scripts and root.endswith('scripts'):
                for f in files:
                    path = os.path.join(root, f)
                    st = os.stat(path)
                    os.chmod(path, st.st_mode | stat.S_IEXEC)
                continue
            for dir_name in dirs:
                if dir_name == '__pycache__':
                    path = os.path.join(root, dir_name)
                    print('deleting {!r} ...'.format(path))
                    shutil.rmtree(path)
            for file_name in files:
                if os.path.splitext(file_name)[1].lower() in ('.pyc', '.pyo'):
                    path = os.path.join(root, file_name)
                    print('deleting {!r} ...'.format(path))
                    os.remove(path)

        if _IS_PY2:
            compileall.compile_dir(whl_tmp_dir)
        else:
            compileall.compile_dir(whl_tmp_dir, legacy=True)

        for root, dirs, files in os.walk(whl_tmp_dir):
            if ensure_executable_scripts and root.endswith('scripts'):
                continue
            for file_name in files:
                if os.path.splitext(file_name)[1].lower() == '.py':
                    path = os.path.join(root, file_name)
                    print('deleting {!r} ...'.format(path))
                    os.remove(path)

        new_whl_file_name = _retag_package(whl_bname)
        new_whl_file_path = os.path.join(dst_dir, new_whl_file_name)
        if not os.path.isdir(dst_dir):
            os.makedirs(dst_dir)
        if os.path.isfile(new_whl_file_path):
            print('deleting {!r} ...'.format(new_whl_file_path))
            os.remove(new_whl_file_path)
        print('creating {!r} ...'.format(new_whl_file_path))
        new_zip_file = zipfile.ZipFile(new_whl_file_path, 'w')
        for root, dirs, files in os.walk(whl_tmp_dir):
            rel_root = root.lstrip(whl_tmp_dir)
            for file_name in files:
                srcname = os.path.join(root, file_name)
                arcname = os.path.join(rel_root, file_name)
                print('adding {!r} -> {!r} ...'.format(srcname, arcname))
                new_zip_file.write(srcname, arcname)

    finally:
        print('deleting {!r} ...'.format(whl_tmp_dir))
        shutil.rmtree(whl_tmp_dir)


def pack_all(wheel_files, dst_dir):
    for w in wheel_files:
        pack(w, dst_dir)


def main():
    """
    Main function
    """
    # parsing program arguments
    parser = argparse.ArgumentParser(
        description='This program Re-Pack a Python Wheel to a PYC-Only One'
    )
    parser.add_argument('--version', action='version',
                        version='%(prog)s {}'.format(__version__))
    parser.add_argument('--dst', nargs='?', type=str, default='dist',
                        help='New Wheel output directory (default: %(default)s)')
    parser.add_argument('wheels', nargs='+', type=str, help='*.whl file name')
    args = parser.parse_args()
    pack_all(args.wheels, args.dst)


if __name__ == '__main__':
    main()
