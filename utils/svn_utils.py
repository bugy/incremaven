import os

import utils.process_utils as process_utils
import utils.xml_utils as xml_utils


class SvnGateway():
    def get_local_changed_files(self, abs_path, ignore_unversioned=True):
        status_info = process_utils.invoke(['svn', 'status', '--xml', abs_path])

        entries_xpath = '*/entry'
        found_results = xml_utils.find_in_string(status_info, [entries_xpath])
        entries = found_results[entries_xpath]

        return self.svn_xml_status_to_files(entries, abs_path, ignore_unversioned)

    def svn_status_to_files(self, all_lines):
        result = []

        for line in all_lines:
            if os.name != 'nt':
                if not ('/' in line):
                    continue
                file_path = line[line.index("/"):]

            else:
                if not ('\\' in line):
                    continue
                file_path = line[line.index(':\\') - 1:]

            result.append(file_path)

        return result

    def svn_xml_status_to_files(self, found_entries, abs_path, ignore_unversioned=True):
        result = []

        if found_entries:
            if not isinstance(found_entries, list):
                found_entries = [found_entries]

            for entry in found_entries:
                status_info = entry['wc-status']
                status = status_info['item']

                if ignore_unversioned and (status == 'unversioned'):
                    continue

                path = entry['path']

                if status in ['normal', 'modified']:
                    full_path = os.path.join(abs_path, path)
                    if os.path.isdir(full_path):
                        continue

                result.append(path)

        return result

    def svn_xml_diff_to_files(self, paths, abs_path):
        result = []

        if paths:
            if not isinstance(paths, list):
                paths = [paths]

            for path in paths:
                status = path['item']
                path = path['text']

                if status in ['none', 'modified']:
                    full_path = os.path.join(abs_path, path)
                    if os.path.isdir(full_path):
                        continue

                result.append(path)

        return result

    def get_revision_changed_files(self, abs_path, from_revision, to_revision):
        status_info = process_utils.invoke(
            ['svn', 'diff', '--summarize', '--xml', '-r' + from_revision + ':' + to_revision, abs_path])

        entries_xpath = '*/path'
        found_results = xml_utils.find_in_string(status_info, [entries_xpath])
        entries = found_results[entries_xpath]

        return self.svn_xml_diff_to_files(entries, abs_path)

    def get_revision(self, project_path):
        svn_info = process_utils.invoke(['svn', 'info', project_path])
        info_lines = svn_info.split('\n')

        revision_prefix = 'Revision: '

        for line in info_lines:
            if line.startswith(revision_prefix):
                return line[len(revision_prefix):]

        raise Exception("Couldn't get svn revision in " + project_path)


def is_svn_repo(path):
    return process_utils.check_call('svn info', path)
