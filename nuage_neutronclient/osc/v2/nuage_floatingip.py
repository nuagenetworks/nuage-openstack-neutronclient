# Copyright 2018 NOKIA
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
from osc_lib import utils

from nuage_neutronclient._i18n import _

LOG = logging.getLogger(__name__)


# This is not a dict because order is important in Nuage floating ip list/show
_column_map = [('ID', 'id'), ('Floating_ip_address', 'floating_ip_address'),
               ('Assigned', 'assigned')]


class ListNuageFloatingIP(command.Lister):
    """List Nuage Floating IPs"""

    def get_parser(self, prog_name):
        parser = super(ListNuageFloatingIP, self).get_parser(prog_name)
        group = parser.add_mutually_exclusive_group(required=False)
        group.add_argument(
            '--for-subnet',
            help=_('ID or name of subnet for which to find available floating '
                   'ips.'))
        group.add_argument(
            '--for-port',
            help=_('ID or name of port for which to find available floating '
                   'ips.'))
        return parser

    def take_action(self, parsed_args):

        filters = {}
        if getattr(parsed_args, 'for_subnet', None):
            subnet_id = self.app.client_manager.network.find_subnet(
                parsed_args.for_subnet, ignore_missing=False).id
            filters['for_subnet'] = [subnet_id]
        elif getattr(parsed_args, 'for_port', None):
            port_id = self.app.client_manager.network\
                .find_port(parsed_args.for_port, ignore_missing=False).id
            filters['for_port'] = [port_id]

        headers, attrs = utils.calculate_header_and_attrs(
            column_headers=[x[0] for x in _column_map],
            attrs=[x[1] for x in _column_map],
            parsed_args=parsed_args)

        floatingips = (self.app.client_manager.nuageclient
                       .list_nuage_floatingips(**filters)['nuage_floatingips'])

        return (headers, (utils.get_dict_properties(
            s, attrs) for s in floatingips))


class ShowNuageFloatingIP(command.ShowOne):
    """Show information of a given Nuage Floating IP"""

    def get_parser(self, prog_name):
        parser = super(ShowNuageFloatingIP, self).get_parser(prog_name)

        parser.add_argument(
            'nuage_floatingip',
            metavar="<nuage_floatingip>",
            help=_("Nuage_floatingip to display (name or ID)")
        )

        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient

        obj = client.show_nuage_floatingip(
            parsed_args.nuage_floatingip)['nuage_floatingip']
        columns = sdk_utils.get_osc_show_columns_for_sdk_resource(
            obj, dict(_column_map))
        return columns[0], utils.get_dict_properties(obj, columns[1])
