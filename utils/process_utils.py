from __future__ import print_function

import os
import subprocess
import sys

import utils.string_utils as string_utils


def invoke(command, work_dir=".", exit_on_failure=False):
    command = prepare_command(command)

    shell = requires_shell()
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         cwd=work_dir,
                         shell=shell)

    (output_bytes, error_bytes) = p.communicate()

    output = output_bytes.decode('utf-8')
    error = error_bytes.decode('utf-8')

    result_code = p.returncode
    if result_code != 0:
        message = 'Execution failed with exit code ' + str(result_code)

        if not exit_on_failure:
            print(message)

        print(string_utils.utf_to_stdout(output))

        if error:
            print(" --- ERRORS ---:")
            print(string_utils.utf_to_stdout(error))

        if exit_on_failure:
            sys.exit(result_code)
        else:
            raise Exception(message)

    if error:
        print("WARN! Error output wasn't empty, although the command finished with code 0!")

    return output


def check_call(command, work_dir="."):
    command = prepare_command(command)

    shell = requires_shell()
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         cwd=work_dir,
                         shell=shell)

    p.communicate()
    result_code = p.returncode

    return result_code == 0


def invoke_attached(command, work_dir="."):
    command = prepare_command(command)

    shell = requires_shell()
    p = subprocess.Popen(command,
                         stderr=subprocess.STDOUT,
                         cwd=work_dir,
                         shell=shell)

    p.communicate()

    result_code = p.returncode
    if result_code != 0:
        sys.exit(result_code)


def requires_shell():
    return os.name == 'nt'  # on windows commands like mvn won't work without shell


def prepare_command(command):
    if isinstance(command, str):
        return command.split()
    return command
