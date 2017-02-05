from __future__ import print_function

import os
import subprocess


def invoke(command, work_dir="."):
    if isinstance(command, str):
        command = command.split()

    shell = (os.name == 'nt')  # on windows commands like mvn won't work without shell
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         cwd=work_dir,
                         shell=shell)

    (output_bytes, error_bytes) = p.communicate()

    output = output_bytes.decode("utf-8")
    error = error_bytes.decode("utf-8")

    result_code = p.returncode
    if result_code != 0:
        message = "Execution failed with exit code " + str(result_code)
        print(message)
        print(output)

        if error:
            print(" --- ERRORS ---:")
            print(error)
        raise Exception(message)
        
    if error:
        print("WARN! Error output wasn't empty, although the command finished with code 0!")

    return output
