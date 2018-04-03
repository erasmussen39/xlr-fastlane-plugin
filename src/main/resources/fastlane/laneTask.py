#
# THIS CODE AND INFORMATION ARE PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR FITNESS
# FOR A PARTICULAR PURPOSE. THIS CODE AND INFORMATION ARE NOT SUPPORTED BY XEBIALABS.
#

from fastlane.git_client import GitClient
from fastlane.fastlane_client import FastlaneClient


def process(task_vars):
    git = GitClient.new_instance(task_vars)

    if task_vars["gitCloneUrl"]:
        git.fetch_repo()

    if task_vars["gitBranch"]:
        git.checkout(task_vars["gitBranch"])

    fastlane = FastlaneClient.new_instance(git.git_dir, task_vars)
    fastlane.run_lane(task_vars["lane"], task_vars["options"])


if __name__ == '__main__' or __name__ == '__builtin__':
    process(locals())
