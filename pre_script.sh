#!/bin/bash

apt-get update && apt-get install -y tzdata
ln -fs /usr/share/zoneinfo/Asia/Taipei /etc/localtime
dpkg-reconfigure --frontend noninteractive tzdata
