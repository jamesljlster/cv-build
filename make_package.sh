#!/bin/bash

cd `dirname $BASH_SOURCE`
bash pre_script.sh
bash build_package.sh
bash make_deb.sh
