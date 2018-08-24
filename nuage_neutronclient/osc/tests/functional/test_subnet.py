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

import tempest.lib.exceptions as exceptions

from nuage_neutronclient.osc.tests.utils import create_l2_domain
from nuage_neutronclient.osc.tests.utils import create_new_vspk_session
from nuage_neutronclient.osc.tests.utils import delete_and_verify
from nuage_neutronclient.osc.tests.utils import get_random_ipv4_subnet_config
from nuage_neutronclient.osc.tests.utils import get_random_name
from nuage_neutronclient.osc.tests.utils import get_vsd_net_parition_name
from openstackclient.tests.functional.network.v2.test_subnet import SubnetTests


class NuageSubnetTests(SubnetTests):

    def test_vsd_managed_crud(self):
        session = create_new_vspk_session()
        enterprise = session.user.enterprises.get_first(
            filter='name == "{}"'.format(get_vsd_net_parition_name()))

        subnet_name = get_random_name()
        ip_config = get_random_ipv4_subnet_config()
        l2domain = create_l2_domain(self, enterprise, ip_config['address'],
                                    ip_config['netmask'], ip_config['gateway'])

        # CREATE / READ
        cmd_create = ('subnet create -f json --network {network} '
                      '--net-partition {net_partition} --nuagenet {nuagenet} '
                      '--subnet-range {subnet_range} {subnet_name} '
                      '--gateway None'
                      .format(network=self.NETWORK_NAME,
                              net_partition=enterprise.id,
                              nuagenet=l2domain.id,
                              subnet_range=ip_config['cidr'],
                              subnet_name=subnet_name))
        cmd_show = 'subnet show -f json {}'.format(subnet_name)
        for cmd in [cmd_create, cmd_show]:
            cmd_output = json.loads(self.openstack(cmd))
            self.assertEqual(expected=True,
                             observed=cmd_output['vsd_managed'])
            self.assertEqual(expected=subnet_name,
                             observed=cmd_output['name'])
            self.assertEqual(expected=l2domain.id,
                             observed=cmd_output['nuagenet'])
            self.assertEqual(expected=enterprise.id,
                             observed=cmd_output['net_partition'])
            self.assertEqual(expected=ip_config['cidr'],
                             observed=cmd_output['cidr'])

        # UPDATE
        update_cmd = 'subnet set --nuage-underlay route {}'.format(subnet_name)
        try:
            self.openstack(update_cmd)
        except exceptions.CommandFailed:
            # Proper error messages are broken in upstream Queen's
            # We need Change-Id: I617e55d67d93f1e07f5192ba94dcc0997ba9e12f
            # self.assertIn(needle='is a VSD-managed subnet. Update is not '
            #                      'supported for attributes other than ',
            #               haystack=str(e.stderr))
            pass
        else:
            self.assertIsNotNone(None, message="Update command should fail.")

        # DELETE
        delete_and_verify(self, 'subnet', subnet_name)

    def test_underlay_option(self):
        router_name = get_random_name()
        self.openstack('router create {}'.format(router_name))
        self.addCleanup(self.openstack, 'router delete {}'.format(router_name))

        external_network_name = get_random_name()
        self.openstack('network create --external {}'
                       .format(external_network_name))
        self.addCleanup(self.openstack, 'network delete {}'
                        .format(external_network_name))

        for is_underlay_enabled in [True, False]:
            subnet_name = get_random_name()
            underlay_argument = ('--underlay True' if is_underlay_enabled
                                 else '--underlay False')
            cmd = ('subnet create -f json {underlay} --network {network} '
                   '--subnet-range'.format(underlay=underlay_argument,
                                           network=external_network_name))
            cmd_output = self._subnet_create(cmd, subnet_name)

            self.assertEqual(expected=is_underlay_enabled,
                             observed=cmd_output['underlay'])
            self.assertEqual(expected=False,
                             observed=cmd_output['vsd_managed'])
            self.openstack('subnet delete {}'.format(subnet_name))

    def test_nuage_underlay_option(self):
        router_name = get_random_name()
        self.openstack('router create {}'.format(router_name))
        self.addCleanup(self.openstack, 'router delete {}'.format(router_name))

        subnet_name = get_random_name()
        self._subnet_create('subnet create -f json'
                            ' --network {network} --subnet-range'
                            .format(network=self.NETWORK_NAME), subnet_name)
        self.addCleanup(self.openstack, 'subnet delete {}'.format(subnet_name))

        self.openstack('router add subnet {router} {subnet}'
                       .format(router=router_name, subnet=subnet_name))
        self.addCleanup(self.openstack,
                        'router remove subnet {router} {subnet}'
                        .format(router=router_name, subnet=subnet_name))

        for (param, expected) in [('', 'inherited'), ('off', 'off'),
                                  ('route', 'route'), ('snat', 'snat')]:
            if param:
                param = '--nuage-underlay ' + param
                self.openstack('subnet set {param} {subnet}'
                               .format(param=param, subnet=subnet_name))
            cmd_output = json.loads(self.openstack("subnet show -f json {}"
                                                   .format(subnet_name)))
            self.assertEqual(expected=expected,
                             observed=cmd_output['nuage_underlay'])

    def test_nuage_uplink_option(self):
        external_network_1_name = get_random_name()
        self.openstack('network create --external {}'
                       .format(external_network_1_name))
        self.addCleanup(self.openstack, 'network delete {}'
                        .format(external_network_1_name))

        external_network_2_name = get_random_name()
        self.openstack('network create --external {}'
                       .format(external_network_2_name))
        self.addCleanup(self.openstack, 'network delete {}'
                        .format(external_network_2_name))

        subnet_1_name = get_random_name()
        cmd = ('subnet create -f json --underlay False --network {network} '
               '--subnet-range'.format(network=external_network_1_name))
        cmd_output = self._subnet_create(cmd, subnet_1_name)
        self.addCleanup(self.openstack, ('subnet delete {}'
                                         .format(subnet_1_name)))
        nuage_uplink_1 = cmd_output['nuage_uplink']
        self.assertIsNotNone(nuage_uplink_1)

        subnet_2_name = get_random_name()
        cmd = ('subnet create -f json --underlay False --network {network} '
               '--nuage-uplink {uplink} '
               '--subnet-range'.format(network=external_network_2_name,
                                       uplink=nuage_uplink_1))
        cmd_output = self._subnet_create(cmd, subnet_2_name)
        self.addCleanup(self.openstack, ('subnet delete {}'
                                         .format(subnet_2_name)))
        nuage_uplink_2 = cmd_output['nuage_uplink']

        self.assertEqual(nuage_uplink_1, nuage_uplink_2)
