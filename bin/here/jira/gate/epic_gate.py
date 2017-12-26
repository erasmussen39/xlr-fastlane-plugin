#
# Copyright 2018 XEBIALABS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

from here.jira.gate import handle_sleep, process_gate
import here.xlr.xlr_helper
reload(here.xlr.xlr_helper)
from here.xlr.xlr_helper import XlrApiHelper
import here.jira.jira_client
reload(here.jira.jira_client)
from here.jira.jira_client import JiraClient


def process(task_vars):
    jira = JiraClient.new_instance(task_vars)
    links = jira.find_epic_links(task_vars['issueId'])
    result = process_gate(task_vars, links)
    api_helper = task_vars['api_helper']
    for key, status_summary in result['issues'].items():
        api_helper.add_gate_to_block(task_vars['dependencyBlock'], key, "%s: %s" % (key, status_summary['summary']),
                                     task_vars['epicTemplate'], task_vars["businessReleaseVersion"])
    api_helper.delete_other_gates_from_block(task_vars['dependencyBlock'], result['issues'].keys())
    return result


if __name__ == '__main__' or __name__ == '__builtin__':
    api_helper = XlrApiHelper(locals())
    output_vars = process(locals())
    for k, v in output_vars.items():
        locals()[k] = v
    handle_sleep(locals(), output_vars)
