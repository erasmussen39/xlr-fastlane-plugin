#
# Copyright 2018 XEBIALABS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#


from here.git.git_client import GitClient
from here.xlr.markdown_logger import MarkdownLogger as mdl
import re


def process(task_vars):
    client = GitClient.new_instance(task_vars)
    client.fetch_repo()
    commits = client.list_commits_between_commit_and__last_tag(task_vars["commitId"])
    matcher = re.compile(task_vars["storyRegexp"])
    stories = set()
    mdl.print_header3("Commit Messages")
    mdl.print_hr()
    for commit in commits:
        mdl.println(commit['message'])
        match = matcher.match(commit['message'])
        if match:
            stories.add(match.group(1))
    mdl.print_hr()
    mdl.print_header3("Stories found in messages")
    mdl.print_list(stories)
    if len(stories) == 0:
        raise Exception("No stories found in commit logs")

    return {"stories": stories}


if __name__ == '__main__' or __name__ == '__builtin__':
    output_vars = process(locals())
    stories = output_vars['stories']

