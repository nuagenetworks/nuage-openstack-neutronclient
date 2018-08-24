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

from nuage_neutronclient.osc.tests import utils
import testtools

from openstackclient.tests.functional.network.v2.test_network \
    import NetworkTests


class NuageNetworkTests(NetworkTests):

    def test_show_network_nuage_options(self):
        network_name = utils.get_random_name()
        cmd_create = 'network create -f json {name}'.format(name=network_name)
        cmd_show = 'network show -f json {name}'.format(name=network_name)

        for cmd in [cmd_create, cmd_show]:
            cmd_output = json.loads(self.openstack(cmd))
            self.assertIn(needle='nuage_l2bridge', haystack=cmd_output)
            self.assertIsNone(observed=cmd_output['nuage_l2bridge'])

        self.addCleanup(self.openstack,
                        'network delete {}'.format(network_name))

    @testtools.skipIf(not utils.is_dhcp_agent_present(),
                      'Skipping test that requires neutron dhcp agent')
    def test_network_dhcp_agent(self):
        super(NuageNetworkTests, self).test_network_dhcp_agent()
