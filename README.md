# cv-build

Build OpenCV 4 deb package for ubuntu with docker no matter what environment are you using.

### Requirements

-   python
-   docker
-   python-docker (Docker API for Python)

### Usage

Build OpenCV 4 deb package

```bash
python make_opencv_deb.py ubuntu_code_name opencv_version
```

For example:

```bash
python make_opencv_deb.py bionic 4.5.0
```

Copy package and install on ubuntu.  
For example:

```bash
sudo apt install --fix-broken ./libopencv4-4.5.0-dev.deb
```

### TODO

-   Script error handling
-   Ctrl-C handling
    -   Stop and remove container

### Planing

-   APT Repository
-   Package name generator (required by APT repository)
