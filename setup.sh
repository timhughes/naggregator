#! /bin/sh
#
# setup.sh
# Copyright (C) 2015 Tim Hughes <thughes@thegoldfish.org>
#
# Distributed under terms of the MIT license.
#



mkdir /opt/naggregator
cp -r ./src/ /opt/naggregator/
virtualenv /opt/naggregator/
/opt/naggregator/bin/pip install -r requirements.txt
ln /opt/naggregator/naggregator.service /etc/systemd/system/

