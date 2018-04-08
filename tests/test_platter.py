import os
import tarfile
from click.testing import CliRunner
import platter


def test_end_to_end(tmpdir):
    test_dir = os.path.dirname(__file__)
    runner = CliRunner()
    result = runner.invoke(platter.build_cmd,
                           ['--output={}'.format(tmpdir),
                            '--postbuild-script={}'.format(os.path.join(test_dir,
                                                                   'postbuild.sh'))])
    assert result.exit_code == 0
    files = tmpdir.listdir()
    assert len(files) == 1
    assert files[0].fnmatch('platter-*.tar.gz')
    with files[0].open('rb') as f:
        tf = tarfile.open(fileobj=f)
        members = tf.getmembers()
        # TODO: why are multiple versions of wheel and setuptools are included?
        wheels = [f.split('/')[-1].split('-')[0] for f in tf.getnames()
                  if f.endswith('.whl')]

    platter_wheels = ['platter', 'pytoml', 'click', 'argparse']
    python_wheels = ['pip', 'setuptools', 'wheel']
    assert set(python_wheels + platter_wheels) == set(wheels)

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





