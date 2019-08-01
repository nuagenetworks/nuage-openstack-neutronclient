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

import testtools

from nuage_neutronclient.osc.tests import utils
from vspk import v6 as vspk

from openstackclient.tests.functional.network.v2.test_router \
    import RouterTests


class NuageRouterTests(RouterTests):

    @classmethod
    def setUpClass(cls):
        super(NuageRouterTests, cls).setUpClass()
        cls.session = utils.create_new_vspk_session()
        cls.enterprise = cls.session.user.enterprises.get_first(
            filter='name == "{}"'.format(utils.get_vsd_net_parition_name()))

    def _verify(self, expected, observed):
        for key in expected:
            self.assertIn(needle=key, haystack=observed)
            self.assertEqual(expected=expected[key], observed=observed[key])

    def _create_l3_domain_template(self):
        template = self.enterprise.create_child(vspk.NUDomainTemplate(
            name=utils.get_random_name()))[0]
        template.create_child(vspk.NUZoneTemplate(
            name='openstack-isolated'))
        template.create_child(vspk.NUZoneTemplate(
            name='openstack-shared'))

        self.addCleanup(template.delete)

        return template

    @staticmethod
    def _build_arg_str(items):
        return (' '.join('--{} {}'.format(k.replace('_', '-'), v)
                         for k, v in items.items()))

    def _random_target(self):
        # VSD-35089
        return '{}:{}'.format(random.randrange(10, 5000),
                              random.randrange(10, 5000))

    def test_nuage_options(self):
        # TODO(glenn) Test nuage-net-partition when the resource is implemented

        # Create a router with Nuage arguments and verify using router show
        router_name = utils.get_random_name()
        args_for_create = {
            'nuage_router_template': self._create_l3_domain_template().id,
            'nuage_rd': self._random_target(),
            'nuage_rt': self._random_target(),
            'nuage_backhaul_vnid': 12345678,
            'nuage_backhaul_rd': self._random_target(),
            'nuage_backhaul_rt': self._random_target(),
            'nuage_tunnel_type': 'GRE',
            'nuage_ecmp_count': 3,
            'nuage_underlay': 'snat'
        }

        cmd_create = ('router create -f json {args} {name}'
                      .format(args=self._build_arg_str(args_for_create),
                              name=router_name))
        cmd_show = 'router show -f json {}'.format(router_name)
        for cmd in [cmd_create, cmd_show]:
            cmd_output = json.loads(self.openstack(cmd))
            self._verify(expected=dict(args_for_create, name=router_name),
                         observed=cmd_output)

        # Set Nuage arguments and verify using router show
        # a. update a property and check that the other ones did not change
        args_for_set = {'nuage_ecmp_count': 4}
        cmd_set = ('router set {args} {router}'
                   .format(args=self._build_arg_str(args_for_set),
                           router=router_name))
        cmd_output = self.openstack(cmd_set)
        self.assertEqual(expected='', observed=cmd_output)

        cmd_show = 'router show -f json {}'.format(router_name)
        cmd_output = json.loads(self.openstack(cmd_show))
        self._verify(expected=dict(args_for_create, **args_for_set),
                     observed=cmd_output)

        # b. update all properties
        args_for_set = {
            'nuage_rd': self._random_target(),
            'nuage_rt': self._random_target(),
            'nuage_backhaul_vnid': 16777215,
            'nuage_backhaul_rd': self._random_target(),
            'nuage_backhaul_rt': self._random_target(),
            'nuage_tunnel_type': 'VXLAN',
            'nuage_ecmp_count': 4,
            'nuage_underlay': 'route',
            'name': utils.get_random_name()
        }

        cmd_set = ('router set {args} {router}'
                   .format(args=self._build_arg_str(args_for_set),
                           router=router_name))
        cmd_output = self.openstack(cmd_set)
        self.assertEqual(expected='', observed=cmd_output)

        cmd_show = 'router show -f json {}'.format(args_for_set['name'])
        cmd_output = json.loads(self.openstack(cmd_show))
        self._verify(expected=args_for_set, observed=cmd_output)

        # Delete the router and verify using router list
        utils.delete_and_verify(self, 'router', args_for_set['name'])

    @testtools.skip("Nuage does not have an L3 agent as such.")
    def test_router_list_l3_agent(self):
        return super(NuageRouterTests).test_router_list_l3_agent()

    def test_router_set_show_unset(self):
        try:
            return super(NuageRouterTests, self).test_router_set_show_unset()
        except Exception as e:
            # Nuage does not come with the distributed router extension loaded
            self.assertIn(needle="Unrecognized attribute(s) 'distributed'",
                          haystack=str(e))
