# Copyright 2015 Alcatel-Lucent USA Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
import json

from openstackclient.tests.functional import base
from tempest.lib import exceptions

from nuage_neutronclient.osc.tests.utils import get_random_name


class NuageProjectNetpartitionMappingTest(base.TestCase):

    def _create_and_verify(self, name, use_name=False):
        # Verify when using ID's

        # Create netpartition through CLI
        cmd = ('nuage netpartition create -f json {name}'
               .format(name=name))
        np = json.loads(self.openstack(cmd))
        self.addCleanup(self.openstack,
                        'nuage netpartition delete {}'.format(name))
        # Create projec through CLI
        cmd = 'project create -f json {name}'.format(name=name)
        project = json.loads(self.openstack(cmd))
        self.addCleanup(self.openstack,
                        'project delete {}'.format(name))
        # Create
        if use_name:
            cmd = ('nuage netpartition add project -f json {np} {project}'
                   .format(np=np['name'], project=project['name']))
        else:
            cmd = ('nuage netpartition add project -f json {np} {project}'
                   .format(np=np['id'], project=project['id']))

        cmd_output = json.loads(self.openstack(cmd))

        # Verify
        self.assertEqual(observed=cmd_output['Associated Project'],
                         expected=project['id'])
        self.assertEqual(observed=cmd_output['Netpartition Name'],
                         expected=np['name'])
        self.assertEqual(observed=cmd_output['Netpartition ID'],
                         expected=np['id'])

        return np, project

    def _show_and_verify(self, np, project, use_name=False):
        if use_name:
            cmd = ('nuage netpartition project show -f json {name}'
                   .format(name=project['name']))
        else:
            cmd = ('nuage netpartition project show -f json {name}'
                   .format(name=project['id']))

        cmd_output = json.loads(self.openstack(cmd))

        # verify something is returned..
        self.assertIsNotNone(cmd_output)

        # with three keys..
        self.assertEqual(expected=3, observed=len(cmd_output))

        self.assertEqual(observed=cmd_output['Associated Project'],
                         expected=project['id'])
        self.assertEqual(observed=cmd_output['Netpartition Name'],
                         expected=np['name'])
        self.assertEqual(observed=cmd_output['Netpartition ID'],
                         expected=np['id'])

    def _list_and_verify(self, np, project):
        cmd = 'nuage netpartition project list -f json'
        cmd_output = json.loads(self.openstack(cmd))
        for mapping in cmd_output:
            # verify something is returned..
            self.assertIsNotNone(mapping)

            # with three keys..
            self.assertEqual(expected=3, observed=len(mapping))
            self.assertIn(needle='Netpartition Name', haystack=mapping)
            self.assertIn(needle='Netpartition ID', haystack=mapping)
            self.assertIn(needle='Associated Project', haystack=mapping)

        # verify that the correct mapping is in the list
        mapping = next((mapping for mapping in cmd_output
                        if mapping['Associated Project'] == project['id']),
                       None)
        self.assertIsNotNone(mapping)
        self.assertEqual(observed=mapping['Associated Project'],
                         expected=project['id'])
        self.assertEqual(observed=mapping['Netpartition Name'],
                         expected=np['name'])
        self.assertEqual(observed=mapping['Netpartition ID'],
                         expected=np['id'])

    def _delete_and_verify(self, resource):
        cmd_delete = ('nuage netpartition remove project {resource}'
                      .format(resource=resource))
        cmd_output = self.openstack(cmd_delete)
        self.assertEqual(expected='', observed=cmd_output)

        cmd_show = ('nuage netpartition project show'
                    ' {resource}').format(resource=resource)
        self.assertRaises(exceptions.CommandFailed,
                          self.openstack, cmd_show)

    def test_create_list_show_delete_id(self):
        netpartition1_name = get_random_name()

        np, project = self._create_and_verify(netpartition1_name)
        self._list_and_verify(np, project)
        self._show_and_verify(np, project)
        self._delete_and_verify(project['id'])

    def test_create_list_show_delete_name(self):
        netpartition1_name = get_random_name()

        np, project = self._create_and_verify(netpartition1_name,
                                              use_name=True)
        self._list_and_verify(np, project)
        self._show_and_verify(np, project, use_name=True)
        self._delete_and_verify(project['name'])
