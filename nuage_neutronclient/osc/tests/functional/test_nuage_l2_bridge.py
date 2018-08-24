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

from nuage_neutronclient.osc.tests.utils import delete_and_verify
from nuage_neutronclient.osc.tests.utils import get_random_name
from nuage_neutronclient.osc.v2.utils import format_list_of_dicts


class NuageL2BridgeTests(base.TestCase):

    def _build_physnet_arg(self, physnets):
        phsynet_template = ('--physnet physnet_name={physnet},'
                            'segmentation_id={segmentation_id},'
                            'segmentation_type={segmentation_type}')
        args = ' '.join(phsynet_template.format(**physnet)
                        for physnet in physnets)
        return args if args else ''

    def create_and_verify(self, name, physnets, clean_up=True):
        cmd = ('nuage l2bridge create -f json {physnets_args} {name}'
               .format(physnets_args=self._build_physnet_arg(physnets),
                       name=name))
        cmd_output = json.loads(self.openstack(cmd))
        if clean_up:
            self.addCleanup(self.openstack,
                            'nuage l2bridge delete {}'.format(name))

        self.assertIsNotNone(cmd_output)
        self.assertIsNotNone(cmd_output['id'])
        self.assertEqual(observed=cmd_output['name'],
                         expected=name)
        self.assertIsNone(cmd_output['nuage_subnet_id'])
        self.assertEqual(expected=format_list_of_dicts(physnets),
                         observed=cmd_output['physnets'])
        self.assertIsNotNone(cmd_output['tenant_id'])

        return cmd_output

    def show_and_verify(self, name, physnets, networks):
        cmd = ('nuage l2bridge show -f json {name}'
               .format(physnets_args=self._build_physnet_arg(physnets),
                       name=name))
        cmd_output = json.loads(self.openstack(cmd))

        self.assertIsNotNone(cmd_output)
        self.assertIsNotNone(cmd_output['id'])
        self.assertEqual(observed=cmd_output['name'],
                         expected=name)
        self.assertIsNone(cmd_output['nuage_subnet_id'])
        self.assertEqual(expected=format_list_of_dicts(physnets),
                         observed=cmd_output['physnets'])
        self.assertIsNotNone(cmd_output['tenant_id'])
        self.assertEqual(observed=cmd_output['networks'], expected=networks)

        return cmd_output

    def list_and_verify(self, name, physnets):
        cmd = 'nuage l2bridge list -f json'
        cmd_output = json.loads(self.openstack(cmd))
        for bridge in cmd_output:
            self.assertIsNotNone(bridge)
        bridge = next((bridge for bridge in cmd_output
                       if bridge['Name'] == name), None)
        self.assertIsNotNone(bridge)
        self.assertIsNone(bridge['Nuage_subnet_id'])
        self.assertEqual(expected=format_list_of_dicts(physnets),
                         observed=bridge['Physnets'])
        self.assertIsNone(bridge['Nuage_subnet_id'])

        return cmd_output

    def set_and_verify(self, name, physnets_to_set, physnets_to_verify,
                       networks_to_verify, name_to_set=None,
                       no_physnets=False):
        # set
        cmd = ('nuage l2bridge set {physnets} {no_physnet} {new_name} {name}'
               .format(physnets=self._build_physnet_arg(physnets_to_set),
                       no_physnet='--no-physnet' if no_physnets else '',
                       name=name,
                       new_name=('--name ' + name_to_set
                                 if name_to_set else '')))
        cmd_output = self.openstack(cmd)

        # verify
        self.assertEqual(expected='', observed=cmd_output)
        self.show_and_verify(name=name_to_set, physnets=physnets_to_verify,
                             networks=networks_to_verify)

    def test_crud(self):
        bridge_name = get_random_name()

        physnet = {"segmentation_id": "100", "segmentation_type": "vlan",
                   "physnet": "physnet1"}

        # CREATE / READ
        self.create_and_verify(name=bridge_name, physnets=[physnet],
                               clean_up=False)
        self.show_and_verify(name=bridge_name, physnets=[physnet], networks=[])
        self.list_and_verify(name=bridge_name, physnets=[physnet])

        # UPDATE
        new_physnet = {"segmentation_type": "vlan", "segmentation_id": 106,
                       "physnet": "physnet4"}
        new_bridge_name = get_random_name()
        self.set_and_verify(name=bridge_name, physnets_to_set=[new_physnet],
                            physnets_to_verify=[new_physnet, physnet],
                            name_to_set=new_bridge_name, networks_to_verify=[],
                            no_physnets=False)

        # DELETE
        delete_and_verify(self, 'nuage l2bridge', new_bridge_name)

    def test_physnets(self):
        # No physnets
        name = get_random_name()
        self.create_and_verify(name=name, physnets=[])
        self.show_and_verify(name=name, physnets=[],
                             networks=[])
        self.list_and_verify(name=name, physnets=[])

        # Multiple physnets
        name = get_random_name()
        physnet1 = {"segmentation_id": "100", "segmentation_type": "vlan",
                    "physnet": "physnet1"}
        physnet2 = {"segmentation_id": "101", "segmentation_type": "vlan",
                    "physnet": "physnet2"}
        physnet3 = {"segmentation_id": "1020", "segmentation_type": "vlan",
                    "physnet": "physnet2"}
        self.create_and_verify(name=name,
                               physnets=[physnet1, physnet2])
        self.show_and_verify(name=name, physnets=[physnet1, physnet2],
                             networks=[])
        self.list_and_verify(name=name, physnets=[physnet1, physnet2])
        self.set_and_verify(name=name, physnets_to_set=[physnet3],
                            physnets_to_verify=[physnet1, physnet2, physnet3],
                            name_to_set=name, networks_to_verify=[],
                            no_physnets=False)
        self.set_and_verify(name=name, physnets_to_set=[physnet1],
                            physnets_to_verify=[physnet1],
                            name_to_set=name, networks_to_verify=[],
                            no_physnets=True)
        self.set_and_verify(name=name, physnets_to_set=[physnet2, physnet3],
                            physnets_to_verify=[physnet2, physnet3],
                            name_to_set=name, networks_to_verify=[],
                            no_physnets=True)
        self.set_and_verify(name=name, physnets_to_set=[],
                            physnets_to_verify=[],
                            name_to_set=name, networks_to_verify=[],
                            no_physnets=True)
