#!/bin/bash
rsync -av --exclude=.git . root@192.168.42.1:bsideslv/
