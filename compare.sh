#!/bin/bash
python3 cfg_orig.py $1 && python3 ./cfg.py $1
open -a "Sublime Text" $1