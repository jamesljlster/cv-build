#!/bin/bash

apt-get update && apt-get install --no-install-recommends -y tzdata openssl ca-certificates
ln -fs /usr/share/zoneinfo/Asia/Taipei /etc/localtime
dpkg-reconfigure --frontend noninteractive tzdata
