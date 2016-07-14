#!/bin/bash
rsync -av --exclude=.git --exclude='*.swp' --delete . root@192.168.42.1:bsideslv/
