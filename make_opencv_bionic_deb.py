import os
import sys
import docker

# Repo git url
git_url = 'https://github.com/opencv/opencv.git'

# Package information
pkg_name = 'libopencv4-dev'
pkg_ver = '4.5.0'
pkg_arch = 'amd64'
pkg_maintainer = 'James Lai <jamesljlster@gmail.com>'
pkg_section = 'universe/libdevel'
pkg_homepage = 'https://opencv.org'
pkg_description = 'development files for opencv'

# Dependency
build_deps = ['git', 'make']
pkg_deps = [
    'g++', 'cmake', 'pkg-config', 'qt5-default', 'libdc1394-22-dev',
    'libavcodec-dev', 'libavformat-dev', 'libavutil-dev', 'libswscale-dev',
    'libavresample-dev', 'python3', 'python3-dev', 'python3-numpy',
    'liblapack-dev', 'libeigen3-dev', 'libatlas-base-dev', 'liblapacke-dev'
]

# Build arguments
cmake_args = {
    'CMAKE_INSTALL_PREFIX': '/usr',
    'WITH_QT': 'ON',
    'WITH_OPENGL': 'ON',
    'BUILD_opencv_python3': 'ON',
    'CMAKE_BUILD_TYPE': 'Release',
    'OPENCV_GENERATE_PKGCONFIG': 'ON',
    'OPENCV_DOWNLOAD_PATH': '/tmp/opencv-cache'
}


def check_makedirs(path):
    if os.path.exists(path):
        if not os.path.isdir(path):
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
    workDir = os.path.dirname(__file__)

    # Make packaging directory
    pkgDir = os.path.join(workDir, pkg_name)
    check_makedirs(pkgDir)

    # Write control file
    check_makedirs(os.path.join(pkgDir, 'DEBIAN'))
    with open(os.path.join(pkgDir, 'DEBIAN/control'), 'w') as f:
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
        os.path.join(workDir, 'build_package.sh'), [
            'apt install -y ' + ' '.join(build_deps + pkg_deps),
            'git clone --branch %s --depth 1 %s' % (pkg_ver, git_url),
            'mkdir build && cd build',
            'cmake %s ../opencv' % (
                ' '.join(['-D%s=%s' % (key, cmake_args[key]) for key in cmake_args])),
            'make -j %d package' % os.cpu_count()
        ]
    )

    write_script(
        os.path.join(workDir, 'make_deb.sh'), [
            'tar -xzvf ./build/OpenCV-%s-x86_64.tar.gz -C ./libopencv4-dev' % pkg_ver,
            'mv ./libopencv4-dev/OpenCV-%s-x86_64 ./libopencv4-dev/usr' % pkg_ver,
            ('echo \"Installed-Size: $(du -sh ./libopencv4-dev/usr | cut -f1)\"' +
             ' | tee --append ./libopencv4-dev/DEBIAN/control'),
            'dpkg -b ./libopencv4-dev'
        ]
    )

    # Create build container
    ctWorkDir = os.path.join('/root', os.path.basename(workDir))
    client = docker.from_env()
    cvBuild = client.containers.run(
        image='ubuntu:18.04',
        name='cv-build',
        hostname='cv-build',
        working_dir='/root',
        volumes={
            os.path.abspath(workDir): {
                'bind': ctWorkDir,
                'mode': 'rw'
            }
        },
        environment=['DEBIAN_FRONTEND=noninteractive'],
        entrypoint=os.path.join(ctWorkDir, 'make_package.sh'),
        detach=True
    )

    logs = iter(cvBuild.logs(stream=True))
    for log in logs:
        sys.stdout.write(log.decode('utf-8'))

    # Delete container
    cvBuild.wait()
    cvBuild.remove()
