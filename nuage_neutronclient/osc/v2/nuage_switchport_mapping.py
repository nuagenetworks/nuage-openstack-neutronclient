# Copyright 2019 NOKIA
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
import logging

from openstackclient.network import sdk_utils
from osc_lib.command import command
from osc_lib import exceptions
from osc_lib import utils
from osc_lib.utils import columns as column_util

from nuage_neutronclient._i18n import _
from nuage_neutronclient.osc.v2.utils import update_dict

LOG = logging.getLogger(__name__)

RESOURCE_NAME = 'switchport_mapping'
RESOURCE_NAME_PLURAL = 'switchport_mappings'

_attr_map = (('id', 'ID', column_util.LIST_BOTH),
             ('switch_id', 'Switch ID', column_util.LIST_BOTH),
             ('switch_info', 'Switch Info', column_util.LIST_BOTH),
             # ('port_name', 'Port Name', column_util.LIST_BOTH),
             ('physnet', 'Physical Network', column_util.LIST_BOTH),
             ('host_id', 'Host ID[:PCI slot]', column_util.LIST_BOTH),
             ('port_uuid', 'Port UUID', column_util.LIST_BOTH))

def add_arguments_for_create_update(parser, is_create):
    parser.add_argument(
        '--switch-id',
        dest='switch_id',
        help=_('SystemID of the gateway device.'),
        required=is_create)
    parser.add_argument(
        '--switch-info',
        dest='switch_info',
        help=_('Name of the switch device'),
        required=False)
    parser.add_argument(
        '--port-name',
        dest='port_name',
        help=_('Physical port name of the switch port'),
        required=is_create)
    parser.add_argument(
        '--port-desc',
        dest='port_desc',
        help=_('Port description to put in VSD'),
        required=False)
    parser.add_argument(
        '--host-id',
        help=_('Nova compute host id, hypervisor_hostname'),
        required=is_create)
    parser.add_argument(
        '--pci-slot',
        help=_('Optional PCI slot of a VF on given host'),
        required=False)
    parser.add_argument(
        '--physnet',
        dest='physnet',
        help=_('Physical network for the given NIC.'),
        required=is_create)


def get_body_update_create(parsed_args):
    body = {RESOURCE_NAME: {}}
    update_dict(parsed_args, body[RESOURCE_NAME],
                ('switch_id', 'switch_info', 'port_name', 'port_desc',
                 'host_id', 'pci_slot', 'physnet'))
    return body


class CreateNuageSwitchportMapping(command.ShowOne):
    """Create a new Nuage Switchport Mapping"""

    def get_parser(self, prog_name):
        parser = (super(CreateNuageSwitchportMapping, self)
                  .get_parser(prog_name))
        add_arguments_for_create_update(parser, is_create=True)
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient

        body = get_body_update_create(parsed_args)
        item = client.create_switchport_mapping(body)[RESOURCE_NAME]

        column_getter = sdk_utils.get_osc_show_columns_for_sdk_resource
        osc_column_map = {k: v for v, k, _ in _attr_map}
        columns, display_columns = column_getter(
            item, osc_column_map)

        return display_columns, utils.get_dict_properties(item, columns)


class DeleteNuageSwitchportMapping(command.Command):
    """Delete a given Nuage Switchport Mapping"""

    def get_parser(self, prog_name):
        parser = (super(DeleteNuageSwitchportMapping, self)
                  .get_parser(prog_name))
        parser.add_argument(
            'nuage_switchport_mapping',
            metavar='<nuage-switchport-mapping>',
            nargs='+',
            help=_('Nuage switchport mappings to delete (ID)'))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient
        result = 0

        for mapping_id in parsed_args.nuage_switchport_mapping:
            try:
                client.delete_switchport_mapping(mapping_id)
            except Exception as e:
                result += 1
                LOG.error(_("Failed to delete nuage switchport mapping with "
                            "name or ID '{}': {}").format(mapping_id, e))

        if result > 0:
            total = len(parsed_args.nuage_switchport_mapping)
            msg = (_("{result} of {total} nuage switchport mapping(s) failed "
                     "to delete.").format(result=result, total=total))
            raise exceptions.CommandError(msg)


class ListNuageSwitchportMapping(command.Lister):
    """List Nuage Switchport Mappings"""

    def take_action(self, _):
        client = self.app.client_manager.nuageclient

        items = client.list_switchport_mappings()[RESOURCE_NAME_PLURAL]

        headers, columns = column_util.get_column_definitions(
            _attr_map, long_listing=True)
        return (headers, (utils.get_dict_properties(obj, columns)
                          for obj in items))


class ShowNuageSwitchportMapping(command.ShowOne):
    """Show information of a given Nuage Switchport Mapping"""

    def get_parser(self, prog_name):
        parser = super(ShowNuageSwitchportMapping, self).get_parser(prog_name)

        parser.add_argument(
            'nuage_switchport_mapping',
            metavar='<nuage-switchport-mapping>',
            help=_("Nuage switchport mapping to display (ID)")
        )

        return parser

    def take_action(self, parsed_args):
        invisible_columns = ('tenant_id',)

        client = self.app.client_manager.nuageclient
        item = client.show_switchport_mapping(
            parsed_args.nuage_switchport_mapping)[RESOURCE_NAME]

        column_getter = sdk_utils.get_osc_show_columns_for_sdk_resource
        osc_column_map = {k: v for v, k, _ in _attr_map}
        columns, display_columns = column_getter(
            item, osc_column_map, invisible_columns)

        return display_columns, utils.get_dict_properties(item, columns)


class SetNuageSwitchportMapping(command.Command):
    """Set Nuage L2bridge properties"""

    def get_parser(self, prog_name):
        parser = super(SetNuageSwitchportMapping, self).get_parser(prog_name)
        parser.add_argument(
            'nuage_switchport_mapping',
            metavar="<nuage-switchport-mapping>",
            help=_("Nuage switchport mapping to update (ID)")
        )
        add_arguments_for_create_update(parser, is_create=False)
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient
        obj = client.find_resource_by_id(RESOURCE_NAME,
                                         parsed_args.nuage_switchport_mapping)

        changed_attrs = get_body_update_create(parsed_args)

        try:
            client.update_switchport_mapping(obj['id'], changed_attrs)
        except Exception as e:
            msg = (_("Failed to set Nuage Switchport '%(item)s': %(e)s")
                   % {'item': parsed_args.nuage_switchport_mapping, 'e': e})
            raise exceptions.CommandError(msg)
