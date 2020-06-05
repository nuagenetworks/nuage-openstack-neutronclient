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

from osc_lib.command import command
from osc_lib import utils
from osc_lib.utils import columns as column_util

from nuage_neutronclient._i18n import _

LOG = logging.getLogger(__name__)

RESOURCE_NAME = 'nuage_gateway'
RESOURCE_NAME_PLURAL = 'nuage_gateways'

_attr_map = (('id', 'ID', column_util.LIST_BOTH),
             ('type', 'Type', column_util.LIST_BOTH),
             ('template', 'Template', column_util.LIST_BOTH),
             ('systemid', 'System ID', column_util.LIST_BOTH),
             ('tenant_id', 'Tenant ID', column_util.LIST_BOTH),
             ('name', 'Name', column_util.LIST_BOTH),
             ('status', 'Status', column_util.LIST_BOTH),
             ('redundant', 'Redundant', column_util.LIST_LONG_ONLY),
             )


class ListNuageGateway(command.Lister):
    """List Nuage Gateway"""

    def take_action(self, _):
        client = self.app.client_manager.nuageclient

        items = client.list_nuage_gateways()[RESOURCE_NAME_PLURAL]

        headers, columns = column_util.get_column_definitions(
            _attr_map, long_listing=False)
        return (headers, (utils.get_dict_properties(obj, columns)
                          for obj in items))


class ShowNuageGateway(command.ShowOne):
    """Show information of a given Nuage Gateway"""

    def get_parser(self, prog_name):
        parser = super(ShowNuageGateway, self).get_parser(prog_name)
        parser.add_argument(
            'nuage_gateway',
            metavar='<nuage-gateway>',
            help=_("Nuage gateway to display (name or ID)")
        )

        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient
        gw_id = client.find_resource(RESOURCE_NAME,
                                     parsed_args.nuage_gateway)['id']
        obj = client.show_nuage_gateway(gw_id)[RESOURCE_NAME]
        columns, display_columns = column_util.get_columns(obj, _attr_map)
        data = utils.get_dict_properties(obj, columns)
        return display_columns, data
