# Copyright 2020 Nokia
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

from nuage_neutronclient.osc.tests import utils

from openstackclient.tests.functional.network.v2 import common


class NuageNetworkSegmentTests(common.NetworkTests):

    @classmethod
    def setUpClass(cls):
        super(NuageNetworkSegmentTests, cls).setUpClass()
        if cls.haz_network:
            cls.NETWORK_NAME = utils.get_random_name()
            cmd_output = json.loads(cls.openstack(
                'network create -f json ' +
                '--provider-network-type nuage_hybrid_mpls ' +
                cls.NETWORK_NAME
            ))
            cls.NETWORK_ID = cmd_output["id"]

    @classmethod
    def tearDownClass(cls):
        try:
            if cls.haz_network:
                raw_output = cls.openstack(
                    'network delete ' +
                    cls.NETWORK_NAME
                )
                cls.assertOutput('', raw_output)
        finally:
            super(NuageNetworkSegmentTests, cls).tearDownClass()

    def test_nuage_hybrid_mpls_segment_create_delete(self):
        name = utils.get_random_name()
        json_output = json.loads(self.openstack(
            'network segment create -f json ' +
            '--network ' + self.NETWORK_ID + ' ' +
            '--network-type nuage_hybrid_mpls ' +
            name
        ))
        self.assertEqual(
            'nuage_hybrid_mpls',
            json_output["network_type"]
        )

        raw_output = self.openstack(
            'network segment delete ' + name
        )
        self.assertOutput('', raw_output)

    def test_nuage_hybrid_mpls_segment_list(self):
        name = utils.get_random_name()
        json_output = json.loads(self.openstack(
            'network segment create -f json ' +
            '--network ' + self.NETWORK_ID + ' ' +
            '--network-type nuage_hybrid_mpls ' +
            name
        ))
        network_segment_id = json_output.get('id')
        network_segment_name = json_output.get('name')
        self.addCleanup(
            self.openstack,
            'network segment delete ' + network_segment_id
        )
        self.assertEqual(
            'nuage_hybrid_mpls',
            json_output["network_type"]
        )

        json_output = json.loads(self.openstack(
            'network segment list -f json'
        ))
        item_map = {
            item.get('ID'): item.get('Name') for item in json_output
        }
        self.assertIn(network_segment_id, item_map.keys())
        self.assertIn(network_segment_name, item_map.values())

    def test_nuage_hybrid_mpls_segment_set_show(self):
        name = utils.get_random_name()
        json_output = json.loads(self.openstack(
            'network segment create -f json ' +
            '--network ' + self.NETWORK_ID + ' ' +
            '--network-type nuage_hybrid_mpls ' +
            name
        ))
        self.addCleanup(
            self.openstack,
            'network segment delete ' + name
        )

        extension_output = json.loads(self.openstack(
            "extension list -f json "
        ))
        ext_alias = [x["Alias"] for x in extension_output]
        if "standard-attr-segment" in ext_alias:
            self.assertEqual(
                '',
                json_output["description"],
            )
        else:
            self.assertIsNone(
                json_output["description"],
            )

        new_description = 'new_description'
        cmd_output = self.openstack(
            'network segment set ' +
            '--description ' + new_description + ' ' +
            name
        )
        self.assertOutput('', cmd_output)

        json_output = json.loads(self.openstack(
            'network segment show -f json ' +
            name
        ))
        self.assertEqual(
            new_description,
            json_output["description"],
        )
