# Copyright 2020 Alcatel-Lucent USA Inc.
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
import itertools
import json
import random

from openstackclient.tests.functional import base
from vspk import v6 as vspk

import nuage_neutronclient.osc.tests.utils as utils


class NuageGatewayTests(base.TestCase):

    _gw_attr_map = (('id', 'ID', True),
                    ('type', 'Type', True),
                    ('template', 'Template', True),
                    ('systemid', 'System ID', True),
                    ('tenant_id', 'Tenant ID', True),
                    ('name', 'Name', True),
                    ('status', 'Status', True),
                    ('redundant', 'Redundant', False),
                    )

    _gw_port_attr_map = (('id', 'ID', True),
                         ('usermnemonic', 'User mnemonic', True),
                         ('physicalname', 'Physical name', True),
                         ('vlan', 'VLAN', True),
                         ('tenant_id', 'Tenant ID', True),
                         ('name', 'Name', True),
                         ('status', 'Status', True),
                         )

    _vlan_attr_map = (('id', 'ID', True),
                      ('usermnemonic', 'User mnemonic', True),
                      ('assigned', 'Assigned', True),
                      ('value', 'Value', True),
                      ('status', 'Status', True),
                      ('gateway', 'Gateway', True),
                      ('gatewayport', 'Gateway Port', True),
                      ('vport', 'vPort', True),
                      )

    _vport_attr_map = (('id', 'ID', True),
                       ('interface', 'Interface', True),
                       ('name', 'Name', True),
                       ('subnet', 'Subnet', True),
                       ('type', 'Type', True),
                       ('tenant_id', 'Tenant ID', False),
                       ('vlan', 'VLAN', False),
                       ('gateway', 'Gateway', False),
                       ('gatewayport', 'Gateway Port', False),
                       ('port', 'Port', False),
                       )

    @classmethod
    def setUpClass(cls):
        super(NuageGatewayTests, cls).setUpClass()
        cls.session = utils.create_new_vspk_session()

        cls.personality = 'NUAGE_210_WBX_32_Q'

        cls.gw_name = 'wbx-' + str(random.randint(1, 0x7fffffff))
        cls.system_id = str(random.randint(1, 0x7fffffff))
        cls.gateway = cls.session.user.create_child(
            vspk.NUGateway(name=cls.gw_name,
                           system_id=cls.system_id,
                           personality=cls.personality))[0]

        cls.gw_port_name = 'gw-port-1'
        cls.gw_port_phys_name = '1/1/1'
        cls.gw_port_mnem = cls.gw_port_name + '_mnem'
        cls.gw_port_vlan_range = '0-4095'
        cls.port_type = 'ACCESS'
        cls.gw_port = cls.gateway.create_child(
            vspk.NUPort(name=cls.gw_port_name,
                        user_mnemonic=cls.gw_port_mnem,
                        vlan_range=cls.gw_port_vlan_range,
                        physical_name=cls.gw_port_phys_name,
                        port_type=cls.port_type))[0]

        cls.gw_port_name_2 = 'gw-port-2'
        cls.gw_port_phys_name_2 = '1/1/2'

        cls.gw_port_2 = cls.gateway.create_child(
            vspk.NUPort(name=cls.gw_port_name_2,
                        user_mnemonic=(cls.gw_port_name_2 + '_mnem'),
                        vlan_range='0-4095',
                        physical_name=cls.gw_port_phys_name_2,
                        port_type='ACCESS'))[0]

    @classmethod
    def tearDownClass(cls):
        super(NuageGatewayTests, cls).tearDownClass()
        cls.gateway.delete()

    def _verify_expected_keys(self, obj, attr_map, is_long):
        # verify something is returned..
        self.assertIsNotNone(obj)

        # with keys..
        expected_keys = [item[1] for item in attr_map if (item[2] or is_long)]
        self.assertEqual(expected=len(expected_keys), observed=len(obj))
        for key in expected_keys:
            self.assertIn(needle=key, haystack=obj)

    def _verify_expected_keys_for_show(self, obj, attr_map):
        self._verify_expected_keys(obj, attr_map, True)

    def _verify_expected_keys_for_create(self, obj, attr_map):
        self._verify_expected_keys(obj, attr_map, False)

    def _verify_expected_keys_for_list(self, obj, attr_map):
        # verify something is returned..
        self.assertGreater(len(obj), 0)

        # with keys..
        for item in obj:
            self._verify_expected_keys(item, attr_map, False)

    def _verify_vport_values_for_show(self, *args, **kwargs):
        self._verify_show_list_vport_values(*args, is_long=True, **kwargs)

    def _verify_vport_values_for_list(self, *args, **kwargs):
        self._verify_show_list_vport_values(*args, is_long=False, **kwargs)

    def _openstack_assert_equivalent(self, commands,
                                     message='Lookup by name and id should '
                                             'return the same output'):
        """Verify that a series of cli commands return the same output

        @return command output
        """
        cmd_output = json.loads(self.openstack(commands.pop()))
        self.assertTrue(all(json.loads(
            self.openstack(x)) == cmd_output for x in commands), message)
        return cmd_output

    def test_list_gateway(self):
        cmd = 'nuage gateway list -f json'
        cmd_output = json.loads(self.openstack(cmd))

        self._verify_expected_keys_for_list(cmd_output, self._gw_attr_map)

        gw = next((gw for gw in cmd_output if gw['Name'] == self.gw_name),
                  None)
        self.assertIsNotNone(gw)

        # and the correct attributes
        self.assertEqual(observed=gw['Type'], expected=self.personality)
        self.assertNotEqual(gw['Template'], '')
        self.assertEqual(observed=gw['System ID'],
                         expected=self.system_id)
        self.assertNotEqual(gw['Tenant ID'], '')
        self.assertEqual(observed=gw['Name'], expected=self.gw_name)
        self.assertEqual(observed=gw['Status'], expected=False)
        self.assertNotIn(needle='Redundant', haystack=gw)

    def test_show_gateway(self):
        cmd_output = self._openstack_assert_equivalent([
            'nuage gateway show -f json {}'.format(self.gw_name),
            'nuage gateway show -f json {}'.format(self.gateway.id)])

        # verify something is returned..
        self.assertGreater(len(cmd_output), 0)
        gw = cmd_output

        # with keys..
        self._verify_expected_keys_for_show(gw, self._gw_attr_map)

        # and the correct attributes
        self.assertEqual(observed=gw['Type'], expected=self.personality)
        self.assertNotEqual(gw['Template'], '')
        self.assertEqual(observed=gw['System ID'],
                         expected=self.system_id)
        self.assertNotEqual(gw['Tenant ID'], '')
        self.assertEqual(observed=gw['Name'], expected=self.gw_name)
        self.assertEqual(observed=gw['Status'], expected=False)
        self.assertEqual(observed=gw['Redundant'], expected=False)

    def test_list_gateway_port(self):
        cmd_output = self._openstack_assert_equivalent([
            'nuage gateway port list -f json {}'.format(self.gw_name),
            'nuage gateway port list -f json {}'.format(self.gateway.id)])

        self._verify_expected_keys_for_list(
            cmd_output, self._gw_port_attr_map)

        gw_port = next((gw_port for gw_port in cmd_output
                        if gw_port['Name'] == self.gw_port_name), None)
        self.assertIsNotNone(gw_port)

        # and the correct attributes
        self.assertEqual(observed=gw_port['User mnemonic'],
                         expected=self.gw_port_mnem)
        self.assertEqual(observed=gw_port['Physical name'],
                         expected=self.gw_port_phys_name)
        self.assertEqual(observed=gw_port['VLAN'],
                         expected=self.gw_port_vlan_range)
        self.assertNotEqual(gw_port['Tenant ID'], '')
        self.assertEqual(observed=gw_port['Status'], expected='INITIALIZED')

    def test_show_gateway_port(self):
        cmd_output = self._openstack_assert_equivalent([
            'nuage gateway port show --gateway {} -f json {}'
            .format(self.gw_name, self.gw_port_name),
            'nuage gateway port show --gateway {} -f json {}'
            .format(self.gw_name, self.gw_port.id),
            'nuage gateway port show --gateway {} -f json {}'
            .format(self.gateway.id, self.gw_port_name),
            'nuage gateway port show --gateway {} -f json {}'
            .format(self.gateway.id, self.gw_port.id),
            'nuage gateway port show -f json {}'
            .format(self.gw_port.id)])

        # verify something is returned..
        self.assertGreater(len(cmd_output), 0)
        gw_port = cmd_output

        # with keys..
        self._verify_expected_keys_for_show(
            gw_port, self._gw_port_attr_map)

        # and the correct attributes
        self.assertEqual(observed=gw_port['User mnemonic'],
                         expected=self.gw_port_mnem)
        self.assertEqual(observed=gw_port['Physical name'],
                         expected=self.gw_port_phys_name)
        self.assertEqual(observed=gw_port['VLAN'],
                         expected=self.gw_port_vlan_range)
        self.assertNotEqual(gw_port['Tenant ID'], '')
        self.assertEqual(observed=gw_port['Status'], expected='INITIALIZED')

    def test_crud_vlan(self):
        # create vlan
        random_vlan = self._get_random_vlan()
        cmd = ('nuage gateway port vlan create --gateway {} --gatewayport {} '
               '-f json {}'.format(self.gw_name, self.gw_port_name,
                                   random_vlan))
        cmd_output_create = json.loads(self.openstack(cmd))

        # show vlan
        show_with_3_args = itertools.product(
            ['--gateway ' + self.gw_name, '--gateway ' + self.gateway.id],
            ['--gatewayport ' + self.gw_port_name, '--gatewayport ' +
             self.gw_port.id],
            [str(random_vlan), cmd_output_create['ID']]
        )
        show_with_2_args = itertools.product(
            ['--gatewayport ' + self.gw_port.id],
            [str(random_vlan), cmd_output_create['ID']]
        )
        show_with_1_arg = [[cmd_output_create['ID']]]
        cmd_output_show = self._openstack_assert_equivalent([
            'nuage gateway port vlan show -f json {}'. format(' '.join(args))
            for args in itertools.chain(show_with_3_args, show_with_2_args,
                                        show_with_1_arg)])

        # Show and create return the same output
        self.assertEqual(cmd_output_create, cmd_output_show)
        cmd_output = cmd_output_create

        # Validate show/create
        self._verify_expected_keys_for_show(
            cmd_output, self._vlan_attr_map)

        self._verify_show_list_vlan_values(cmd_output, random_vlan)

        # list vlan
        cmd_output = self._openstack_assert_equivalent([
            'nuage gateway port vlan list -f json --gateway {} {}'
            .format(self.gw_name, self.gw_port_name),
            'nuage gateway port vlan list -f json --gateway {} {}'
            .format(self.gw_name, self.gw_port.id),
            'nuage gateway port vlan list -f json --gateway {} {}'
            .format(self.gateway.id, self.gw_port_name),
            'nuage gateway port vlan list -f json --gateway {} {}'
            .format(self.gateway.id, self.gw_port.id),
            'nuage gateway port vlan list -f json {}'
            .format(self.gw_port.id)])

        self._verify_expected_keys_for_list(cmd_output, self._vlan_attr_map)

        vlan = next((vlan for vlan in cmd_output
                     if vlan['Gateway Port'] == self.gw_port.id), None)
        self.assertIsNotNone(vlan)
        self._verify_show_list_vlan_values(vlan, random_vlan)

        # add project
        project_name = 'admin'
        cmd = ('nuage gateway port vlan add project --gateway {} '
               '--gatewayport {} {} {}').format(self.gw_name,
                                                self.gw_port_name,
                                                random_vlan, project_name)
        cmd_output = self.openstack(cmd)
        self.assertEqual('', cmd_output)

        cmd_output_show = json.loads(self.openstack(
            'nuage gateway port vlan show -f json {}'.format(
                cmd_output_create['ID'])))
        self.assertIsNotNone(cmd_output_show['Assigned'])

        # remove project
        cmd = ('nuage gateway port vlan remove project --gateway {} '
               '--gatewayport {} {} {}').format(self.gw_name,
                                                self.gw_port_name,
                                                random_vlan, project_name)
        cmd_output = self.openstack(cmd)
        self.assertEqual('', cmd_output)

        cmd_output_show = json.loads(
            self.openstack('nuage gateway port vlan show -f json {}'
                           .format(cmd_output_create['ID'])))
        self.assertIsNone(cmd_output_show['Assigned'])

        # Delete VLAN
        cmd_delete = ('nuage gateway port vlan delete --gateway {} '
                      '--gatewayport {} {}'
                      .format(self.gw_name, self.gw_port_name, random_vlan))
        cmd_output = self.openstack(cmd_delete)
        self.assertEqual('', cmd_output)
        self.assertRaisesRegex(Exception, r'.*Unable\ to\ find.*',
                               self.openstack, cmd_delete)

    def _verify_show_list_vlan_values(self, cmd_output, random_vlan,
                                      assigned=False):
        self.assertIsNone(observed=cmd_output['User mnemonic'])
        self.assertIsNone(cmd_output['Assigned'])
        self.assertEqual(observed=cmd_output['Value'],
                         expected=random_vlan)
        self.assertEqual(observed=cmd_output['Status'],
                         expected='INITIALIZED')
        self.assertEqual(observed=cmd_output['Gateway'],
                         expected=self.gateway.id)
        self.assertEqual(observed=cmd_output['Gateway Port'],
                         expected=self.gw_port.id)
        self.assertIsNone(observed=cmd_output['vPort'])

    def _verify_show_list_vport_values(self, cmd_output, is_long,
                                       subnet, gateway, gatewayport, port,
                                       vlan, type='BRIDGE'):
        self.assertNotEqual('', cmd_output['Interface'])
        self.assertEqual(observed=cmd_output['Type'],
                         expected=type)
        self.assertEqual(observed=cmd_output['Subnet'],
                         expected=subnet)
        self.assertIn(needle='Bridge Vport' if type == 'BRIDGE' else 'Host',
                      haystack=cmd_output['Name'])
        if is_long:
            self.assertEqual(observed=cmd_output['Port'],
                             expected=port)
            self.assertEqual(observed=cmd_output['Gateway Port'],
                             expected=gatewayport)
            self.assertEqual(observed=cmd_output['Gateway'],
                             expected=gateway)
            self.assertEqual(observed=cmd_output['VLAN'],
                             expected=vlan)
            self.assertNotEqual('', cmd_output['Tenant ID'])

    def _get_random_vlan(self):
        return random.randint(
            *map(int, self.gw_port_vlan_range.split('-')))

    def test_crud_vport(self):
        # Setup
        vlan_value = self._get_random_vlan()
        cmd = ('nuage gateway port vlan create --gateway {} --gatewayport {} '
               '-f json {}'.format(self.gw_name, self.gw_port_name,
                                   vlan_value))
        vlan = json.loads(self.openstack(cmd))
        self.addCleanup(self.openstack,
                        ('nuage gateway port vlan delete --gateway {} '
                         '--gatewayport {} {}'
                         .format(self.gw_name, self.gw_port_name, vlan_value)))
        self.openstack('nuage gateway port vlan add project --gateway {} '
                       '--gatewayport {} {} {}'
                       .format(self.gw_name, self.gw_port_name,
                               vlan_value, 'admin'))
        self.addCleanup(self.openstack,
                        ('nuage gateway port vlan remove project '
                         '--gateway {} --gatewayport {} {} {}'
                         .format(self.gw_name, self.gw_port_name,
                                 vlan_value, 'admin')))

        self.openstack('network create network_{}'.format(vlan_value))
        self.addCleanup(self.openstack, 'network delete network_{}'
                        .format(vlan_value))
        cmd_output_subnet = json.loads(self.openstack(
            'subnet create -f json --network network_{v} '
            '--subnet-range 10.0.0.1/24 subnet_{v}'
            .format(v=vlan_value)))
        self.addCleanup(self.openstack, 'subnet delete subnet_{}'
                        .format(vlan_value))

        # create vPort
        cmd = ('nuage gateway vport create --subnet subnet_{} -f json {}'
               .format(vlan_value, vlan['ID']))
        cmd_output_create = json.loads(self.openstack(cmd))
        self._verify_expected_keys_for_create(
            cmd_output_create, self._vport_attr_map)

        # show vPort
        cmd_show = ('nuage gateway vport show -f json {}'
                    .format(cmd_output_create['ID']))

        cmd_output_show = json.loads(self.openstack(cmd_show))

        self.assertGreater(len(cmd_output_show), len(cmd_output_create))
        self._verify_expected_keys_for_show(
            cmd_output_show, self._vport_attr_map)

        params = dict(subnet=cmd_output_subnet['id'], gateway=self.gateway.id,
                      gatewayport=self.gw_port.id, port=None, vlan=vlan_value,
                      type='BRIDGE')
        self._verify_vport_values_for_show(cmd_output_show, **params)

        # list vPorts
        cmd_output = self._openstack_assert_equivalent([
            'nuage gateway vport list -f json subnet_{}'
            .format(vlan_value),
            'nuage gateway vport list -f json {}'
            .format(cmd_output_subnet['id'])])

        self._verify_expected_keys_for_list(cmd_output, self._vport_attr_map)

        vport = next((vport for vport in cmd_output
                     if vport['ID'] == cmd_output_create['ID']), None)
        self.assertIsNotNone(vport)
        self._verify_vport_values_for_list(vport, **params)

        # Delete vPort
        cmd_delete = ('nuage gateway vport delete {}'
                      .format(cmd_output_show['ID']))
        cmd_output = self.openstack(cmd_delete)
        self.assertEqual('', cmd_output)
        self.assertRaisesRegex(Exception, r'.*could\ not\ be\ found.*',
                               self.openstack, cmd_delete)
