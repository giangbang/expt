"""setup.py for expt"""

import ast
import os
import shutil
import sys
import textwrap

from setuptools import Command
from setuptools import setup

try:
  from setuptools_rust import Binding
  from setuptools_rust import build_rust
  from setuptools_rust import RustExtension
  from setuptools_rust.command import get_rust_version
except ImportError:
  sys.stderr.write(textwrap.dedent(
      """\
          Error: setuptools_rust cannot be imported.
          Runnig setup.py like `python setup.py` is deprecated.

          Please run `pip install .` or `pip install -e .[test]` instead.
      """))  # yapf: disable  # noqa
  sys.exit(1)

__PATH__ = os.path.abspath(os.path.dirname(__file__))

EXPT_DISABLE_RUST = ast.literal_eval(os.getenv("EXPT_DISABLE_RUST") or "False")


class build_rust_for_expt(build_rust):

  def run(self):
    if not EXPT_DISABLE_RUST and get_rust_version() is None:
      from distutils.errors import DistutilsPlatformError
      raise DistutilsPlatformError(
          "Rust toolchain (cargo, rustc) not found. "
          "Please install rust toolchain to build expt with the rust extension. "
          "If you would like to build expt without the extension, "
          "export EXPT_DISABLE_RUST=1 and try again.")
    return super().run()


def read_readme():
  with open('README.md', encoding='utf-8') as f:
    return f.read()


try:
  import setuptools_scm
except ImportError as ex:
  raise ImportError("setuptools_scm not found. When running setup.py directly, "
                    "setuptools_scm needs to be installed manually. "
                    "Or consider running `pip install -e .` instead.") from ex


def read_version():
  return setuptools_scm.get_version()


__version__ = read_version()


# brought from https://github.com/kennethreitz/setup.py
class DeployCommand(Command):
  description = 'Build and deploy the package to PyPI.'
  user_options = []

  def initialize_options(self):
    pass

  def finalize_options(self):
    pass

  @staticmethod
  def status(s):
    print(s)

  def run(self):
    import twine  # we require twine locally  # noqa

    assert 'dev' not in __version__, ("Only non-devel versions are allowed. "
                                      "__version__ == {}".format(__version__))

    with os.popen("git status --short") as fp:
      git_status = fp.read().strip()
      if git_status:
        print("Error: git repository is not clean.\n")
        os.system("git status --short")
        sys.exit(1)

    try:
      self.status('Removing previous builds ...')
      shutil.rmtree(os.path.join(__PATH__, 'dist'))
    except OSError:
      pass

    self.status('Building Source and Wheel (universal) distribution ...')
    os.system('{0} setup.py sdist'.format(sys.executable))

    self.status('Uploading the package to PyPI via Twine ...')
    ret = os.system('twine upload dist/*')
    if ret != 0:
      sys.exit(ret)

    self.status('Creating git tags ...')
    os.system('git tag v{0}'.format(__version__))
    os.system('git tag --list')
    sys.exit()


install_requires = [
    'numpy>=1.16.5',
    'scipy',
    'typeguard>=2.6.1',
    'matplotlib>=3.0.0',
    'pandas>=1.3',
    'pyyaml>=6.0',
    'multiprocess>=0.70.12',
    'multiprocessing_utils==0.4',
    'typing_extensions>=4.0',
]

tests_requires = [
    'setuptools-rust',
    'mock>=2.0.0',
    'pytest>=7.0',
    'pytest-cov',
    'pytest-asyncio',
    # Optional dependencies.
    'tensorboard>=2.3',
    'fabric~=2.6',
    'paramiko>=2.8',
]


def next_semver(version: setuptools_scm.version.ScmVersion):
  """Determine next development version."""

  if version.branch and 'release' in version.branch:
    # Release branch: bump up patch versions
    return version.format_next_version(
        setuptools_scm.version.guess_next_simple_semver,
        retain=setuptools_scm.version.SEMVER_PATCH)
  else:
    # main/dev branch: bump up minor versions
    return version.format_next_version(
        setuptools_scm.version.guess_next_simple_semver,
        retain=setuptools_scm.version.SEMVER_MINOR)


setup(
    name='expt',
    version=__version__,
    use_scm_version=dict(
        write_to='expt/_version.py',
        version_scheme=next_semver,
    ),
    license='MIT',
    description='EXperiment. Plot. Tabulate.',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/wookayin/expt',
    author='Jongwook Choi',
    author_email='wookayin@gmail.com',
    #keywords='',
    classifiers=[
        # https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Utilities',
        'Topic :: Scientific/Engineering',
    ],
    packages=['expt'],
    rust_extensions=[
        RustExtension("expt._internal", binding=Binding.PyO3, \
                      debug=False  # Always use --release (optimized) build
                      ),
    ] if not EXPT_DISABLE_RUST else [],
    install_requires=install_requires,
    extras_require={'test': tests_requires},
    setup_requires=['setuptools-rust'],
    tests_require=tests_requires,
    entry_points={
        #'console_scripts': ['expt=expt:main'],
    },
    cmdclass={
        'deploy': DeployCommand,
        'build_rust': build_rust_for_expt,
    },  # type: ignore
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3.7',
)
