import argparse
import semver
import subprocess


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'release_type',
        choices=['major', 'minor', 'patch']
    )
    return parser.parse_args()


def read_version(path):
    with open(path) as f:
        return f.read()


def increment_version(version, release_type):
    if release_type == 'major':
        return semver.bump_major(version)
    elif release_type == 'minor':
        return semver.bump_minor(version)
    return semver.bump_patch(version)


def write_version(path, version):
    with open(path, 'w') as f:
        f.write(version + '\n')


def git_tag(version):
    subprocess.call(['git', 'tag', 'v' + version])


def git_push():
    subprocess.call(['git', 'push', '--tags'])


def git_commit(version):
    subprocess.call(['git', 'add', 'version.txt'])
    subprocess.call(['git', 'commit', '-m', 'bump version to ' + version])


def run(release_type):
    version = read_version('version.txt')
    new_version = increment_version(version, release_type)
    write_version('version.txt', new_version)
    git_commit(new_version)
    git_tag(new_version)
    git_push()


if __name__ == '__main__':
    args = parse_args()
    run(**vars(args))
