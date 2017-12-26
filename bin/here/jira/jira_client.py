#
# Copyright 2018 XEBIALABS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import json
import requests
from requests.auth import HTTPBasicAuth
from here.xlr.markdown_logger import MarkdownLogger as mdl


class JiraClient(object):

    def __init__(self, url, username, password):
        self.url = url
        if self.url.endswith("/"):
            self.url = self.url[0:-1]
        self.auth = HTTPBasicAuth(username, password)

    @staticmethod
    def new_instance(params):
        jira_server = params["jiraServer"]
        if "username" in params and params["username"]:
            return JiraClient(jira_server["url"], params["username"], params["password"])
        else:
            return JiraClient(jira_server["url"],jira_server["username"], jira_server["password"])

    @staticmethod
    def pretty_print_json(dump_obj):
        print json.dumps(dump_obj, sort_keys=True, indent=4, separators=(',', ': '))


    def dump_err(self, err):
        if len(err["errorMessages"]) > 0:
            mdl.print_list(err["errorMessages"])
        rows = [[k, v] for k, v in err['errors'].items()]
        mdl.print_table(["Field", "Error"], rows)

    def send(self, method, uri, params=None, **kwargs):
        endpoint = "%s/rest/api/2/%s" % (self.url, uri)
        r = requests.request(method, endpoint, params=params, verify=False, auth=self.auth, **kwargs)
        if r.status_code == requests.codes.bad:
            try:
                err = r.json()
                self.dump_err(err)
            except ValueError:
                mdl.println(r.text)
        r.raise_for_status()
        return r

    def post_json_data(self, uri, json_data):
        return self.send("post", uri, data=json.dumps(json_data), headers={'Content-Type': 'application/json'})

    def put_json_data(self, uri, json_data):
        return self.send("put", uri, data=json.dumps(json_data), headers={'Content-Type': 'application/json'})

    def get_json_data(self, uri):
        return self.send('get', uri).json()

    def get_fields(self):
        field_lookup = {}
        r = self.send('get', 'field').json()
        for field in r:
            field_lookup[field['name'].strip().lower()] = field
        return field_lookup

    def get_editissue_metadata_for_type(self, issue_id):
        return self.send('get', 'issue/%s/editmeta' % issue_id).json()

    def get_issue(self, issue_id, fields=None):
        endpoint = 'issue/%s' % issue_id
        if fields:
            endpoint += '?fields=%s' % ','.join(fields)
        return self.send('get', endpoint).json()

    def get_createissue_metadata_for_type(self, project_name, issue_type_name):
        meta_data = self.send('get', 'issue/createmeta?expand=projects.issuetypes.fields').json()
        project_name = project_name.lower()
        project_meta_data = [p for p in meta_data['projects']
                             if project_name == p['name'].lower() or project_name == p['key'].lower()]
        if len(project_meta_data) != 1:
            raise Exception("Project '%s' not found." % project_name)
        project_meta_data = project_meta_data[0]
        issue_type_name = issue_type_name.strip().lower()
        issue_type_meta_data = [i for i in project_meta_data['issuetypes'] if issue_type_name == i['name'].lower()]
        if len(issue_type_meta_data) != 1:
            raise Exception("Issue type '%s' not found in project '%s'" % (issue_type_name, project_name))

        return [project_meta_data, issue_type_meta_data[0]]

    def get_resolved_value_from_allowed_values(self, value, field_meta_data, variable_name='value'):
        allowed_values = [v[variable_name] for v in field_meta_data['allowedValues']]
        resolved_value = [v for v in allowed_values if value == v.lower()]
        if len(resolved_value) != 1:
            raise Exception("Field '%s' only supports values of %s. Given '%s'." % (field_meta_data['name'],
                                                                                    allowed_values, value))
        return {variable_name: resolved_value[0]}

    def resolve_option_values(self, user_value, field_meta_data):
        user_values = user_value.split(',')
        user_values = [v.strip().lower() for v in user_values]
        schema_type = field_meta_data['schema']['custom']
        if not schema_type.startswith('com.atlassian.jira.plugin.system.customfieldtypes:'):
            raise Exception("This plugin only supports custom option field types of " +
                            "'com.atlassian.jira.plugin.system.customfieldtypes'. Found '%s'" % schema_type)
        field_type = schema_type.split(':')[1]
        supported_field_types = ['select', 'multiselect']
        if field_type not in supported_field_types:
            raise Exception("This plugin only supports custom option field types of %s. Found '%s'"
                            % (str(supported_field_types), field_type))
        if field_type == "select":
            if len(user_values) != 1:
                raise Exception("Field '%s' only supports single selection" % (field_meta_data['name']))
            return self.get_resolved_value_from_allowed_values(user_values[0], field_meta_data)
        else:
            return [self.get_resolved_value_from_allowed_values(uv, field_meta_data) for uv in user_values]

    def get_field_create_edit_meta(self, resolved_key, create_edit_meta):
        field_screen_meta_data = [create_edit_meta[f] for f in create_edit_meta.keys() if f == resolved_key]
        if len(field_screen_meta_data) != 1:
            raise Exception("Field '%s' is not defined in Jira create or edit metadata" % resolved_key)
        return field_screen_meta_data[0]

    def set_additional_fields(self, fields, additional_fields, create_edit_meta):
        lookup = self.get_fields()
        for k, v in additional_fields.items():
            try:
                field_meta_data = lookup[k.strip().lower()]
            except KeyError:
                raise Exception("Jira does not recognise field '%s'." % k)
            resolved_key = field_meta_data['id']
            schema_type = field_meta_data['schema']['type']
            if schema_type == 'number':
                fields[resolved_key] = int(v)
                continue
            elif schema_type == 'string' or schema_type == 'date':
                fields[resolved_key] = str(v)
                continue
            if not field_meta_data["custom"]:
                if schema_type == "priority" or schema_type == "array":
                    field_ce_meta_data = self.get_field_create_edit_meta(resolved_key, create_edit_meta)
                    fields[resolved_key] = self.get_resolved_value_from_allowed_values(v, field_ce_meta_data, 'name')
                else:
                    raise Exception("Only 'string', 'number', 'date', 'array', 'priority' types are supported for Jira fields. '%s' is of type '%s'"
                                    % (resolved_key, schema_type))
            else:
                if schema_type == 'option' or schema_type == 'array':
                    field_ce_meta_data = self.get_field_create_edit_meta(resolved_key, create_edit_meta)
                    fields[resolved_key] = self.resolve_option_values(v, field_ce_meta_data)
                else:
                    raise Exception("Only 'option', 'number', 'date, 'array', 'string' types are supported for custom Jira fields." +
                                    "'%s' is of type '%s'" % (resolved_key, schema_type))

    def update_issue(self, issue_id, assignee, additional_fields={}):
        issue_type_meta = self.get_editissue_metadata_for_type(issue_id)
        fields = {}
        if assignee:
            fields['assignee'] = {"name": assignee}

        self.set_additional_fields(fields, additional_fields, issue_type_meta['fields'])
        self.put_json_data('issue/%s' % issue_id, {'fields': fields})

    def create_issue(self, project, title, description, issue_type, assignee, additional_fields={}):
        description = description if description else ""
        project_meta, issue_type_meta = self.get_createissue_metadata_for_type(project, issue_type)
        fields = {
            'project': {'key': project_meta['key']},
            'summary': title,
            'description': description,
            'issuetype': {'name': issue_type_meta['name']}
        }

        if assignee:
            fields['assignee'] = {"name": assignee}

        self.set_additional_fields(fields, additional_fields, issue_type_meta['fields'])
        response = self.post_json_data('issue', {'fields': fields})
        return response.json()['key']

    def query(self, query, fields=['summary'], max_results=100):
        if not query:
            raise Exception('No JQL query provided.')
        content = {
            'jql': query,
            'startAt': 0,
            'fields': fields,
            'maxResults': max_results
        }
