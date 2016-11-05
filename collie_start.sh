#!/bin/bash
source /etc/profile

# set -x 
# set -e

source bin/activate && uwsgi -x django_socket.xml 
