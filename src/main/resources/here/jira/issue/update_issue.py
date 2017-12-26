#
# Copyright 2018 XEBIALABS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

from here.xlr.markdown_logger import MarkdownLogger as mdl
from here.jira.jira_client import JiraClient
from jira import JiraServer  # From the default XLR Jira plugin


def process(task_vars):
    new_status = task_vars["newStatus"]
    comment = task_vars["comment"]
    issue_id = task_vars["issueId"]
    if new_status or comment:
        default_jira = JiraServer(task_vars["jiraServer"], task_vars["username"], task_vars["password"])
        default_jira.updateIssue(issue_id, new_status, comment)

    assignee = task_vars["assignee"]
    additional_fields = task_vars["additionalFields"]
    if assignee or len(additional_fields.keys()) > 0:
        extended_jira = JiraClient.new_instance(task_vars)
        extended_jira.update_issue(issue_id, assignee, additional_fields)

    mdl.print_link(issue_id, "%s/browse/%s" % (task_vars["jiraServer"]['url'], issue_id), "Updated issue")


if __name__ == '__main__' or __name__ == '__builtin__':
    process(locals())
