# Copyright 2014 Alcatel-Lucent USA Inc.
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

from neutronclient.common import extension

class NetPartition(extension.NeutronClientExtension):
    resource = 'net_partition'
    resource_plural = '%ss' % resource
    object_path = '/%s' % 'net-partitions' 
    resource_path = '/%s/%%s' % 'net-partitions' 
    versions = ['2.0']	

class NetPartitionList(extension.ClientExtensionList, NetPartition):
    shell_command = 'nuage-netpartition-list'
    list_columns = ['id', 'name']
    pagination_support = True
    sorting_support = True

class NetPartitionCreate(extension.ClientExtensionCreate, NetPartition):
    shell_command = 'nuage-netpartition-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            'name', metavar='name',
            help='Name of netpartition to create.')

    def args2body(self, parsed_args):
        body = {'net_partition': {'name': parsed_args.name}, }
        return body

class NetPartitionDelete(extension.ClientExtensionDelete, NetPartition):
    shell_command = 'nuage-netpartition-delete'


class NetPartitionShow(extension.ClientExtensionShow, NetPartition):
    shell_command = 'nuage-netpartition-show'
