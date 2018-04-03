#
# THIS CODE AND INFORMATION ARE PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR FITNESS
# FOR A PARTICULAR PURPOSE. THIS CODE AND INFORMATION ARE NOT SUPPORTED BY XEBIALABS.
#

import os

from fastlane.overthere import LocalConnectionOptions, OverthereHost, OverthereHostSession, SshConnectionOptions
from com.xebialabs.overthere import OperatingSystemFamily
from fastlane.markdown_logger import MarkdownLogger as mdl


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
        mdl.println("Beginning lane '%s'" % lane)
        session = OverthereHostSession(self.host, enable_logging=True, stream_command_output=False)
        with session:
            mdl.println("Checking if '%s' is fastlane enabled" % self.git_dir)
            ot_file = session.remote_file("%s/fastlane/Fastfile" % self.git_dir)
            fastlane_exists = ot_file.exists()

            if not fastlane_exists:
                raise Exception("fastlane not enabled for '%s'.  Run 'fastlane init' in your repository first." % self.git_dir)

            cmd = ["cd", self.git_dir, "&&", "fastlane", "--capture_output", lane]
            if options:
                for k in options.keys:
                    cmd.extend("%s:%s" % (k, options[k]))

            session.execute_cmd(cmd, show_output=False)
