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


class XlrApiHelper(object):

    def __init__(self, task_vars):
        self.task_vars = task_vars
        self.release_api = task_vars['releaseApi']
        self.task_api = task_vars['taskApi']
        self.template_api = task_vars['templateApi']

    def get_current_release(self):
        return self.task_vars['getCurrentRelease']()

    def get_release(self, release_name, fail_not_found=True):
        target_release = self.task_vars['getReleasesByTitle'](release_name)
        if len(target_release) == 0 and fail_not_found:
            raise Exception("Release with title '%s' not found." % release_name)
        elif len(target_release) == 0:
            return None
        return target_release[0]

    def get_template(self, template_name):
        templates = self.template_api.getTemplates(template_name)
        if len(templates) == 0:
            raise Exception("Template with title '%s' not found." % template_name)
        return templates[0]

    def get_task_from_release(self, name, release_id):
        task = self.task_api.searchTasksByTitle(name, None, release_id)
        if len(task) == 0:
            raise Exception("Task with title '%s' not found in release '%s'." % (name, release_id))
        return task[0]

    def complete_task(self, task_id, comment):
        import com.xebialabs.xlrelease.api.v1.forms.Comment
        self.task_api.completeTask(task_id, com.xebialabs.xlrelease.api.v1.forms.Comment(comment))

    def abort_task(self, task_id, comment):
        import com.xebialabs.xlrelease.api.v1.forms.Comment
        self.task_api.abortTask(task_id, com.xebialabs.xlrelease.api.v1.forms.Comment(comment))

    def get_task(self, name):
        task = self.task_vars['getTasksByTitle'](name)
        if len(task) == 0:
            raise Exception("Task with title '%s' not found." % name)
        return task[0]

    def create_release(self, title, template_name, variables, tags=[]):
        import com.xebialabs.xlrelease.api.v1.forms
        params = com.xebialabs.xlrelease.api.v1.forms.CreateRelease()
        params.setReleaseTitle(title)
        params.setAutoStart(True)
        params.setReleaseVariables(variables)
        template_id = self.get_template(template_name).id
        release = self.template_api.create(template_id, params)
        tags.extend(release.getTags())
        release.setTags(tags)
        self.release_api.updateRelease(release)
        return release

    def add_gate_to_block(self, block_name, gate_name, release_name, template_name, br_version):
        target_release = self.get_release(release_name, fail_not_found=False)
        if not target_release:
            target_release = self.create_release(release_name, template_name,
                                                 {"issueId": gate_name, "br_version": br_version}, [br_version])
            mdl.println("Created release '%s'" % release_name, bold=True)
        block = self.get_task(block_name)
        if not block.type in ["xlrelease.SequentialGroup", "xlrelease.ParallelGroup"]:
            raise Exception("Task '%s' is not a SequentialGroup. Cannot add gate to release '%s'" % (block_name, release_name))
        existing_task = [t for t in block.tasks if t.title == gate_name]
        if len(existing_task) > 0:
            return
        gate_task = self.task_api.newTask("xlrelease.GateTask")
        gate_task.setTitle(gate_name)
        gate_task = self.task_api.addTask(block.id, gate_task)
        self.task_api.addDependency(gate_task.id, target_release.id)

    def delete_other_gates_from_block(self, block_name, gate_names_to_keep):
        block = self.get_task(block_name)
        if block.type not in ["xlrelease.SequentialGroup", "xlrelease.ParallelGroup"]:
            raise Exception("Task '%s' is not a SequentialGroup or ParallelGroup. Cannot remove gate" % block_name)
        for gate in block.tasks:
            if gate.title not in gate_names_to_keep:
                self.task_api.delete(gate.id)
                release_id = gate.dependencies[0].targetId
                if release_id:
                    self.terminate_active_tasks_and_abort_release(release_id)

    def terminate_active_tasks_and_abort_release(self, release_id):
        try:
            tasks = self.release_api.getActiveTasks(release_id)
            for task in tasks:
                if str(task.status) == 'IN_PROGRESS':
                    self.abort_task(task.id, "De-scoped in Jira")
        except Exception as e:
            mdl.print_error(str(e))
        try:
            self.release_api.abort(release_id)
            mdl.println("Aborted release id '%s'" % release_id, bold=True)
        except Exception as e:
            mdl.print_error(str(e))

    def update_variable(self, var_name, new_value):
        current_release_id = self.get_current_release().getId()
        variables = self.release_api.getVariables(current_release_id)
        for v in variables:
            if v.key == var_name:
                v.setValue(new_value)
                self.release_api.updateVariable(v)
                return
        raise Exception("Variable with name '%s' not found." % var_name)
