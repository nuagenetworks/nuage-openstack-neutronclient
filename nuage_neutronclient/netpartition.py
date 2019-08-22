# Copyright 2016 Alcatel-Lucent USA Inc.
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
from __future__ import print_function
import copy

from neutronclient.common import exceptions
from neutronclient.common import extension
from neutronclient.neutron import v2_0 as neutronV20

from nuage_neutronclient._i18n import _


class NetPartition(extension.NeutronClientExtension):
    resource = 'net_partition'
    resource_plural = '%ss' % resource
    object_path = '/%s' % 'net-partitions'
    resource_path = '/%s/%%s' % 'net-partitions'
    versions = ['2.0']


class NetPartitionList(extension.ClientExtensionList, NetPartition):
    """List netpartitions that belong to a given tenant."""

    shell_command = 'nuage-netpartition-list'
    list_columns = ['id', 'name']


class NetPartitionCreate(extension.ClientExtensionCreate, NetPartition):
    """Create a netpartition for a given tenant."""

    shell_command = 'nuage-netpartition-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            'name', metavar='name',
            help='Name of netpartition to create.')

    def args2body(self, parsed_args):
        body = {'net_partition': {'name': parsed_args.name}, }
        return body


class NetPartitionDelete(extension.ClientExtensionDelete, NetPartition):
    """Delete a given netpartition."""

    shell_command = 'nuage-netpartition-delete'


class NetPartitionShow(extension.ClientExtensionShow, NetPartition):
    """Show information of a given netpartition."""

    shell_command = 'nuage-netpartition-show'


class ProjectNetPartitionMapping(extension.NeutronClientExtension):
    resource = 'project_net_partition_mapping'
    object_path = '/%s' % 'project-net-partition-mappings'
    resource_plural = '%ss' % resource
    resource_path = '/%s/%%s' % 'project-net-partition-mappings'
    versions = ['2.0']

    def cleanup_output_data(self, data):
        result = data['project_net_partition_mapping']
        resource_path = '/%s/%%s' % 'net-partitions'
        client = self.get_client()
        try:
            netpartition = client.get(
                resource_path % result['net_partition_id'])['net_partition']
        except exceptions.NotFound:
            netpartition = None
        new_row = {
            'project': result['project'],
            'associated_netpartition_id': result['net_partition_id'],
        }
        if netpartition:
            new_row['associated_netpartition_name'] = netpartition['name']
        data['project_net_partition_mapping'] = new_row


class ProjectNetpartitionMappingCreate(extension.ClientExtensionCreate,
                                       ProjectNetPartitionMapping):
    shell_command = 'nuage-netpartition-project-add'

    def get_parser(self, prog_name):
        parser = super(ProjectNetpartitionMappingCreate,
                       self).get_parser(prog_name)
        parser.add_argument(
            'net_partition', metavar='NETPARTITION',
            help=_('ID or name of the net_partition to associate.'))
        parser.add_argument(
            'project', metavar='PROJECT',
            help=_('ID of the project'))

        return parser

    def args2body(self, parsed_args):
        net_partition_id = neutronV20.find_resourceid_by_name_or_id(
            self.get_client(), 'net_partition', parsed_args.net_partition)

        body = {
            'project_net_partition_mapping':
                {
                    'project': parsed_args.project,
                    'net_partition_id': net_partition_id
                }
        }
        return body


class ProjectNetpartitionMappingDelete(extension.ClientExtensionDelete,
                                       ProjectNetPartitionMapping):
    shell_command = 'nuage-netpartition-project-delete'
    allow_names = False

    def get_parser(self, prog_name):
        parser = super(ProjectNetpartitionMappingDelete,
                       self).get_parser(prog_name)
        # Change ID parser to project_id
        id_parser = parser._actions[-1]
        id_parser.help = _("Project ID to "
                           "delete project_net_partition_mapping for")
        id_parser.metavar = 'PROJECT'
        return parser

    def take_action(self, parsed_args):
        try:
            super(ProjectNetpartitionMappingDelete, self).take_action(
                parsed_args)
        except exceptions.NeutronCLIError as e:
            if e.message.startswith('Unable to find'):
                e.message = e.message.replace(
                    self.resource + '(s) with id(s)',
                    'net-partition to project mapping for project')
                e._error_string = e.message
            raise


class ProjectNetpartitionMappingList(extension.ClientExtensionList,
                                     ProjectNetPartitionMapping):

    shell_command = 'nuage-netpartition-project-list'

    list_columns = ['project', 'associated_netpartition_id',
                    'associated_netpartition_name']

    def extend_list(self, data, parsed_args):
        results = copy.deepcopy(data)
        resource_path = '/%s' % 'net-partitions'
        client = self.get_client()
        response = client.get(resource_path)['net_partitions']
        netpartitions = {netpart['id']: netpart for netpart in response}
        for row in results:
            data.remove(row)
            new_row = {
                'associated_netpartition_id': row['net_partition_id'],
                'project': row['project']
            }
            netpartition = netpartitions.get(row['net_partition_id'])
            if netpartition:
                new_row['associated_netpartition_name'] = netpartition['name']
            data.append(new_row)


class ProjectNetpartitionMappingShow(extension.ClientExtensionShow,
                                     ProjectNetPartitionMapping):

    shell_command = 'nuage-netpartition-project-show'

    allow_names = False

    def get_parser(self, prog_name):
        parser = super(ProjectNetpartitionMappingShow,
                       self).get_parser(prog_name)
        # Change ID parser to project_id
        id_parser = parser._actions[-1]
        id_parser.help = _("Project ID to "
                           "show project_net_partition_mapping for")
        id_parser.metavar = 'PROJECT'
        return parser
