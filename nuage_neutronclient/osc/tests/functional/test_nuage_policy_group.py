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

import netaddr
from openstackclient.tests.functional import base
from osc_lib.utils import format_list

from vspk import v6 as vspk

import nuage_neutronclient.osc.tests.utils as utils


class NuagePolicyGroupTests(base.TestCase):

    def __init__(self, *args, **kwargs):
        super(NuagePolicyGroupTests, self).__init__(*args, **kwargs)
        self.nuage_pg1 = None
        self.nuage_pg2 = None
        self.port1 = None
        self.port2 = None
        self.subnet1 = None
        self.subnet2 = None

    @classmethod
    def setUpClass(cls):
        super(NuagePolicyGroupTests, cls).setUpClass()
        cls.session = utils.create_new_vspk_session()

    def _create_subnet(self, network, cidr):
        user_enterprise = self.session.user.enterprises.get_first(
            filter='name == "{}"'.format(utils.get_vsd_net_parition_name()))

        # Create VSD managed subnet
        l3domain = utils.create_l3_domain(self, user_enterprise)
        zone = l3domain.create_child(
            vspk.NUZone(name=utils.get_random_name()))[0]
        subnet = zone.create_child(
            vspk.NUSubnet(name=utils.get_random_name(),
                          address=str(cidr.ip),
                          netmask=str(cidr.netmask)))[0]

        cmd_create = ('subnet create -f json --network {network} '
                      '--net-partition {net_partition} --nuagenet {nuagenet} '
                      '--subnet-range {subnet_range} {subnet_name}'
                      .format(network=network,
                              net_partition=user_enterprise.id,
                              nuagenet=subnet.id,
                              subnet_range=cidr,
                              subnet_name=utils.get_random_name()))
        create_output = json.loads(self.openstack(cmd_create))
        self.addCleanup(self.openstack,
                        'subnet delete {}'.format(create_output['id']))

        return create_output, l3domain

    @staticmethod
    def _create_nuage_pg(l3domain, **kwargs):
        return l3domain.create_child(vspk.NUPolicyGroup(**kwargs))[0]

    def _create_port(self, network_id, subnet_id):
        port_name = utils.get_random_name()
        cmd_create = ('port create -f json --network {network}'
                      ' --fixed-ip subnet={subnet} {name}'
                      .format(network=network_id,
                              subnet=subnet_id,
                              name=port_name))
        self.addCleanup(self.openstack, 'port delete {}'.format(port_name))
        return json.loads(self.openstack(cmd_create))

    def _create_network(self):
        network_name = utils.get_random_name()
        return json.loads(self.openstack('network create -f json {}'
                                         .format(network_name)))

    def setUp(self):
        super(NuagePolicyGroupTests, self).setUp()

        network = self._create_network()

        self.subnet1, l3domain1 = self._create_subnet(
            network=network['id'],
            cidr=netaddr.IPNetwork('10.0.0.0/24'))
        self.subnet2, l3domain2 = self._create_subnet(
            network=network['id'],
            cidr=netaddr.IPNetwork('20.0.0.0/24'))

        self.nuage_pg1 = self._create_nuage_pg(
            l3domain1,
            name=utils.get_random_name(),
            type='SOFTWARE',
            description=utils.get_random_name(),
            evpn_community_tag='1:2',
            external=True)

        self.nuage_pg2 = self._create_nuage_pg(
            l3domain2,
            name=utils.get_random_name(),
            type='SOFTWARE',
            description=utils.get_random_name(),
            external=False)

        self.port1 = self._create_port(network_id=network['id'],
                                       subnet_id=self.subnet1['id'])
        self.port2 = self._create_port(network_id=network['id'],
                                       subnet_id=self.subnet2['id'])

    def verify_short_form(self, expected_pg, observed_pg, expected_ports=None):
        self.assertIsNotNone(observed_pg)
        self.assertEqual(expected=2, observed=len(observed_pg))
        self.assertIsNotNone(observed_pg['ID'])
        self.assertEqual(expected=expected_pg.name,
                         observed=observed_pg['Name'])

    def verify_long_form(self, expected_pg, observed_pg, expected_ports=None):
        self.assertIsNotNone(observed_pg)
        self.assertEqual(expected=8, observed=len(observed_pg))
        self.assertIsNotNone(observed_pg['ID'])
        self.assertEqual(expected=expected_pg.name,
                         observed=observed_pg['Name'])
        self.assertEqual(expected=expected_pg.description,
                         observed=observed_pg['Description'])
        self.assertEqual(expected=expected_pg.type,
                         observed=observed_pg['Type'])
        self.assertEqual(expected=('external' if expected_pg.external
                                   else 'internal'),
                         observed=observed_pg['Scope'])
        self.assertEqual(expected=expected_pg.evpn_community_tag,
                         observed=observed_pg['EVPN Tag'])
        self.assertEqual(expected=expected_pg.policy_group_id,
                         observed=observed_pg['Policy group ID'])
        self.assertEqual(expected=format_list(expected_ports
                                              if expected_ports else []),
                         observed=observed_pg['Ports'])

    def test_list_show(self):
        # check list
        cmd_output = json.loads(
            self.openstack('nuage policy group list -f json'))

        pg1 = next((pg for pg in cmd_output if
                    pg['Name'] == self.nuage_pg1.name), None)
        self.verify_short_form(expected_pg=self.nuage_pg1, observed_pg=pg1)

        pg2 = next((pg for pg in cmd_output if
                    pg['Name'] == self.nuage_pg2.name), None)
        self.verify_short_form(expected_pg=self.nuage_pg2, observed_pg=pg2)

        # check show for one of the pgs
        cmd_output = json.loads(
            self.openstack('nuage policy group show {} -f json'
                           .format(pg1['ID'])))
        self.verify_long_form(expected_pg=self.nuage_pg1,
                              observed_pg=cmd_output)

    def test_list_with_args(self):
        # when specifying --for-subnet or --for-port expect only the pg from
        # the subnet to show up, not the other one we created
        cmd_output = json.loads(
            self.openstack('nuage policy group list -f json --for-subnet {}'
                           .format(self.subnet2['id'])))

        self.assertEqual(expected=1, observed=len(cmd_output))

        cmd_output = json.loads(
            self.openstack('nuage policy group list -f json --for-port {}'
                           .format(self.port2['id'])))

        self.assertEqual(expected=1, observed=len(cmd_output))

        cmd_output = json.loads(
            self.openstack('nuage policy group list -f json --ports {}'
                           .format(self.port2['id'])))

        self.assertEqual(expected=0, observed=len(cmd_output))

        self.openstack('port set --nuage-policy-group {pg} {port}'
                       .format(pg=self.nuage_pg2.id, port=self.port2['id']))

        cmd_output = json.loads(
            self.openstack('nuage policy group list -f json --ports {}'
                           .format(self.port2['id'])))

        self.assertEqual(expected=1, observed=len(cmd_output))
