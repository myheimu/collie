#!/bin/bash

# check variable value is not empty
set -u
# check each command return code is correct
set -e

project_path=
service_name=
table_name=
file_content=

while test $# -gt 0; do
    case "$1" in 
	-h|--help)
	    shift
	    echo " - TODO"
	    echo " "
	    echo " [options] "
	    echo " "
	    echo "options:"
	    echo "-p, --project-path    specify thrift log project path"
	    echo "-..."
	    ;;
	-p|--project-path)
	    shift
	    if test $# -gt 0; then
		project_path=$1
	    else
		echo "no project-path specified"
		exit 1
	    fi
	    shift
	    ;;
	-s|--service-name)
	    shift
	    if test $# -gt 0; then
		service_name=$1
	    else
		echo "no service-name specified"
		exit 1
	    fi
	    shift
	    ;;		
	-t|--table-name)
	    shift
	    if test $# -gt 0; then
		table_name=$1
	    else
		echo "no table-name specified"
		exit 1
	    fi
	    shift
	    ;;
	-f|--file-content)
	    shift
	    if test $# -gt 0; then
		file_content=$1
	    else
		echo "no file-content specified"
		exit 1
	    fi
	    shift
	    ;;
	*)
	    break
	    ;;
    esac
done

# save thrift file
pushd $project_path
file_path="src/main/thrift/${service_name}/${table_name}Table.thrift"
touch $file_path
printf "$file_content" > $file_path
git pull
git add .
git commit -a -m "create table $table_name"
git push
mvn --batch-mode release:prepare
mvn release:perform
git pull
popd


