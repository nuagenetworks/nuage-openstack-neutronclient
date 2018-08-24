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
import json
import random
import sys
from uuid import uuid4 as uuid

from six import moves
from vspk import v5_0 as vspk

from openstackclient.tests.functional.base import execute


def get_random_name():
    return str(uuid())


def is_dhcp_agent_present():
    cmd = ('openstack network agent list -f json '
           '--agent-type dhcp')
    output = json.loads(execute(cmd, fail_ok=False))
    return output and output[0]['State'] == 'UP'


def get_vsd_api_url():
    config = moves.configparser.ConfigParser()
    try:
        config.read('/etc/neutron/plugins/nuage/plugin.ini')
        return 'https://' + config.get(section='restproxy', option='server')
    except Exception as e:
        sys.stderr.write('Unable to get VSD url from plugin.ini ({}), '
                         'using default value instead\n'.format(e))
        return '[changeme]'  # Local dev vsd server


def get_vsd_net_parition_name():
    config = moves.configparser.ConfigParser()
    try:
        config.read('/etc/neutron/plugins/nuage/plugin.ini')
        return config.get(section='restproxy',
                          option='default_net_partition_name')
    except Exception as e:
        sys.stderr.write('Unable to get default_net_partition_name from '
                         'plugin.ini ({}), using default value instead\n'
                         .format(e))
        return '[changeme]'  # Local dev net partition


def create_new_vspk_session():
    session = vspk.NUVSDSession(
        username='csproot',
        password='csproot',
        enterprise='csp',
        api_url=get_vsd_api_url())
    session.start()
    return session


def create_l2_domain(cleanup_registry, enterprise, address, netmask, gateway):
    domain_template = enterprise.create_child(vspk.NUL2DomainTemplate(
        name=get_random_name(), dhcp_managed=True,
        address=address, netmask=netmask, gateway=gateway))[0]
    cleanup_registry.addCleanup(lambda: domain_template.delete())

    l2domain = enterprise.create_child(vspk.NUL2Domain(
        name=get_random_name(), template_id=domain_template.id))[0]
    cleanup_registry.addCleanup(lambda: l2domain.delete())

    return l2domain


def create_l3_domain(cleanup_registry, enterprise):
    domain_template = enterprise.create_child(vspk.NUDomainTemplate(
        name=get_random_name()))[0]
    cleanup_registry.addCleanup(lambda: domain_template.delete())

    domain = enterprise.create_child(vspk.NUDomain(
        name=get_random_name(), template_id=domain_template.id))[0]
    cleanup_registry.addCleanup(lambda: domain.delete())

    return domain


def get_random_ipv4_subnet_config():
    prefix = ".".join(map(str, (random.randint(1, 223)
                                for _ in range(3))))
    return {"address": '{}.0'.format(prefix),
            "cidr": '{}.0/24'.format(prefix),
            "netmask": '255.255.255.0',
            "gateway": '{}.1'.format(prefix)}


def delete_and_verify(test_class, resource, resource_name):
    cmd_list = '{} list -f value -c Name'.format(resource)
    cmd_output = test_class.openstack(cmd_list)
    test_class.assertIn(needle=resource_name, haystack=cmd_output)

    cmd_delete = ('{resource} delete {name}'
                  .format(resource=resource, name=resource_name))
    cmd_output = test_class.openstack(cmd_delete)
    test_class.assertEqual(expected='', observed=cmd_output)

    cmd_list = '{} list -f value -c Name'.format(resource)
    cmd_output = test_class.openstack(cmd_list)
    test_class.assertNotIn(needle=resource_name, haystack=cmd_output)
