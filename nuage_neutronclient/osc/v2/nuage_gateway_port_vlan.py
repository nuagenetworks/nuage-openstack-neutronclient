# Copyright 2020 NOKIA
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

from keystoneclient import utils as project_utils
from neutronclient.common import exceptions
from osc_lib.command import command
from osc_lib import utils
from osc_lib.utils import columns as column_util

from nuage_neutronclient._i18n import _
from nuage_neutronclient.osc.v2.nuage_gateway \
    import RESOURCE_NAME as GW_RESOURCE_NAME
from nuage_neutronclient.osc.v2.nuage_gateway_port \
    import RESOURCE_NAME as GW_PORT_RESOURCE
from nuage_neutronclient.osc.v2.nuage_gateway_port \
    import RESOURCE_NAME_PLURAL as GW_PORT_RESOURCE_PLURAL
from nuage_neutronclient.osc.v2.utils import find_nested_resource

LOG = logging.getLogger(__name__)

RESOURCE_NAME = 'nuage_gateway_vlan'
RESOURCE_NAME_PLURAL = 'nuage_gateway_vlans'


_attr_map = (('id', 'ID', column_util.LIST_BOTH),
             ('usermnemonic', 'User mnemonic', column_util.LIST_BOTH),
             ('assigned', 'Assigned', column_util.LIST_BOTH),
             ('value', 'Value', column_util.LIST_BOTH),
             ('status', 'Status', column_util.LIST_BOTH),
             ('gateway', 'Gateway', column_util.LIST_BOTH),
             ('gatewayport', 'Gateway Port', column_util.LIST_BOTH),
             ('vport', 'vPort', column_util.LIST_BOTH),
             )


def find_gw_port_id(client, gw_port_name_or_id, gw_name_or_id=None):
    return find_nested_resource(
        name_or_id=gw_port_name_or_id,
        parent_name_or_id=gw_name_or_id,
        resource_finder=lambda x: client.find_resource(GW_PORT_RESOURCE, x),
        resource_lister=(
            lambda **kwargs: client.list_nuage_gateway_ports(
                **kwargs)[GW_PORT_RESOURCE_PLURAL]),
        parent_resource_finder=(
            lambda x: client.find_resource(GW_RESOURCE_NAME, x)),
        resource_name='gateway-port',
        parent_resource_name='gateway')['id']


def find_vlan_id(client, vlan_name_or_id, gw_port_id=None):
    return find_nested_resource(
        name_or_id=vlan_name_or_id,
        parent_name_or_id=gw_port_id,
        resource_finder=lambda x: client.find_resource(RESOURCE_NAME, x),
        resource_lister=(
            lambda **kwargs: client.list_nuage_gateway_vlans(
                **kwargs)[RESOURCE_NAME_PLURAL]),
        parent_resource_finder=lambda x: {'id': x},  # id is passed already
        resource_name='vlan',
        parent_resource_name='gatewayport')['id']


class ListNuageGatewayPortVLAN(command.Lister):
    """List Nuage Gateway Port VLAN"""

    def get_parser(self, prog_name):
        parser = super(ListNuageGatewayPortVLAN, self).get_parser(prog_name)
        parser.add_argument(
            'nuage_gatewayport', metavar='<nuage-gatewayport>',
            help=_('ID or name of nuage gateway port to look up.'))
        parser.add_argument(
            '--gateway', metavar='<nuage-gateway>',
            help=_('ID or name of nuage gateway to look up.'))
        parser.add_argument(
            '--project', metavar='<project>',
            help=_('The owner project (Name or ID)'), default='')
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient
        project_id = project_utils.find_resource(
            self.app.client_manager.identity.projects,
            parsed_args.project).id if parsed_args.project else ''
        params = dict(
            tenant=project_id,
            gatewayport=find_gw_port_id(
                client, parsed_args.nuage_gatewayport, parsed_args.gateway)
        )
        items = client.list_nuage_gateway_vlans(
            **params)[RESOURCE_NAME_PLURAL]
        for item in items:
            del item['tenant_id']

        headers, columns = column_util.get_column_definitions(
            _attr_map, long_listing=False)
        return (headers, (utils.get_dict_properties(obj, columns)
                          for obj in items))


def add_vlan_arguments(parser):
    parser.add_argument(
        'nuage_gateway_port_vlan',
        metavar='<nuage-gateway-port-vlan>',
        help=_("Nuage gateway port VLAN"
               "(ID or VLAN number if --gatewayport is also provided)")
    )
    parser.add_argument(
        '--gatewayport', metavar='<nuage-gateway-port>',
        help=_("Nuage gateway port the VLAN belongs to. "
               "Provide this argument in order to search by VLAN number."))
    parser.add_argument(
        '--gateway',
        metavar='<nuage-gateway>',
        help=_("Nuage gateway the gateway port belongs to (name or ID). "
               "Provide this argument in order to search by port name.")
    )


