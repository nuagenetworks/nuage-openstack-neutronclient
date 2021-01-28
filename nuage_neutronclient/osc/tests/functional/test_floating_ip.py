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

import testtools

import nuage_neutronclient.osc.tests.utils as utils
from openstackclient.tests.functional.network.v2.test_floating_ip \
    import FloatingIpTests


class NuageFloatingIPExtensionTests(FloatingIpTests):

    @classmethod
    def setUpClass(cls):
        super(NuageFloatingIPExtensionTests, cls).setUpClass()
        cls.random_name = utils.get_random_name()

        # Private network
        cls.openstack('network create {}'.format(cls.random_name))

        cls.openstack(('subnet create --subnet-range 99.168.0.1/24 '
                       '--network {} {}'.format(cls.random_name,
                                                cls.random_name)))

        cls.openstack('port create --network {} {}'.format(cls.random_name,
                                                           cls.random_name))

        # Public network
        cls.openstack('network create --external public-{}'
                      .format(cls.random_name))
        random_cidr = utils.get_random_ipv4_subnet_config()["cidr"]
        cls.openstack((('subnet create --subnet-range {} '
                       '--network public-{} public-{}'
                        .format(random_cidr, cls.random_name,
                                cls.random_name))))

        # Router
        cls.openstack('router create {}'.format(cls.random_name))
        cls.openstack(('router set --external-gateway {} {}'
                       .format('public-{}'.format(cls.random_name),
                               cls.random_name)))
        cls.openstack(('router add subnet {} {}'
                       .format(cls.random_name, cls.random_name)))

    @classmethod
    def tearDownClass(cls):
        super(NuageFloatingIPExtensionTests, cls).tearDownClass()

        # Router
        cls.openstack('router remove subnet {} {}'.format(cls.random_name,
                                                          cls.random_name))
        cls.openstack(('router unset --external-gateway {}'
                       .format(cls.random_name)))

        cls.openstack('router delete {}'.format(cls.random_name))

        # Public network
        cls.openstack('subnet delete public-{}'.format(cls.random_name))
        cls.openstack('network delete public-{}'.format(cls.random_name))

        # Private network
        cls.openstack('port delete {}'.format(cls.random_name))
        cls.openstack('subnet delete {}'.format(cls.random_name))
        cls.openstack('network delete {}'.format(cls.random_name))

    def test_crud(self):
        # create with nuage attributes, expect no output
        cmd_output = json.loads(self.openstack((
            'floating ip create -f json --port {} '
            '--nuage-ingress-fip-rate-kbps 100 '
            '--nuage-egress-fip-rate-kbps 200 '
            'public-{}'.format(self.random_name, self.random_name))))
        fip_id = cmd_output['id']

        self.addCleanup(self.openstack, ('floating ip delete {}'
                                         .format(fip_id)))
        self.assertEqual(observed=cmd_output['nuage_ingress_fip_rate_kbps'],
                         expected=100)
        self.assertEqual(observed=cmd_output['nuage_egress_fip_rate_kbps'],
                         expected=200)

        # verify show
        cmd_output = json.loads(self.openstack(('floating ip show -f json {}'
                                                .format(fip_id))))
        self.assertEqual(observed=cmd_output['nuage_ingress_fip_rate_kbps'],
                         expected=100)
        self.assertEqual(observed=cmd_output['nuage_egress_fip_rate_kbps'],
                         expected=200)

        # update nuage attributes
        cmd_output = self.openstack(('floating ip set '
                                     '--nuage-ingress-fip-rate-kbps 200 '
                                     '--nuage-egress-fip-rate-kbps 100 {}'
                                     .format(fip_id)))
        self.assertEqual(expected='', observed=cmd_output)

        # verify show
        cmd_output = json.loads(self.openstack(('floating ip show -f json {}'
                                                .format(fip_id))))
        self.assertEqual(observed=cmd_output['nuage_ingress_fip_rate_kbps'],
                         expected=200)
        self.assertEqual(observed=cmd_output['nuage_egress_fip_rate_kbps'],
                         expected=100)

    @testtools.skip("OPENSTACK-2591")
    def test_floating_ip_set_and_unset_port(self):
        return super(NuageFloatingIPExtensionTests, self)\
            .test_floating_ip_set_and_unset_port()
