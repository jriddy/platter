import os
import sys
import tarfile
from contextlib import contextmanager

import pytest
from click.testing import CliRunner

import platter

try:
    from unittest import mock
except ImportError:
    import mock

TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), 'files')
# https://github.com/pypa/virtualenv/tree/master/virtualenv_support
SUPPORT_WHEELS = ['pip', 'setuptools', 'wheel', 'argparse']

@contextmanager
def cwd(path):
    prev_dir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_dir)


def test_end_to_end(tmpdir):
    runner = CliRunner()
    result = runner.invoke(
        platter.build_cmd,
        ['--output={}'.format(tmpdir.strpath),
         '--postbuild-script={}'.format(
             os.path.join(TEST_FILES_DIR, 'postbuild.sh'))])
    assert result.exit_code == 0
    files = tmpdir.listdir()
    assert len(files) == 1
    assert files[0].fnmatch('platter-*.tar.gz')
    with files[0].open('rb') as f:
        tf = tarfile.open(fileobj=f)
        members = tf.getmembers()
        wheels = [f.split('/')[-1].split('-')[0] for f in tf.getnames()
                  if f.endswith('.whl')]

    pkg_wheels = ['platter', 'pytoml', 'click']
    assert set(SUPPORT_WHEELS + pkg_wheels) == set(wheels)

    install_member = None
    postbuild_member = None
    for m in members:
        if os.path.basename(m.name) == 'install.sh':
            install_member = m
        if os.path.basename(m.name) == 'postbuild_ran':
            postbuild_member = m
    assert install_member
    assert install_member.mode == 0o0755
    assert postbuild_member
    assert postbuild_member.name.split(os.sep)[-2] == 'data'


def test_pipenv(tmpdir):
    pytest.importorskip('pipenv')
    runner = CliRunner()
    result = runner.invoke(
        platter.build_cmd,
        ['--output={}'.format(tmpdir.strpath),
         os.path.join(TEST_FILES_DIR, 'pipenv')])
    print(result.output)
    assert result.exit_code == 0
    assert "Pipfile.lock detected." in result.output
    files = tmpdir.listdir()
    assert len(files) == 1
    assert files[0].fnmatch('dummy-*.tar.gz')
    with files[0].open('rb') as f:
        tf = tarfile.open(fileobj=f)
        wheels = [f.split('/')[-1].split('-')[0] for f in tf.getnames()
                  if f.endswith('.whl')]

    pkg_wheels = ['dummy', 'pep8']
    assert set(SUPPORT_WHEELS + pkg_wheels) == set(wheels)


@mock.patch.object(platter.Builder, '__init__')
def test_pyproject(mocked_builder):
    runner = CliRunner()
    runner.invoke(platter.build_cmd, [TEST_FILES_DIR])
    assert mocked_builder.call_count == 1
    assert mocked_builder.call_args[1]['python'] == 'python3.7'


def test_multiline_toml():
    ctx = platter.build_cmd.make_context('build', args=[])
    conf = platter.get_opts_from_pyproject(ctx, TEST_FILES_DIR)
    assert len(conf['postbuild_script'].splitlines()) == 2


def test_bad_path(tmpdir):
    bad_path = tmpdir.join('does-not-exist').strpath
    runner = CliRunner()
    result = runner.invoke(platter.build_cmd, [bad_path])
    assert result.exit_code != 0
    err_msg = "The project path ({}) does not exist".format(bad_path)
    assert err_msg in result.output

def test_bad_script(tmpdir):
    runner = CliRunner()
    result = runner.invoke(
        platter.build_cmd,
        ['--output={}'.format(tmpdir.strpath),
         '--prebuild-script={}'.format(tmpdir.join('nope.sh').strpath)])
    assert result.exit_code != 0
    assert "Build script failed" in result.output

def test_clean_cache(tmpdir):
    test_file = tmpdir.ensure('test.whl')
    assert test_file.exists()
    runner = CliRunner()
    result = runner.invoke(platter.clean_cache_cmd,
                           ['--wheel-cache={}'.format(tmpdir.strpath)])
    assert result.exit_code == 0
    assert test_file.exists() is False
