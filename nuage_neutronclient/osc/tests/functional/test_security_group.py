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

from tempest.lib import exceptions as tempest_exceptions

from nuage_neutronclient.osc.tests import utils
from openstackclient.tests.functional.network.v2.test_security_group \
    import SecurityGroupTests


class NuageSecurityGroupTests(SecurityGroupTests):

    def _create(self, name, extra_params=''):
        cmd = ('security group create -f json {extra_params} {name}'
               .format(extra_params=extra_params, name=name))
        sg = json.loads(self.openstack(cmd))
        self.addCleanup(self.openstack, ('security group delete {}'
                                         .format(sg['id'])))
        return sg

    def _set(self, name_or_id, extra_params=''):
        cmd = ('security group set {extra_params} {name_or_id}'
               .format(extra_params=extra_params, name_or_id=name_or_id))
        return self.openstack(cmd)

    def _show(self, name_or_id):
        cmd = ('security group show -f json {name_or_id}'
               .format(name_or_id=name_or_id))
        return json.loads(self.openstack(cmd))

    def test_stateful_option(self):
        # test create with no option
        sg = self._create(name=utils.get_random_name())
        self.assertIn(needle='stateful', haystack=sg)
        self.assertIn(needle=sg['stateful'], haystack=[True, False])

        # test create with --stateful
        sg1 = self._create(name=utils.get_random_name(),
                           extra_params='--stateful')
        self.assertIn(needle='stateful', haystack=sg1)
        self.assertEqual(expected=True, observed=sg1['stateful'])

        # test create with --no-stateful
        sg2 = self._create(name=utils.get_random_name(),
                           extra_params='--no-stateful')
        self.assertIn(needle='stateful', haystack=sg2)
        self.assertEqual(expected=False, observed=sg2['stateful'])

        # test create with illegal option combination
        self.assertRaisesRegex(
            tempest_exceptions.CommandFailed,
            'error: argument --stateful: not allowed with argument '
            '--no-stateful',
            self._create,
            name=utils.get_random_name(),
            extra_params='--no-stateful --stateful')

        # test show
        for sg in [sg1, sg2]:
            output = self._show(sg['id'])
            self.assertIn(needle='stateful', haystack=output)
            self.assertEqual(expected=sg['stateful'],
                             observed=output['stateful'])

        # test set (invert stateful value)
        for sg in [sg1, sg2]:
            param = '--no-stateful' if sg['stateful'] else '--stateful'
            output = self._set(sg['id'], param)
            self.assertEqual(expected='', observed=output)

        # test show inverted values after set
        for sg in [sg1, sg2]:
            output = self._show(sg['id'])
            self.assertIn(needle='stateful', haystack=output)
            self.assertEqual(expected=not sg['stateful'],
                             observed=output['stateful'])
