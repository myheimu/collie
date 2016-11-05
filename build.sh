#!/bin/bash

# 部署系统会将项目在部署系统中的名字作为第一个参数传递给 build.sh
job_name=$1
service_group=$(echo $job_name | sed -n 's/.*\.\([^.]*\)_cluster.*/\1/p')
cluster=$(echo $job_name |sed -n 's/.*_cluster\.\([^._]*\)_.*/\1/p')

rm -rf release/*
rsync -rv --exclude=release --exclude=.git --exclude=*.pyc . release
pushd release/settings
echo "service_group is "$service_group
mv 'settings_'$service_group'.py' settings.py
popd
cp -r deploy release/