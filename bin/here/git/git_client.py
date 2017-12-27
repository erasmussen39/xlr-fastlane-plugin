#
# Copyright 2018 XEBIALABS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import os
from here.xlr.overthere import LocalConnectionOptions, OverthereHost, OverthereHostSession, SshConnectionOptions
from com.xebialabs.overthere import OperatingSystemFamily
from here.xlr.markdown_logger import MarkdownLogger as mdl
from here.git.logs import parser
import json


class GitClient(object):

    def __init__(self, clone_url, repo_base_dir, tag_prefix, ssh_host=None, show_output=False):
        self.show_output = show_output
        self.tag_prefix = tag_prefix
        self.repo_base_dir = repo_base_dir
        if not repo_base_dir.startswith("/"):
            self.repo_base_dir = "%s/%s" % (os.getcwd(), repo_base_dir)
        self.clone_url = clone_url
        clone_url_parts = clone_url.split('/')
        self.repo_name = clone_url_parts[len(clone_url_parts) - 1]
        self.git_dir = "%s/%s" % (self.repo_base_dir, self.repo_name)
        if ssh_host is None:
            mdl.println("SSH Host not configured.  Using local connection option.")
            host_opts = LocalConnectionOptions(os=OperatingSystemFamily.UNIX)
        else:
            mdl.println("Using SSH Host %s" % ssh_host['address'])
            additional_props = ssh_host['connectionProperties']
            host_opts = SshConnectionOptions(ssh_host['address'], ssh_host['username'], password=ssh_host["password"],
                                             privateKeyFile=ssh_host["privateKeyFile"], **additional_props)
        self.host = OverthereHost(host_opts)

    @staticmethod
    def new_instance(params, show_output=False):
        tag_prefix = ""
        if "tagPrefix" in params.keys():
            tag_prefix = params["tagPrefix"]
        return GitClient(params["gitCloneUrl"], params["gitRepoBaseDir"], tag_prefix,
                         ssh_host=params["clientHost"], show_output=show_output)

    @staticmethod
    def pretty_print_json(dump_obj):
        print json.dumps(dump_obj, sort_keys=True, indent=4, separators=(',', ': '))

    def _parse_log_for_tag(self, log_entry):
        # format of output is "(tag: TR-1383-16)"
        tag = log_entry.strip().split(":")[1].strip()
        return tag[:len(tag)-2]

    def list_commits_between_commit_and__last_tag(self, start_commit_id):
        session = OverthereHostSession(self.host, enable_logging=True)
        with session:
            self.execute_cmd(session, ["cd", self.git_dir])

            known_tags = self.execute_cmd(session, ["git", "log", "--tags", "--simplify-by-decoration", '--pretty="%d"'])
            known_tags = [self._parse_log_for_tag(kt) for kt in known_tags]
            tags = [t for t in known_tags if t.startswith(self.tag_prefix)]
            if len(tags) == 0:
                raise Exception("No tags found matching prefix '%s'. Known tags %s" % (self.tag_prefix, known_tags))

            end_tag = tags[0]
            mdl.println(end_tag)

            commits = self.execute_cmd(session, ["git", "log", "--pretty=raw", "%s...%s" % (start_commit_id, end_tag)])
            if commits:
                # note the parser cannot handle 'gpgsig' signatures in commits
                return list(parser.parse_commits("\n".join(commits)))
            return []

    def tag_commit(self, commit_id, tag_name, push):
        mdl.println("Tagging commit '%s' with tag '%s'" % (commit_id, tag_name))
        session = OverthereHostSession(self.host, enable_logging=True)
        with session:
            self.execute_cmd(session, ["cd", self.git_dir])
            self.execute_cmd(session, ["git", "tag", tag_name, commit_id], show_output=True)
            if push:
                mdl.println("Pushing tag")
                self.execute_cmd(session, ["git", "push", "--tags"], show_output=True)

    def checkout(self, branch):
        session = OverthereHostSession(self.host, enable_logging=True)
        with session:
            mdl.println("Checking out '%s'" % branch)
            self.execute_cmd(session, ["cd", self.git_dir, "&&", "git", "checkout", branch])
        
    def fetch_repo(self):
        mdl.println("Checking if '%s' exists in dir '%s'" % (self.repo_name, self.git_dir))
        session = OverthereHostSession(self.host, enable_logging=True)
        with session:
            ot_file = session.remote_file(self.git_dir)
            dir_exists = ot_file.exists()

            if dir_exists:
                mdl.println("Already cloned. Pulling latest changes")
                self.execute_cmd(session, ["cd", self.git_dir, "&&", "git", "pull"])
            else:
                mdl.println("Cloning to '%s'" % self.git_dir)
                self.execute_cmd(session, ["git", "clone", self.clone_url, self.git_dir])

    def execute_cmd(self, session, cmd_line, show_output=False):
        mdl.println("Executing command line:")
        mdl.print_code(" ".join(cmd_line))

        result = session.execute(cmd_line)
        if self.show_output or show_output:
            mdl.println("Output:")
            mdl.print_code("\n".join(result.stdout))
        return result


