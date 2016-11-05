#!/usr/bin/env python2
"""This program is used to validation the thrift definition for a table."""

import os
import shutil
import subprocess
import tempfile

## Change these settings as needed
THRIFT_BIN = "/usr/local/bin/thrift"
DEFAULT_PUBLIC_THRIFT_ROOT = "/home/wzh/code/xiaomi-commons-java/xiaomi-common-logger/src/main/thrift/"

def to_camel_case(name):
    """Change identifiers from c style (underscore separated words) to Java style (camel case)

    For example:
    `this_is_word`, `_this_is_word`, `__this_is_word`, `this__is_word`,`this_is_word_`
    will all be changed into `ThisIsWord`
    """
    words = name.split('_')
    capitalized_words = [word.capitalize() for word in words if len(word) > 0]
    return "".join(capitalized_words)

def get_path_and_name(table):
    parts = table.split('/')
    assert len(parts) == 2, "Illegal table parameter"
    return parts[0], parts[1]

def get_public_thrift_root():
    public_thrift_root = os.getenv("PUBLIC_THRIFT_ROOT")
    if (public_thrift_root is None):
        return DEFAULT_PUBLIC_THRIFT_ROOT
    else:
        return public_thrift_root

def check_thrift(table, thrift):
    """ Check validation of the thrift definition for table.

    returns (error_code, error_message)
    """

    (table_path, table_name) = get_path_and_name(table)
    clzName = to_camel_case(table_name)

    error_code = 0
    error_message = ""
    compile_path = tempfile.mkdtemp(prefix = "gen")
    clzPath = "{}/gen-java/com/xiaomi/common/logger/thrift/{}/{}.java" \
        .format(compile_path, table_path, clzName)
    public_thrift_root = get_public_thrift_root()

    try:
        cmdline = "{} -o {} --gen java -I {} {} && test -f {}" \
            .format(THRIFT_BIN, compile_path, public_thrift_root, thrift, clzPath)
        subprocess.check_output(cmdline, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        error_code = e.returncode
        error_message = e.output
        if (len(error_message) == 0):
            error_message = "Top level definition donot exists: {}".format(clzPath)
    finally:
        shutil.rmtree(compile_path)

    return error_code, error_message

# entry point if used as a script.
if __name__ == '__main__':
    import sys
    if (len(sys.argv) != 3):
        print("Usage: {} table_path/table_name thrift_definition".format(sys.argv[0]))
        sys.exit(1)

    (error_code, error_message) = check_thrift(sys.argv[1], sys.argv[2])

    if (len(error_message) > 0):
        print("Error message: {}".format(error_message))
    sys.exit(error_code)