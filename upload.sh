#!/bin/bash
rsync -av --exclude=.git --exclude='*.swp' . root@192.168.42.1:bsideslv/
