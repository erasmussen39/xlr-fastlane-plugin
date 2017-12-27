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

from fastlane.overthere import LocalConnectionOptions, OverthereHost, OverthereHostSession, SshConnectionOptions
from com.xebialabs.overthere import OperatingSystemFamily
from fastlane.markdown_logger import MarkdownLogger as mdl


class GitClient(object):

    def __init__(self, clone_url, repo_base_dir, ssh_host=None, show_output=False):
        self.show_output = show_output
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
        return GitClient(params["gitCloneUrl"], params["gitRepoBaseDir"], ssh_host=params["clientHost"], show_output=show_output)


    def checkout(self, branch):
        session = OverthereHostSession(self.host, enable_logging=True)
        with session:
            mdl.println("Checking out '%s'" % branch)
            session.execute_cmd(["cd", self.git_dir, "&&", "git", "checkout", branch])
        

    def fetch_repo(self):
        mdl.println("Checking if '%s' exists in dir '%s'" % (self.repo_name, self.git_dir))
        session = OverthereHostSession(self.host, enable_logging=True)
        with session:
            ot_file = session.remote_file(self.git_dir)
            dir_exists = ot_file.exists()

            if dir_exists:
                mdl.println("Already cloned. Pulling latest changes")
                session.execute_cmd(["cd", self.git_dir, "&&", "git", "pull"])
            else:
                mdl.println("Cloning to '%s'" % self.git_dir)
                session.execute_cmd(["git", "clone", self.clone_url, self.git_dir])
