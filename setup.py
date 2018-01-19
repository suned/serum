from setuptools import setup
from scripts.release import read_version

version = read_version('version.txt')
url = 'https://github.com/suned/serum/archive/{}.tar.gz'.format('v' + version)
setup(
  name='serum',
  packages=['serum'],
  version=version,
  description='Dependency Injection library for Python 3',
  author='Sune Debel',
  license='MIT',
  author_email='sd@dybro-debel.dk',
  python_requires='>=3.5',
  url='https://github.com/suned/serum',
  download_url=url,
  keywords=['dependency-injection', 'solid', 'inversion-of-control'],
  classifiers=[],
)
