# cv-build

Build OpenCV 4 deb package for ubuntu with docker no matter what environment are you using.

### Requirements

-   python
-   docker
-   python-docker (Docker API for Python)

### Usage

Build OpenCV 4 deb package

```bash
python make_opencv_bionic_deb.py
```

Copy package and install on ubuntu

```bash
sudo apt install --fix-broken ./libopencv4-dev.deb
```
