from setuptools import setup
from scripts.release import read_version

version = read_version('version.txt')
url = 'https://github.com/suned/serum/archive/{}.tar.gz'.format('v' + version)


def readme():
    with open('README.md') as f:
        return f.read()


setup(
  name='serum',
  packages=['serum'],
  version=version,
  description='Dependency Injection library for Python 3',
  long_description=readme(),
  long_description_content_type='text/markdown',
  author='Sune Debel',
  license='MIT',
  author_email='sd@dybro-debel.dk',
  python_requires='>=3.5',
  url='https://github.com/suned/serum',
  download_url=url,
  keywords=['dependency-injection', 'solid', 'inversion-of-control'],
  classifiers=[],
)
