import os
import re

import utils.process_utils as process_utils


class GitGateway():
    def get_local_changed_files(self, abs_path, ignore_unversioned=True):
        result = set()

        status_info = process_utils.invoke(['git', 'status', '-s'], abs_path, ['?'])
        if ignore_unversioned:
            changed_files = self.parse_changed_files(status_info, abs_path, ['?'])
        else:
            changed_files = self.parse_changed_files(status_info, abs_path)

        result.update(changed_files)

        return list(result)

    def parse_changed_files(self, diff_info, abs_path, ignored_statuses=None):
        result = []

        lines = diff_info.split('\n')
        for line in lines:
            file_info = re.split(r'\s+', line.strip(), 1)

            if len(file_info) != 2:
                continue

            if ignored_statuses:
                status = file_info[0]
                suitable = False

                for singe_status in status:
                    if singe_status not in ignored_statuses:
                        suitable = True
                        break

                if not suitable:
                    continue

            file_path = file_info[1]

            result.append(os.path.join(abs_path, file_path))

        return result

    def get_revision_changed_files(self, abs_path, from_revision, to_revision):
        diff_info = process_utils.invoke(
            ['git', 'diff', '--name-status', from_revision, to_revision], abs_path)

        return self.parse_changed_files(diff_info, abs_path)

    def get_revision(self, project_path):
        return process_utils.invoke(['git', 'rev-parse', 'HEAD'], project_path).strip()


def is_git_repo(project_path):
    git_files_path = os.path.join(project_path, '.git')
    return os.path.isdir(git_files_path) or process_utils.check_call('git rev-parse --git-dir', project_path)
