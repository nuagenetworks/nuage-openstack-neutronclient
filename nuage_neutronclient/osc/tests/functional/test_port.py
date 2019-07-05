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

from openstackclient.tests.functional.network.v2.test_port import PortTests
from osc_lib import utils as osc_utils
from vspk import v5_0 as vspk

import nuage_neutronclient.osc.tests.utils as utils


class NuagePortTestsVSDManaged(PortTests):

    def __init__(self, *args, **kwargs):
        super(NuagePortTestsVSDManaged, self).__init__(*args, **kwargs)
        self.l3domain = None

    @classmethod
    def setUpClass(cls):
        super(NuagePortTestsVSDManaged, cls).setUpClass()
        cls.session = utils.create_new_vspk_session()

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

    def _port_show(self, port_id_or_name):
        cmd_show = 'port show -f json {}'.format(port_id_or_name)
        return json.loads(self.openstack(cmd_show))

    def setUp(self):
        super(NuagePortTestsVSDManaged, self).setUp()

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
                      .format(network=self.NETWORK_NAME,
                              net_partition=user_enterprise.id,
                              nuagenet=subnet.id,
                              subnet_range='10.0.0.0/24',
                              subnet_name=utils.get_random_name()))
        create_output = json.loads(self.openstack(cmd_create))
        self.addCleanup(self.openstack,
                        'subnet delete {}'.format(create_output['id']))

    def test_nuage_floating_ip_option(self):
        """Create, delete a port with a nuage floating ip"""

        # Create Nuage floating ip
        shared_subnet = self._create_shared_fip_subnet(self.session, '1.1.1.0',
                                                       '255.255.255.0')
        floating_ip_str = '1.1.1.10'
        floating_ip = self.l3domain.create_child(vspk.NUFloatingIp(
            associated_shared_network_resource_id=shared_subnet.id,
            address=floating_ip_str))[0]
        self.addCleanup(floating_ip.delete)

        # Create a port with the Nuage floating ip in the VSD managed subnet
        port_name = utils.get_random_name()
        cmd_create = ('port create -f json --nuage-floatingip {floating_ip} '
                      '--network {network} {name}'
                      .format(floating_ip=floating_ip_str,
                              network=self.NETWORK_NAME,
                              name=port_name))
        cmd_output = json.loads(self.openstack(cmd_create))
        self.addCleanup(self.openstack, 'port delete {}'.format(port_name))

        # Verify create
        self.assertIsNotNone(cmd_output.get('nuage_floatingip'))
        self.assertEqual(observed=cmd_output['nuage_floatingip'],
                         expected=osc_utils.format_dict(
                             {'id': floating_ip.id,
                              'floating_ip_address': floating_ip_str}))

        # Verify show
        cmd_output = self._port_show(port_name)
        self.assertEqual(observed=cmd_output['nuage_floatingip'],
                         expected=osc_utils.format_dict(
                             {'id': floating_ip.id,
                              'floating_ip_address': floating_ip_str}))

        # Try to create again, expect failure
        cmd_create = ('port create -f json --nuage-floatingip {floating_ip} '
                      '--network {network} {name}'
                      .format(floating_ip=floating_ip_str,
                              network=self.NETWORK_NAME,
                              name=utils.get_random_name()))
        self.assertRaisesRegex(Exception, "Floating IP .* is already in use",
                               self.openstack, cmd_create)

        # Verify set / unset
        cmd_set = 'port set --nuage-floatingip 1.1.1.99 {}'.format(port_name)
        self.assertRaisesRegex(Exception, 'No Nuage Floating IP available with'
                                          ' IP 1.1.1.99',
                               self.openstack, cmd_set)

        port_name_2 = utils.get_random_name()
        self.openstack('port create -f json --network {network} {name}'
                       .format(network=self.NETWORK_NAME,
                               name=port_name_2))

        cmd_set = 'port set --nuage-floatingip {} {}'.format(floating_ip_str,
                                                             port_name_2)
        self.assertRaisesRegex(Exception,
                               'Floating IP {} is already in use'
                               .format(floating_ip_str),
                               self.openstack, cmd_set)

        cmd_unset = 'port unset --nuage-floatingip {}'.format(port_name)
        self.openstack(cmd_unset)

        # Verify show (No Nuage floating ip)
        cmd_output = self._port_show(port_name)
        self.assertIsNone(cmd_output['nuage_floatingip'])

        # the set should work now, since we unsetted the previous fip
        self.openstack(cmd_set)

        # Verify delete
        utils.delete_and_verify(self, 'port', port_name_2)

    def test_nuage_policygroup_option(self):
        # create policygroups
        pg_names = [utils.get_random_name() for _ in range(2)]
        pg_ids = [self.l3domain.create_child(vspk.NUPolicyGroup(
            name=pg_name, type='SOFTWARE'))[0].id for pg_name in pg_names]

        # create port with the policygroup in the VSD managed subnet and verify
        port_name = utils.get_random_name()
        pgs_arg = ' '.join('--nuage-policy-group {}'
                           .format(name) for name in pg_names)
        cmd_create = ('port create -f json {pgs_arg} '
                      '--network {network} {name}'
                      .format(pgs_arg=pgs_arg,
                              network=self.NETWORK_NAME,
                              name=port_name))
        cmd_output = json.loads(self.openstack(cmd_create))
        self.assertEqual(observed=cmd_output['nuage_policy_groups'],
                         expected=osc_utils.format_list(pg_ids))

        # Set pg that is already set (nothing should change)
        chosen_pg_id = random.choice(pg_ids)
        cmd_set = 'port set --nuage-policy-group {pg_id} {port}'.format(
            pg_id=chosen_pg_id, port=port_name)
        cmd_output = self.openstack(cmd_set)
        self.assertEqual(expected='', observed=cmd_output)
        cmd_output = self._port_show(port_name)
        self.assertEqual(expected=osc_utils.format_list(pg_ids),
                         observed=cmd_output['nuage_policy_groups'])

        # Unset all and verify
        cmd_no_pgs = 'port set --no-nuage-policy-groups {}'.format(port_name)
        cmd_output = self.openstack(cmd_no_pgs)
        self.assertEqual(expected='', observed=cmd_output)
        cmd_output = self._port_show(port_name)
        self.assertIsNone(cmd_output['nuage_policy_groups'])

        # set all and verify
        cmd_set_all = 'port set {pgs_arg} {name}'.format(pgs_arg=pgs_arg,
                                                         name=port_name)
        cmd_output = self.openstack(cmd_set_all)
        self.assertEqual(expected='', observed=cmd_output)
        cmd_output = self._port_show(port_name)
        self.assertEqual(expected=osc_utils.format_list(pg_ids),
                         observed=cmd_output['nuage_policy_groups'])

        # unset one and verify
        cmd_unset = ('port unset --nuage-policy-group {pg} {port}'.format(
            pg=chosen_pg_id, port=port_name))
        cmd_output = self.openstack(cmd_unset)
        self.assertEqual(expected='', observed=cmd_output)
        cmd_output = self._port_show(port_name)
        self.assertEqual(observed=cmd_output['nuage_policy_groups'],
                         expected=osc_utils.format_list(
                             filter(lambda i: i != chosen_pg_id, pg_ids)))

        # overwrite and verify
        cmd_set = ('port set --no-nuage-policy-groups '
                   '--nuage-policy-group {} {}'
                   .format(chosen_pg_id, port_name))
        cmd_output = self.openstack(cmd_set)
        self.assertEqual(expected='', observed=cmd_output)
        cmd_output = self._port_show(port_name)
        self.assertEqual(expected=osc_utils.format_list([chosen_pg_id]),
                         observed=cmd_output['nuage_policy_groups'])

        # set one and verify
        pg_to_set = next(pg_id for pg_id in pg_ids if pg_id != chosen_pg_id)
        cmd_set = ('port set --nuage-policy-group {pg} {port}'.format(
            pg=pg_to_set, port=port_name))
        cmd_output = self.openstack(cmd_set)
        self.assertEqual(expected='', observed=cmd_output)
        cmd_output = self._port_show(port_name)
        self.assertEqual(expected=osc_utils.format_list([chosen_pg_id,
                                                         pg_to_set]),
                         observed=cmd_output['nuage_policy_groups'])

        # delete and verify
        utils.delete_and_verify(self, 'port', port_name)

    def test_nuage_redirect_target_option(self):
        # Note that this test only checks one redirect target per port
        # as it is unclear how to add multiple redirect targets at the moment

        # create RedirectionTarget instances on VSD
        rt_names = [utils.get_random_name() for _ in range(2)]
        rt_ids = [self.l3domain.create_child(vspk.NURedirectionTarget(
            name=rt_name, endPointType='L3'))[0].id for rt_name in rt_names]

        # create port with the redirect target in the VSD managed subnet
        # and verify
        port_name = utils.get_random_name()
        rts_arg = '--nuage-redirect-target {}'.format(rt_names[0])
        cmd_create = ('port create -f json {rts_arg} '
                      '--network {network} {name}'
                      .format(rts_arg=rts_arg,
                              network=self.NETWORK_NAME,
                              name=port_name))
        cmd_output = json.loads(self.openstack(cmd_create))
        self.assertEqual(observed=cmd_output['nuage_redirect_targets'],
                         expected=rt_ids[0])

        # Set rt that is already set (nothing should change)
        cmd_set = 'port set --nuage-redirect-target {rt_name} {port}'.format(
            rt_name=rt_names[0], port=port_name)
        cmd_output = self.openstack(cmd_set)
        self.assertEqual(expected='', observed=cmd_output)
        cmd_output = self._port_show(port_name)
        self.assertEqual(expected=rt_ids[0],
                         observed=cmd_output['nuage_redirect_targets'])

        # Unset and verify
        cmd_no_rts = ('port unset --nuage-redirect-target {port}'
                      .format(port=port_name))
        cmd_output = self.openstack(cmd_no_rts)
        self.assertEqual(expected='', observed=cmd_output)
        cmd_output = self._port_show(port_name)
        self.assertIsNone(cmd_output['nuage_redirect_targets'])

        # Overwrite and verify
        cmd_set = ('port set --nuage-redirect-target {} {}'
                   .format(rt_ids[1], port_name))
        cmd_output = self.openstack(cmd_set)
        self.assertEqual(expected='', observed=cmd_output)
        cmd_output = self._port_show(port_name)
        self.assertEqual(expected=rt_ids[1],
                         observed=cmd_output['nuage_redirect_targets'])

        # delete and verify
        utils.delete_and_verify(self, 'port', port_name)

    def test_port_no_vport(self):
        port_name = utils.get_random_name()
        cmd_create = ('port create -f json --vnic-type=direct '
                      '--network {network} {name}'
                      .format(network=self.NETWORK_NAME, name=port_name))
        cmd_output = json.loads(self.openstack(cmd_create))
        self.assertEqual(expected='direct',
                         observed=cmd_output['binding_vnic_type'])

        new_port_name = utils.get_random_name()
        cmd_update = ('port set --name {} {}'.format(new_port_name, port_name))
        cmd_output = self.openstack(cmd_update)
        self.assertEqual(expected='', observed=cmd_output)

        cmd_output = self._port_show(new_port_name)
        self.assertEqual(expected='direct',
                         observed=cmd_output['binding_vnic_type'])
        self.assertEqual(expected=new_port_name,
                         observed=cmd_output['name'])

        # delete and verify
        utils.delete_and_verify(self, 'port', new_port_name)
