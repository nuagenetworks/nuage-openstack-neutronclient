# Copyright 2016 NOKIA
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

from neutronclient.common import extension
from neutronclient.neutron import v2_0 as gw_mappingV20
from nuage_neutronclient._i18n import _


class SwitchportMapping(extension.NeutronClientExtension):
    resource = 'switchport_mapping'
    resource_plural = 'switchport_mappings'
    path = 'net-topology/switchport_mappings'
    object_path = '/%s' % path
    resource_path = '/%s/%%s' % path
    versions = ['2.0']


class SwitchportMappingCreate(extension.ClientExtensionCreate,
                              SwitchportMapping):

    shell_command = 'nuage-switchport-mapping-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--switch-id',
            dest='switch_id',
            help=_('SystemID of the gateway device.'))
        parser.add_argument(
            '--switch-info',
            dest='switch_info',
            help=_('Name of the switch device'))
        parser.add_argument(
            '--port-name',
            dest='port_name',
            help=_('Physical port name of port on the switch'))
        parser.add_argument(
            '--port-desc',
            dest='port_desc',
            help=_('Port description to put in VSD'))
        parser.add_argument(
            '--host-id',
            help=_('Nova compute host id. hypervisor_hostname'))
        #parser.add_argument(
        #    '--pci-slot',
        #    dest='pci_slot',
        #    help=_('PCI id of the VF device.'))
        parser.add_argument(
            '--physnet',
            dest='physnet',
            help=_('Physical network to which the NIC is connected'))

        return parser

    def args2body(self, args):
        body = {}
        attributes = ['switch_id', 'switch_info', 'port_name', 'port_desc','host_id', 'physnet']
        gw_mappingV20.update_dict(args, body, attributes)

        return {'switchport_mapping': body}


class SwitchportMappingList(extension.ClientExtensionList, SwitchportMapping):
    """List switchport mappings."""

    shell_command = 'nuage-switchport-mapping-list'
    list_columns = ['id', 'switch_id', 'port_uuid', 'host_id', 'physnet']
    pagination_support = True
    sorting_support = True


class SwitchportMappingShow(extension.ClientExtensionShow, SwitchportMapping):
    """Show information of a given switchport mapping."""

    shell_command = 'nuage-switchport-mapping-show'


class SwitchportMappingDelete(extension.ClientExtensionDelete,
                              SwitchportMapping):
    """Delete a given switchport mapping."""

    shell_command = 'nuage-switchport-mapping-delete'


class SwitchportMappingUpdate(extension.ClientExtensionUpdate,
                              SwitchportMapping):
    """Update a given switchport-mapping."""

    shell_command = 'nuage-switchport-mapping-update'

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--switch-id',
            dest='switch_id',
            help=_('SystemID of the gateway device.'))
        parser.add_argument(
            '--switch-info',
            dest='switch_info',
            help=_('Name of the gateway device'))
        parser.add_argument(
            '--port-name',
            dest='port_name',
            help=_('Physical port name of gateway port'))
        parser.add_argument(
            '--port-desc',
            dest='port_desc',
            help=_('Port description to put in VSD'))
        parser.add_argument(
            '--host-id',
            help=_('Nova compute host id. hypervisor_hostname'))
        parser.add_argument(
            '--physnet',
            dest='physnet',
            help=_('Physical network to which the NIC is connected.'))

    def args2body(self, args):
        body = {}
        attributes = ['switch_id', 'switch_info', 'port_name', 'port_desc',
                      'host_id', 'physnet']
        gw_mappingV20.update_dict(args, body, attributes)

        return {'switchport_mapping': body}


class SwitchportBinding(extension.NeutronClientExtension):
    resource = 'switchport_binding'
    resource_plural = 'switchport_bindings'
    path = 'net-topology/switchport_bindings'
    object_path = '/%s' % path
    resource_path = '/%s/%%s' % path
    versions = ['2.0']


class SwitchportBindingList(extension.ClientExtensionList, SwitchportBinding):
    """List switchport bindings."""

    shell_command = 'nuage-switchport-binding-list'
    list_columns = ['id', 'neutron_port_id', 'switch_id', 'port_id',
                    'segmentation_id']
    pagination_support = True
    sorting_support = True


class SwitchportbindingShow(extension.ClientExtensionShow, SwitchportBinding):
    """Show information of a given switchport binding."""

    shell_command = 'nuage-switchport-binding-show'
