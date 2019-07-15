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
import testtools

from nuage_neutronclient.osc.tests.utils import delete_and_verify
from nuage_neutronclient.osc.tests.utils import get_random_name


class NuageNetpartitionTests(base.TestCase):

    def create_and_verify(self, name, clean_up=True):
        cmd = ('nuage netpartition create -f json {name}'
               .format(name=name))
        cmd_output = json.loads(self.openstack(cmd))
        if clean_up:
            self.addCleanup(self.openstack,
                            'nuage netpartition delete {}'.format(name))

        # verify something is returned..
        self.assertIsNotNone(cmd_output)

        # with 2 keys..
        self.assertEqual(expected=2, observed=len(cmd_output))

        # having an id
        self.assertIsNotNone(cmd_output['id'])

        # and the correct name
        self.assertEqual(observed=cmd_output['name'],
                         expected=name)

        # and not the tenant_id, which is broken in plugin at the moment
        self.assertNotIn(needle='tenant_id', haystack=cmd_output)

        return cmd_output

    def show_and_verify(self, name):
        cmd = ('nuage netpartition show -f json {name}'
               .format(name=name))
        cmd_output = json.loads(self.openstack(cmd))

        # verify something is returned..
        self.assertIsNotNone(cmd_output)

        # with two keys..
        self.assertEqual(expected=2, observed=len(cmd_output))

        # having an id
        self.assertIsNotNone(cmd_output['id'])

        # and the correct name
        self.assertEqual(observed=cmd_output['name'],
                         expected=name)

        # and not the tenant_id, which is broken in plugin at the moment
        self.assertNotIn(needle='tenant_id', haystack=cmd_output)

        return cmd_output

    def list_and_verify(self, name):
        cmd = 'nuage netpartition list -f json'
        cmd_output = json.loads(self.openstack(cmd))
        for netpartition in cmd_output:
            # verify something is returned..
            self.assertIsNotNone(netpartition)

            # with two keys..
            self.assertEqual(expected=2, observed=len(netpartition))
            self.assertIn(needle='ID', haystack=netpartition)
            self.assertIn(needle='Name', haystack=netpartition)

        # verify that the netpartition with the name is in the list
        netpartition = next((netpartition for netpartition in cmd_output
                             if netpartition['Name'] == name), None)
        self.assertIsNotNone(netpartition)

        return cmd_output

    def test_basic_create_list_show(self):
        netpartition1_name = get_random_name()

        self.create_and_verify(netpartition1_name, clean_up=False)
        self.list_and_verify(netpartition1_name)
        self.show_and_verify(netpartition1_name)
        delete_and_verify(self, 'nuage netpartition', netpartition1_name)

    @testtools.skip("OPENSTACK-2629")
    def test_basic_create_list_show_unicode(self):
        netpartition1_name = get_random_name() + u'\u00e9\u00fc'

        self.create_and_verify(netpartition1_name, clean_up=False)
        self.list_and_verify(netpartition1_name)
        self.show_and_verify(netpartition1_name)
        delete_and_verify(self, 'nuage netpartition', netpartition1_name)
