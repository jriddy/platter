# -*- coding: utf-8 -*-

"""
Re-Pack `Wheel` to a PYC-Only One

Original Author: https://github.com/tanbro
https://gist.github.com/tanbro/0b624569dcd47ee8c92a2b1cf1d1487a
"""

from __future__ import print_function, unicode_literals

import argparse
import compileall
import ntpath
import os
import shutil
import sys
import zipfile

__version__ = '1.0'

_VARS = {}
_IS_PY2 = bool(sys.version_info[0] < 3)
_PY_TAG = 'py{0[0]}{0[1]}'.format(sys.version_info)


def pack():
    """
    Un-pack original whl, compile all to pyc, then make a new whl
    """
    _args = _VARS['args']
    whl_fname = _args.wheel[0]
    dst_dir = _args.dst
    whl_tmp_dir = whl_bname = ntpath.basename(whl_fname).rsplit('.', 1)[0]

    print('creating {!r} ...'.format(whl_tmp_dir))
    os.mkdir(whl_tmp_dir)
    try:
        print('opening {!r} ...'.format(whl_fname))
        whl_zipfile = zipfile.ZipFile(whl_fname)
        print('extracting {!r} => {!r} ...'.format(whl_fname, whl_tmp_dir))
        whl_zipfile.extractall(whl_tmp_dir)

        for root, dirs, files in os.walk(whl_tmp_dir):
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
            for file_name in files:
                if os.path.splitext(file_name)[1].lower() == '.py':
                    path = os.path.join(root, file_name)
                    print('deleting {!r} ...'.format(path))
                    os.remove(path)

        whl_parts = whl_bname.split('-', 2)
        whl_name = whl_parts[0]
        whl_ver = whl_parts[1]
        whl_tag = whl_parts[2]
        whl_tag_parts = whl_tag.split('-', 2)
        whl_tag_parts[0] = _PY_TAG
        new_whl_tag = '-'.join(whl_tag_parts)

        new_whl_file_name = '{}-{}-{}.whl'.format(
            whl_name, whl_ver, new_whl_tag)
        new_whl_file_path = os.path.join(dst_dir, new_whl_file_name)
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
    parser.add_argument('wheel', nargs=1, type=str, help='*.whl file name')
    parser.add_argument('dst', nargs='?', type=str, default='./',
                        help='New Wheel output directory (default: %(default)s)')
    _VARS['args'] = parser.parse_args()
    pack()


if __name__ == '__main__':
    main()
