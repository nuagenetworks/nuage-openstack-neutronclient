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
from vspk import v5_0 as vspk

import nuage_neutronclient.osc.tests.utils as utils


class NuageFloatingIPTests(base.TestCase):

    @classmethod
    def setUpClass(cls):
        super(NuageFloatingIPTests, cls).setUpClass()
        cls.session = utils.create_new_vspk_session()

    def __init__(self, *args, **kwargs):
        super(NuageFloatingIPTests, self).__init__(*args, **kwargs)
        self.l3domain = None
        self.shared_subnet = None
        self.network_name = utils.get_random_name()
        self.openstack_subnet = None

    def _create_shared_fip_subnet(self, session, address, netmask):
        shared_enterprise = session.user.enterprises.get_first(
            filter='name == "Shared Infrastructure"')
        l3_domain_template_shared_infra = \
            shared_enterprise.domain_templates.get_first(
                filter='name == "Shared Domain template"')
        shared_l3_domain = shared_enterprise.create_child(
            vspk.NUDomain(name=utils.get_random_name(),
                          template_id=l3_domain_template_shared_infra.id))[0]
        self.addCleanup(shared_l3_domain.delete)

        zone = shared_l3_domain.zones.get_first()

        shared_subnet = zone.create_child(
            vspk.NUSubnet(name=utils.get_random_name(),
                          address=address,
                          netmask=netmask,
                          resource_type="FLOATING"))[0]

        self.addCleanup(shared_subnet.delete)

        return shared_subnet

    def setUp(self):
        super(NuageFloatingIPTests, self).setUp()

        self.openstack('network create {}'.format(self.network_name))
        self.addCleanup(self.openstack, 'network delete {}'
                        .format(self.network_name))

        # Create VSD managed subnet
        user_enterprise = self.session.user.enterprises.get_first(
            filter='name == "{}"'.format(utils.get_vsd_net_parition_name()))

        self.l3domain = utils.create_l3_domain(self, user_enterprise)

        zone = self.l3domain.create_child(
            vspk.NUZone(name=utils.get_random_name()))[0]

        subnet = zone.create_child(
            vspk.NUSubnet(name=utils.get_random_name(),
                          address='10.0.0.0',
                          netmask='255.255.255.0'))[0]

        cmd_create = ('subnet create -f json --network {network} '
                      '--net-partition {net_partition} --nuagenet {nuagenet} '
                      '--subnet-range {subnet_range} {subnet_name}'
                      .format(network=self.network_name,
                              net_partition=user_enterprise.id,
                              nuagenet=subnet.id,
                              subnet_range='10.0.0.0/24',
                              subnet_name=utils.get_random_name()))
        self.openstack_subnet = json.loads(self.openstack(cmd_create))
        self.addCleanup(self.openstack,
                        'subnet delete {}'.format(self.openstack_subnet['id']))

        self.shared_subnet = self._create_shared_fip_subnet(self.session,
                                                            '1.1.1.0',
                                                            '255.255.255.0')

    def _nuage_floatingip_show(self, port_id_or_name):
        cmd = 'nuage floating ip show -f json {}'.format(port_id_or_name)
        return json.loads(self.openstack(cmd))

    def _nuage_floatingip_list(self, for_port=None, for_subnet=None):
        cmd = 'nuage floating ip list -f json'
        if for_port:
            cmd += ' --for-port {}'.format(for_port)
        if for_subnet:
            cmd += ' --for-subnet {}'.format(for_subnet)
        return json.loads(self.openstack(cmd))

    def _create_nuage_floating_ip(self, floating_ip_str):
        floating_ip = self.l3domain.create_child(vspk.NUFloatingIp(
            associated_shared_network_resource_id=self.shared_subnet.id,
            address=floating_ip_str))[0]
        return floating_ip

    def test_show_list(self):
        """Create, delete a port with a nuage floating ip"""
        # Create Nuage floating ips
        floating_ip_str_1 = '1.1.1.50'
        floating_ip_str_2 = '1.1.1.60'

        floating_ip_1 = self._create_nuage_floating_ip(floating_ip_str_1)
        self.addCleanup(floating_ip_1.delete)

        floating_ip_2 = self._create_nuage_floating_ip(floating_ip_str_2)
        self.addCleanup(floating_ip_2.delete)

        expected_1 = {'ID': floating_ip_1.id,
                      'Assigned': False,
                      'Floating_ip_address': floating_ip_str_1}

        expected_2 = {'ID': floating_ip_2.id,
                      'Assigned': False,
                      'Floating_ip_address': floating_ip_str_2}

        # Show and verify
        cmd_output_show = self._nuage_floatingip_show(floating_ip_2.id)
        self.assertEqual(expected={k.lower(): v
                                   for k, v in expected_2.items()},
                         observed=cmd_output_show)

        # Attach a floating ip to the port
        port_name = utils.get_random_name()
        self.openstack(('port create -f json --network {network} {name}'
                        .format(network=self.network_name, name=port_name)))
        self.addCleanup(self.openstack, 'port delete {}'.format(port_name))
        self.openstack('port set --nuage-floatingip {fip} {port}'.format(
            fip=expected_1['ID'], port=port_name))
        expected_1['Assigned'] = True

        # List and verify
        cmd_output_list = self._nuage_floatingip_list()
        self.assertIn(needle=expected_1, haystack=cmd_output_list)
        self.assertIn(needle=expected_2, haystack=cmd_output_list)

        cmd_output_list = self._nuage_floatingip_list(for_port=port_name)
        self.assertEqual(expected=[expected_2],
                         observed=cmd_output_list)
        cmd_output_list = self._nuage_floatingip_list(
            for_subnet=self.openstack_subnet['id'])
        self.assertEqual(expected=[expected_2],
                         observed=cmd_output_list)