#        response_code = 500
#        response = self.post_json_data('search', content)
#        mdl.println(response.status_code)
#        if response.status_code >500:
#            time.sleep(60)
#            response = self.post_json_data('search', content)
#        else:
#            return response.json()
#https://stackoverflow.com/questions/4606919/in-python-try-until-no-error
#        response = None
        response_code = 500
        while response_code > 499:
            try:
                # connect
                response = self.post_json_data('search', content)
                response_code = response.status_code
#                mdl.println(response_code)
#                mdl.println(vars(response))
                if response_code == 200 and r.headers['Content-Type'] != "application/json":
                    response_code == 500
                    mdl.println("Unusual Jira response header")
                if response_code > 499:
                    mdl.println("ASDFasdfASDFasdf")
                    mdl.println(response_code)
                    time.sleep(60)
            except:
                pass
        return response.json()

    def _map_query_links_result(self, links):
        result = {}
        for link in links["issues"]:
            fields = link["fields"]
            result[link["key"]] = {"status": fields["status"]["name"], "summary": fields["summary"]}
        return result

    def find_story_links(self, for_epic_id):
        links = self.query('"Epic Link" = %s AND issuetype = "User Story"' % for_epic_id, fields=["summary", "status"])
        return self._map_query_links_result(links)

    def find_epic_links(self, for_feature_id):
        links = self.query('issuetype = Epic AND "Parent Link" = "%s"' % for_feature_id, fields=["summary", "status"])
        return self._map_query_links_result(links)

    def find_feature_links(self, for_version):
        links = self.query('issuetype = Feature AND fixVersion  = "%s"' % for_version, fields=["summary", "status"])
        return self._map_query_links_result(links)

    def transition_issue(self, issue_id, new_status):
        issue_url = 'issue/%s' % issue_id
        # Find possible transitions
        response = self.get_json_data(issue_url + "/transitions?expand=transitions.fields")
        transitions = response['transitions']

        # Check  transition
        wanted_transaction = -1
        for transition in transitions:
            if transition['to']['name'].lower() == new_status.lower():
                wanted_transaction = transition['id']
                break

        if wanted_transaction == -1:
            raise Exception(u"Unable to find status %s for issue %s" % (new_status, issue_id))

        # Prepare POST body
        transition_data = {
            "transition": {
                "id": wanted_transaction
            }
        }

        # Perform transition
        response = self.post_json_data(issue_url + "/transitions?expand=transitions.fields", transition_data)