class ShowNuageGatewayPortVLAN(command.ShowOne):
    """Show information of a given Nuage Gateway Port VLAN"""

    def get_parser(self, prog_name):
        parser = super(ShowNuageGatewayPortVLAN, self).get_parser(prog_name)
        add_vlan_arguments(parser)
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient

        if parsed_args.gateway and not parsed_args.gatewayport:
            message = (_('--gatewayport '
                         'option should be specified'))
            raise exceptions.CommandError(message=message)

        if parsed_args.gateway and parsed_args.gatewayport:
            parsed_args.gatewayport = find_gw_port_id(
                client, parsed_args.gatewayport, parsed_args.gateway)

        vlan_id = find_vlan_id(client, parsed_args.nuage_gateway_port_vlan,
                               parsed_args.gatewayport)
        obj = client.show_nuage_gateway_vlan(vlan_id)[RESOURCE_NAME]
        del obj['tenant_id']

        columns, display_columns = column_util.get_columns(obj, _attr_map)
        data = utils.get_dict_properties(obj, columns)
        return display_columns, data


class CreateNuageGatewayPortVLAN(command.ShowOne):
    """Create Nuage Gateway Port VLAN"""

    def get_parser(self, prog_name):
        parser = super(CreateNuageGatewayPortVLAN, self).get_parser(prog_name)
        parser.add_argument(
            'nuage_gateway_port_vlan',
            metavar='<nuage-gateway-port-vlan>',
            help=_("VLAN ID or VLAN number if --gatewayport is provided.")
        )
        parser.add_argument(
            '--gatewayport', metavar='<nuage-gateway-port>',
            help=_("Nuage gateway port the VLAN belongs to. "
                   "Provide this argument in order to search by VLAN number."))
        parser.add_argument(
            '--gateway',
            metavar='<nuage-gateway>',
            help=_("Nuage gateway the gateway port belongs to (name or ID). "
                   "Provide this argument in order to search by port name.")
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient

        body = {RESOURCE_NAME: {
            'value': parsed_args.nuage_gateway_port_vlan,
            'gatewayport': find_gw_port_id(client,
                                           parsed_args.gatewayport,
                                           parsed_args.gateway)
        }}

        item = client.create_nuage_gateway_vlan(body)[RESOURCE_NAME]
        del item['tenant_id']

        columns, display_columns = column_util.get_columns(
            item, _attr_map)
        data = utils.get_dict_properties(
            item, columns)
        return display_columns, data


class DeleteNuageGatewayPortVLAN(command.Command):
    """Delete Nuage Gateway Port VLAN"""

    def get_parser(self, prog_name):
        parser = super(DeleteNuageGatewayPortVLAN, self).get_parser(prog_name)
        add_vlan_arguments(parser)
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient

        if parsed_args.gateway or parsed_args.gatewayport:
            parsed_args.gatewayport = find_gw_port_id(
                client, parsed_args.gatewayport, parsed_args.gateway)
            parsed_args.nuage_gateway_port_vlan = find_vlan_id(
                client, parsed_args.nuage_gateway_port_vlan,
                parsed_args.gatewayport)
        client.delete_nuage_gateway_vlan(parsed_args.nuage_gateway_port_vlan)


class NuageGatewayPortVLANProjectCommand(command.Command):

    action = None

    def get_parser(self, prog_name):
        parser = (super(NuageGatewayPortVLANProjectCommand, self)
                  .get_parser(prog_name))
        add_vlan_arguments(parser)
        parser.add_argument(
            'project', metavar='<nuage-project>',
            help=_('The owner project (Name or ID)'), default='')
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient

        if parsed_args.gateway or parsed_args.gatewayport:
            parsed_args.gatewayport = find_gw_port_id(
                client, parsed_args.gatewayport, parsed_args.gateway)
            parsed_args.nuage_gateway_port_vlan = find_vlan_id(
                client, parsed_args.nuage_gateway_port_vlan,
                parsed_args.gatewayport)

        body = {RESOURCE_NAME: {
            'tenant': project_utils.find_resource(
                self.app.client_manager.identity.projects,
                parsed_args.project).id,
            'action': self.action
        }}
        client.update_nuage_gateway_vlan(parsed_args.nuage_gateway_port_vlan,
                                         body)


class NuageGatewayPortVLANAddProject(NuageGatewayPortVLANProjectCommand):
    """Add project permission for Nuage Gateway Port VLAN"""

    action = 'assign'


class NuageGatewayPortVLANRemoveProject(NuageGatewayPortVLANProjectCommand):
    """Remove project permission for Nuage Gateway Port VLAN"""

    action = 'unassign'
