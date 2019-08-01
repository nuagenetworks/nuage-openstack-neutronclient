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
import random

from openstackclient.tests.functional import base
from vspk import v6 as vspk

import nuage_neutronclient.osc.tests.utils as utils


class NuageSwitchPortTests(base.TestCase):

    def __init__(self, *args, **kwargs):
        super(NuageSwitchPortTests, self).__init__(*args, **kwargs)
        self.l3domain = None

    @classmethod
    def setUpClass(cls):
        super(NuageSwitchPortTests, cls).setUpClass()
        cls.session = utils.create_new_vspk_session()

        cls.personality = 'NUAGE_210_WBX_32_Q'

        # Gateway + port
        cls.name = 'wbx-' + str(random.randint(1, 0x7fffffff))
        cls.system_id = str(random.randint(1, 0x7fffffff))
        cls.gateway = cls.session.user.create_child(
            vspk.NUGateway(name=cls.name,
                           system_id=cls.system_id,
                           personality=cls.personality))[0]
        cls.gw_port_name = 'gw-port-1'
        cls.gw_port = cls.gateway.create_child(
            vspk.NUPort(name=cls.gw_port_name,
                        user_mnemonic=cls.gw_port_name + '_mnem',
                        vlan_range='0-4095',
                        physical_name=cls.gw_port_name + 'phys',
                        port_type='ACCESS'))[0]

        # Second gateway + port to update the switchport mapping
        cls.name_for_update = 'wbx-' + str(random.randint(1, 0x7fffffff))
        cls.system_id_for_update = str(random.randint(1, 0x7fffffff))

        cls.gateway_for_update = cls.session.user.create_child(
            vspk.NUGateway(name=cls.name_for_update,
                           system_id=cls.system_id_for_update,
                           personality=cls.personality))[0]

        cls.gw_port_for_update_name = 'gw-port-2'

        cls.gw_port_for_update = cls.gateway_for_update.create_child(
            vspk.NUPort(name=cls.gw_port_for_update_name,
                        user_mnemonic=(cls.gw_port_for_update_name + '_mnem'),
                        vlan_range='0-4095',
                        physical_name=cls.gw_port_for_update_name + '_phys',
                        port_type='ACCESS'))[0]
        pass

    @classmethod
    def tearDownClass(cls):
        super(NuageSwitchPortTests, cls).tearDownClass()

        cls.gw_port.delete()
        cls.gateway.delete()

    def create_and_verify_switchport_mapping(self, switch_id, switch_info,
                                             port_id, host_id, pci_slot,
                                             clean_up=True):
        cmd = ('nuage switchport mapping create -f json '
               '--switch-id {switch_id}'
               ' --switch-info {switch_info} --port-id {port_id} '
               '--host-id {host_id} --pci-slot {pci_slot}'
               .format(switch_id=switch_id, port_id=port_id,
                       switch_info=switch_info, host_id=host_id,
                       pci_slot=pci_slot))
        cmd_output = json.loads(self.openstack(cmd))
        if clean_up:
            self.addCleanup(self.openstack,
                            ('nuage switchport mapping delete {}'
                             .format(cmd_output['id'])))

        # verify something is returned..
        self.assertIsNotNone(cmd_output)

        # with x keys..
        self.assertEqual(expected=7, observed=len(cmd_output))

        # having an id
        self.assertIsNotNone(cmd_output['id'])

        # and the correct attributes
        self.assertEqual(observed=cmd_output['host_id'],
                         expected=host_id)
        self.assertEqual(observed=cmd_output['pci_slot'],
                         expected=pci_slot)
        self.assertEqual(observed=cmd_output['switch_id'],
                         expected=switch_id)
        self.assertEqual(observed=cmd_output['port_id'],
                         expected=port_id)
        self.assertEqual(observed=cmd_output['switch_info'],
                         expected=switch_info)
        self.assertIsNotNone(cmd_output['port_uuid'])

        self.assertNotIn(needle='tenant_id', haystack=cmd_output)

        return cmd_output

    def update_and_verify_switchport_mapping(self, switchport_mapping_id,
                                             switch_id, port_id,
                                             switch_info, host_id, pci_slot):
        cmd = ('nuage switchport mapping set --switch-id {switch_id} '
               '--switch-info {switch_info} --port-id {port_id} '
               '--host-id {host_id} --pci-slot {pci_slot} {swp_mapping}'
               .format(switch_id=switch_id, port_id=port_id,
                       switch_info=switch_info, host_id=host_id,
                       pci_slot=pci_slot, swp_mapping=switchport_mapping_id))
        cmd_output = self.openstack(cmd)
        self.assertEqual(expected='', observed=cmd_output)

    def show_and_verify_switchport_mapping(self, id, gw_port_id, host_id,
                                           pci_slot, switch_id, port_id,
                                           switch_info):
        cmd = ('nuage switchport mapping show -f json {id}'
               .format(id=id))
        cmd_output = json.loads(self.openstack(cmd))

        # verify something is returned..
        self.assertIsNotNone(cmd_output)

        # with x keys..
        self.assertEqual(expected=7, observed=len(cmd_output))

        # having an id
        self.assertIsNotNone(cmd_output['id'])

        # and the correct attributes
        self.assertEqual(observed=cmd_output['host_id'],
                         expected=host_id)
        self.assertEqual(observed=cmd_output['pci_slot'],
                         expected=pci_slot)
        self.assertEqual(observed=cmd_output['switch_id'],
                         expected=switch_id)
        self.assertEqual(observed=cmd_output['port_id'],
                         expected=port_id)
        self.assertEqual(observed=cmd_output['switch_info'],
                         expected=switch_info)
        self.assertEqual(observed=cmd_output['port_uuid'],
                         expected=gw_port_id)

        self.assertNotIn(needle='tenant_id', haystack=cmd_output)

        return cmd_output

    def list_and_verify_switchport_mapping(self, id, gw_port_id, host_id,
                                           pci_slot, switch_id, port_id,
                                           switch_info):
        cmd = 'nuage switchport mapping list -f json'
        cmd_output = json.loads(self.openstack(cmd))
        for switchport_mapping in cmd_output:
            # verify something is returned..
            self.assertIsNotNone(switchport_mapping)

            # with two keys..
            self.assertEqual(expected=7, observed=len(switchport_mapping))
            self.assertEqual(observed=switchport_mapping['ID'], expected=id)
            self.assertEqual(expected=switch_id,
                             observed=switchport_mapping['Switch ID'])
            self.assertEqual(expected=switch_info,
                             observed=switchport_mapping['Switch Info'])
            self.assertEqual(
                expected=port_id,
                observed=switchport_mapping['Port ID'])
            self.assertEqual(expected=host_id,
                             observed=switchport_mapping['Host ID'])
            self.assertEqual(expected=pci_slot,
                             observed=switchport_mapping['PCI slot'])
            self.assertEqual(expected=gw_port_id,
                             observed=switchport_mapping['Port UUID'])

        # verify that the switchport mapping with the ID is in the list
        switchport_mapping = next((item for item in cmd_output
                                   if item['ID'] == id), None)
        self.assertIsNotNone(switchport_mapping)

        return cmd_output

    def delete_and_verify_switchport_mapping(self, id):
        cmd_delete = ('nuage switchport mapping delete {id}'
                      .format(id=id))
        cmd_output = self.openstack(cmd_delete)
        self.assertEqual(expected='', observed=cmd_output)

        self.assertRaisesRegex(
            Exception, '.*does not exist.*', self.openstack,
            'nuage switchport mapping show {}'.format(id))

    def test_list_show_set_delete_switchport_mapping(self):
        kwargs = dict(host_id='fake_host_id', pci_slot='0000:18:06.6',
                      switch_id=self.system_id, port_id=self.gw_port_name,
                      switch_info=self.name)
        cmd_output = self.create_and_verify_switchport_mapping(clean_up=False,
                                                               **kwargs)
        self.list_and_verify_switchport_mapping(
            cmd_output['id'], self.gw_port.id, **kwargs)
        self.show_and_verify_switchport_mapping(
            cmd_output['id'], self.gw_port.id, **kwargs)
        args_for_update = dict(switch_id=self.system_id_for_update,
                               port_id=self.gw_port_for_update_name,
                               switch_info=self.name_for_update,
                               host_id='updated', pci_slot='0000:03:10.1')
        self.update_and_verify_switchport_mapping(
            cmd_output['id'], **args_for_update)
        self.show_and_verify_switchport_mapping(
            cmd_output['id'], self.gw_port_for_update.id, **args_for_update)

        self.delete_and_verify_switchport_mapping(cmd_output['id'])

    def test_list_show_switchport_binding(self):

        # create a switchport binding
        host_id = 'fake_host_id'
        pci_slot = '0000:03:10.6'
        vlan = 123
        binding_profile = dict(pci_slot=pci_slot,
                               physical_network='physnet1',
                               pci_vendor_info='8086:10ed')

        self.create_and_verify_switchport_mapping(
            host_id=host_id, pci_slot=pci_slot, switch_id=self.system_id,
            port_id=self.gw_port_name, switch_info=self.name)

        network_name = utils.get_random_name()
        self.openstack('network create --mtu 1450 --provider-network-type vlan'
                       ' --provider-physical-network physnet1'
                       ' --provider-segment {vlan} {network}'
                       .format(vlan=vlan, network=network_name))
        self.addCleanup(self.openstack,
                        'network delete {}'.format(network_name))

        segment_name = utils.get_random_name()
        self.openstack('network segment create --network-type vxlan '
                       '--segment {vlan} --network {network} {segment}'
                       .format(vlan=vlan, network=network_name,
                               segment=segment_name))
        self.addCleanup(self.openstack,
                        'network segment delete {}'.format(segment_name))

        subnet_name = utils.get_random_name()
        self.openstack(('subnet create --network {network} --subnet-range '
                        '10.0.0.1/24 {subnet}'.format(network=network_name,
                                                      subnet=subnet_name)))
        self.addCleanup(self.openstack,
                        'subnet delete {}'.format(subnet_name))

        port_name = utils.get_random_name()
        port_cmd_output = json.loads(self.openstack(
            ("port create -f json --network {network} --vnic-type direct "
             "--binding-profile '{binding_profile}' --host {host} {port}"
             .format(network=network_name,
                     binding_profile=json.dumps(binding_profile),
                     host=host_id,
                     port=port_name))))
        self.addCleanup(self.openstack,
                        'port delete {}'.format(port_cmd_output['id']))

        # list
        cmd_output = json.loads(
            self.openstack('nuage switchport binding list -f json'))
        item = next((m for m in cmd_output
                     if m['Neutron port ID'] == port_cmd_output['id']), None)
        self.assertIsNotNone(item)
        self.assertEqual(expected=5, observed=len(item))
        self.assertIsNotNone(item['ID'])
        self.assertEqual(expected=item['Switch ID'],
                         observed=self.system_id)
        self.assertEqual(expected=item['Port ID'],
                         observed=self.gw_port_name)
        self.assertEqual(expected=item['Segmentation ID'],
                         observed=vlan)

        # show
        cmd_output = json.loads(
            self.openstack('nuage switchport binding show {} -f json'
                           .format(item['ID'])))
        self.assertIsNotNone(cmd_output)
        self.assertEqual(expected=7, observed=len(cmd_output))
        self.assertIsNotNone(cmd_output['id'])
        self.assertEqual(expected=cmd_output['neutron_port_id'],
                         observed=port_cmd_output['id'])
        self.assertIsNotNone(cmd_output['nuage_vport_id'])
        self.assertIsNotNone(cmd_output['port_uuid'])
        self.assertEqual(expected=cmd_output['switch_id'],
                         observed=self.system_id)
        self.assertEqual(expected=cmd_output['port_id'],
                         observed=self.gw_port_name)
        self.assertEqual(expected=cmd_output['segmentation_id'],
                         observed=vlan)
