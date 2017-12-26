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


class FastlaneClient(object):

    def __init__(self, git_dir, ssh_host=None, show_output=False):
        self.show_output = show_output
        self.git_dir = git_dir

        if ssh_host is None:
            host_opts = LocalConnectionOptions(os=OperatingSystemFamily.UNIX)
        else:
            additional_props = ssh_host['connectionProperties']
            host_opts = SshConnectionOptions(ssh_host['address'], ssh_host['username'], password=ssh_host["password"],
                                             privateKeyFile=ssh_host["privateKeyFile"], **additional_props)
        self.host = OverthereHost(host_opts)

    @staticmethod
    def new_instance(git_dir, params, show_output=False):
        return FastlaneClient(git_dir, ssh_host=params["clientHost"], show_output=show_output)


    def run_lane(self, lane, options):
        mdl.println("Checking if '%s' is fastlane enabled" % self.git_dir)
        session = OverthereHostSession(self.host, enable_logging=True, stream_command_output=False)
        with session:
            ot_file = session.remote_file("%s/fastlane/Fastfile" % self.git_dir)
            fastlane_exists = ot_file.exists()

            if not fastlane_exists:
                raise Exception("Fastlane not enabled for '%s'.  Run 'fastlane init' in your repository first." % self.git_dir)

            cmd = ["cd", self.git_dir, ";", "fastlane", lane]
            if options:
                for k in options.keys:
                    cmd.extend(["%s:%s" % (k, options[k])])

            mdl.println("Running lane '%s'" % lane)
            self.execute_cmd(session, cmd)


    def execute_cmd(self, session, cmd_line, show_output=False):
        mdl.println("Executing command line:")
        mdl.print_code(" ".join(cmd_line))
        with session:
            result = session.execute(cmd_line)
            if self.show_output or show_output:
                mdl.println("Output:")
                mdl.print_code("\n".join(result.stdout))
            return result

