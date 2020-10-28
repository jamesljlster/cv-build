import yaml
import argparse

import os
from os.path import \
    exists, isdir, dirname, join, basename, abspath, splitext

import sys
import docker

from glob import glob

# Package information
pkg_name = 'libopencv4-dev'
pkg_url = 'https://github.com/opencv/opencv.git'
pkg_arch = 'amd64'
pkg_maintainer = 'James Lai <jamesljlster@gmail.com>'
pkg_section = 'universe/libdevel'
pkg_homepage = 'https://opencv.org'
pkg_description = 'development files for opencv'

# Build arguments
cmake_args = {
    'CMAKE_INSTALL_PREFIX': '/usr',
    'WITH_QT': 'ON',
    'WITH_OPENGL': 'ON',
    'BUILD_opencv_python3': 'ON',
    'CMAKE_BUILD_TYPE': 'Release',
    'OPENCV_GENERATE_PKGCONFIG': 'ON'
}


def check_makedirs(path):
    if exists(path):
        if not isdir(path):
            raise FileExistsError(
                '\'%s\' exists and it is not a directory' % path)
    else:
        os.makedirs(path)


def write_script(path, content):
    with open(path, 'w') as f:
        f.write('#!/bin/bash\n')
        for line in content:
            f.write(line + '\n')


if __name__ == '__main__':

    # Resolve working directory
    workDir = dirname(__file__)

    # Resolve available platforms
    platCfgs = glob(join(workDir, 'platform/*.yaml'))
    platList = [splitext(basename(cfg))[0] for cfg in platCfgs]

    # Parse arguments
    argp = argparse.ArgumentParser(
        description='Make OpenCV deb package for Ubuntu')
    argp.add_argument('platform', metavar='platform', type=str, choices=platList,
                      help=('Ubuntu release code name. Available: %s.' %
                            ', '.join(platList)))
    argp.add_argument('version', type=str, help='Target OpenCV version.')

    args = argp.parse_args()

    # Get target OpenCV version
    pkg_ver = args.version

    # Load platform config
    platCfg = yaml.load(
        open(join(workDir, 'platform/%s.yaml' % args.platform), 'r'),
        Loader=yaml.FullLoader
    )

    ct_tag = platCfg['tag']
    build_deps = platCfg['build_deps']
    pkg_deps = platCfg['pkg_deps']

    # Make packaging directory
    pkgDir = join(workDir, pkg_name)
    check_makedirs(pkgDir)

    # Write control file
    check_makedirs(join(pkgDir, 'DEBIAN'))
    with open(join(pkgDir, 'DEBIAN/control'), 'w') as f:
        f.writelines([
            'Package: %s\n' % pkg_name,
            'Version: %s\n' % pkg_ver,
            'Architecture: %s\n' % pkg_arch,
            'Maintainer: %s\n' % pkg_maintainer,
            'Depends: %s\n' % ', '.join(pkg_deps),
            'Section: %s\n' % pkg_section,
            'Homepage: %s\n' % pkg_homepage,
            'Description: %s\n' % pkg_description,
        ])

    # Write scripts for building package
    write_script(
        join(workDir, 'build_package.sh'), [
            'apt install -y ' + ' '.join(build_deps + pkg_deps),
            'git clone --branch %s --depth 1 %s' % (pkg_ver, pkg_url),
            'mkdir build && cd build',
            'cmake %s ../opencv' % (
                ' '.join(['-D%s=%s' % (key, cmake_args[key]) for key in cmake_args])),
            'make -j %d package' % os.cpu_count()
        ]
    )

    write_script(
        join(workDir, 'make_deb.sh'), [
            'tar -xzvf ./build/OpenCV-%s-x86_64.tar.gz -C ./libopencv4-dev' % pkg_ver,
            'mv ./libopencv4-dev/OpenCV-%s-x86_64 ./libopencv4-dev/usr' % pkg_ver,
            ('echo \"Installed-Size: $(du -sh ./libopencv4-dev/usr | cut -f1)\"' +
             ' | tee --append ./libopencv4-dev/DEBIAN/control'),
            'dpkg -b ./libopencv4-dev'
        ]
    )

    # Create build container
    ctWorkDir = join('/root', basename(workDir))
    client = docker.from_env()
    cvBuild = client.containers.run(
        image='ubuntu:%s' % ct_tag,
        name='cv-build',
        hostname='cv-build',
        working_dir='/root',
        volumes={
            abspath(workDir): {
                'bind': ctWorkDir,
                'mode': 'rw'
            }
        },
        environment=['DEBIAN_FRONTEND=noninteractive'],
        entrypoint=join(ctWorkDir, 'make_package.sh'),
        detach=True
    )

    logs = iter(cvBuild.logs(stream=True))
    for log in logs:
        sys.stdout.write(log.decode('utf-8'))

    # Delete container
    cvBuild.wait()
    cvBuild.remove()
