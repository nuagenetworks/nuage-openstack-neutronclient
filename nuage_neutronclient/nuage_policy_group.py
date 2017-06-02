# Copyright 2016 Alcatel-Lucent USA Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from neutronclient.common import extension
from neutronclient.neutron import v2_0 as neutronV20
from neutronclient.neutron.v2_0 import port
from neutronclient.neutron.v2_0 import subnet

from nuage_neutronclient._i18n import _


class NuagePolicyGroup(extension.NeutronClientExtension):
    resource = 'nuage_policy_group'
    resource_plural = '%ss' % resource
    object_path = '/nuage-policy-groups'
    resource_path = '/nuage-policy-groups/%s'
    versions = ['2.0']


class NuagePolicyGroupList(extension.ClientExtensionList,
                           NuagePolicyGroup):
    """List VSD policy groups."""

    shell_command = 'nuage-policy-group-list'
    list_columns = ['id', 'name', 'ports']

    def get_parser(self, prog_name):
        parser = super(NuagePolicyGroupList, self).get_parser(
            prog_name)
        group = parser.add_mutually_exclusive_group(required=False)
        group.add_argument(
            '--for-subnet',
            help=_('ID or name of subnet to find policy_groups for'))
        group.add_argument(
            '--for-port',
            help=_('ID or name of port to find policy_groups for'))
        group.add_argument(
            '--ports', action='append',
            help=_('ID or name of port(s) which the policy groups are '
                   'associated with'))
        return parser

    def take_action(self, parsed_args):
        neutron_client = self.get_client()
        filters = {}
        if parsed_args.for_subnet:
            resource = subnet.ListSubnet.resource
            subnet_id = neutronV20.find_resourceid_by_name_or_id(
                neutron_client, resource, parsed_args.for_subnet)
            filters['for_subnet'] = [subnet_id]
        elif parsed_args.for_port:
            resource = port.ListPort.resource
            port_id = neutronV20.find_resourceid_by_name_or_id(
                neutron_client, resource, parsed_args.for_port)
            filters['for_port'] = [port_id]
        elif parsed_args.ports:
            resource = port.ListPort.resource
            filters['ports'] = [neutronV20.find_resourceid_by_name_or_id(
                neutron_client, resource, p) for p in parsed_args.ports]

        filters.update(neutronV20.parse_args_to_dict(self.values_specs))
        policy_groups = neutron_client.list_nuage_policy_groups(
            **filters)[self.resource_plural]
        return self.setup_columns(policy_groups, parsed_args)


class NuagePolicyGroupShow(extension.ClientExtensionShow,
                           NuagePolicyGroup):
    """Show a given VSD policy group."""
    shell_command = 'nuage-policy-group-show'

    def take_action(self, parsed_args):
        policy_group = self.get_client().show_nuage_policy_group(
            parsed_args.id)[self.resource]
        return self.dict2columns(policy_group)
