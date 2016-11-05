#!/bin/bash
source /etc/profile

# set -x 
# set -e

source bin/activate && which uwsgi | xargs -i lsof {} | awk '{print $2}' | grep -v PID | xargs -i kill {}
