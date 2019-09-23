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
from tempest.lib import exceptions

from vspk import v6 as vspk

import nuage_neutronclient.osc.tests.utils as utils


class NuageRedirectTargetTests(base.TestCase):

    def __init__(self, *args, **kwargs):
        super(NuageRedirectTargetTests, self).__init__(*args, **kwargs)
        self.nuage_rtl3 = None
        self.nuage_rtl2 = None
        self.l3domain = None
        self.l2domain = None
        self.portl3 = None
        self.portl2 = None

    @classmethod
    def setUpClass(cls):
        super(NuageRedirectTargetTests, cls).setUpClass()
        cls.session = utils.create_new_vspk_session()

    def _create_topology(self, network, cidr, is_l3=True):
        user_enterprise = self.session.user.enterprises.get_first(
            filter='name == "{}"'.format(utils.get_vsd_net_parition_name()))

        # Create VSD managed subnet
        if is_l3:
            l3domain = utils.create_l3_domain(self, user_enterprise)
            zone = l3domain.create_child(
                vspk.NUZone(name=utils.get_random_name()))[0]
            vsd_subnet = zone.create_child(
                vspk.NUSubnet(name=utils.get_random_name(),
                              address=str(cidr.ip),
                              netmask=str(cidr.netmask)))[0]
        else:
            l3domain = None
            vsd_subnet = utils.create_l2_domain(self, user_enterprise,
                                                address=str(cidr.ip),
                                                netmask=str(cidr.netmask),
                                                gateway=str(cidr.ip + 1))
        subnet_create_str = ('subnet create -f json --network {network} '
                             '--net-partition {net_partition} '
                             '--nuagenet {nuagenet} '
                             '--subnet-range {subnet_range} {subnet_name}')
        if not is_l3:
            subnet_create_str += ' --gateway None'

        cmd_create = subnet_create_str.format(
            network=network,
            net_partition=user_enterprise.id,
            nuagenet=vsd_subnet.id,
            subnet_range=cidr,
            subnet_name=utils.get_random_name())
        subnet = json.loads(self.openstack(cmd_create))
        self.addCleanup(self.openstack,
                        'subnet delete {}'.format(subnet['id']))

        return subnet, l3domain or vsd_subnet

    @staticmethod
    def _create_nuage_rt(domain, **kwargs):
        return domain.create_child(vspk.NURedirectionTarget(**kwargs))[0]

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
        super(NuageRedirectTargetTests, self).setUp()

        network = self._create_network()

        self.subnetl3, self.l3domain = self._create_topology(
            network=network['id'],
            cidr=netaddr.IPNetwork('10.0.0.0/24'))
        self.subnetl2, self.l2domain = self._create_topology(
            network=network['id'],
            cidr=netaddr.IPNetwork('20.0.0.0/24'), is_l3=False)

        self.nuage_rtl3 = self._create_nuage_rt(
            self.l3domain,
            name=utils.get_random_name(),
            end_point_type='L3',
            description=utils.get_random_name())

        self.nuage_rtl2 = self._create_nuage_rt(
            self.l2domain,
            name=utils.get_random_name(),
            end_point_type='VIRTUAL_WIRE',
            description=utils.get_random_name())

        self.portl3 = self._create_port(network_id=network['id'],
                                        subnet_id=self.subnetl3['id'])
        self.portl2 = self._create_port(network_id=network['id'],
                                        subnet_id=self.subnetl2['id'])

    def verify_short_form(self, expected_rt, observed_rt):
        self.assertIsNotNone(observed_rt)
        self.assertEqual(expected=4, observed=len(observed_rt))
        self.assertEqual(expected=expected_rt.id,
                         observed=observed_rt['ID'])
        self.assertEqual(expected=expected_rt.name,
                         observed=observed_rt['Name'])
        self.assertEqual(expected=expected_rt.end_point_type,
                         observed=observed_rt['Insertion Mode'])
        self.assertEqual(expected=expected_rt.redundancy_enabled,
                         observed=observed_rt['Redundancy Enabled'])

    def verify_long_form(self, expected_rt, observed_rt, expected_ports=None):
        self.assertIsNotNone(observed_rt)
        self.assertEqual(expected=expected_rt.id,
                         observed=observed_rt['ID'])
        self.assertEqual(expected=expected_rt.name,
                         observed=observed_rt['Name'])
        self.assertEqual(expected=expected_rt.end_point_type,
                         observed=observed_rt['Insertion Mode'])
        self.assertEqual(expected=expected_rt.redundancy_enabled,
                         observed=observed_rt['Redundancy Enabled'])
        self.assertEqual(expected=expected_rt.description,
                         observed=observed_rt['Description'])
        self.assertEqual(expected=format_list(expected_ports
                                              if expected_ports else []),
                         observed=observed_rt['Ports'])

    def test_list_show(self):
        # check list by subnet
        cmd_output = json.loads(
            self.openstack(
                'nuage redirect target list'
                ' -f json {subnet}'.format(subnet=self.subnetl3['name'])))

        rt1 = next((rt for rt in cmd_output if
                    rt['Name'] == self.nuage_rtl3.name), None)
        self.verify_short_form(expected_rt=self.nuage_rtl3, observed_rt=rt1)

        cmd_output = json.loads(
            self.openstack(
                'nuage redirect target list'
                ' -f json {subnet}'.format(subnet=self.subnetl2['id'])))

        rt2 = next((rt for rt in cmd_output if
                    rt['Name'] == self.nuage_rtl2.name), None)
        self.verify_short_form(expected_rt=self.nuage_rtl2, observed_rt=rt2)

        # check show
        cmd_output = json.loads(
            self.openstack('nuage redirect target show {} -f json'
                           .format(rt1['ID'])))
        self.verify_long_form(expected_rt=self.nuage_rtl3,
                              observed_rt=cmd_output)

        cmd_output = json.loads(
            self.openstack('nuage redirect target show {} -f json'
                           .format(rt1['Name'])))
        self.verify_long_form(expected_rt=self.nuage_rtl3,
                              observed_rt=cmd_output)

        # Check show for non-existing resource
        self.assertRaisesRegex(
            exceptions.CommandFailed,
            "Unable to find nuage_redirect_target with name "
            "or id '{}'".format('non-existing-RT'),
            self.openstack,
            'nuage redirect target show {} '
            '-f json'.format('non-existing-RT'))

    def test_with_ports(self):
        # Assign ports to redirect target
        vportl3 = self.l3domain.vports.get_first()
        self.nuage_rtl3.assign([vportl3], vspk.NUVPort)
        self.addCleanup(self.nuage_rtl3.assign, [], vspk.NUVPort)
        vportl2 = self.l2domain.vports.get_first()
        self.nuage_rtl2.assign([vportl2], vspk.NUVPort)
        self.addCleanup(self.nuage_rtl2.assign, [], vspk.NUVPort)
        # check show
        cmd_output = json.loads(
            self.openstack('nuage redirect target show {} -f json'
                           .format(self.nuage_rtl3.id)))
        self.verify_long_form(expected_rt=self.nuage_rtl3,
                              observed_rt=cmd_output,
                              expected_ports=[self.portl3['id']])
        cmd_output = json.loads(
            self.openstack('nuage redirect target show {} -f json'
                           .format(self.nuage_rtl2.id)))
        self.verify_long_form(expected_rt=self.nuage_rtl2,
                              observed_rt=cmd_output,
                              expected_ports=[self.portl2['id']])
