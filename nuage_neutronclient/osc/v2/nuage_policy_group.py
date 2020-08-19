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

from osc_lib.command import command
from osc_lib import utils
from osc_lib.utils import columns as column_util
from osc_lib.utils import format_list

from nuage_neutronclient._i18n import _

LOG = logging.getLogger(__name__)

_formatters = {
    'ports': format_list,
}

_attr_map = (('id', 'ID', column_util.LIST_BOTH),
             ('name', 'Name', column_util.LIST_BOTH),
             ('description', 'Description', column_util.LIST_LONG_ONLY),
             ('type', 'Type', column_util.LIST_LONG_ONLY),
             ('scope', 'Scope', column_util.LIST_LONG_ONLY),
             ('evpn_tag', 'EVPN Tag', column_util.LIST_LONG_ONLY),
             ('pg_id', 'Policy group ID', column_util.LIST_LONG_ONLY),
             ('ports', 'Ports', column_util.LIST_LONG_ONLY),
             )


class ListNuagePolicyGroup(command.Lister):
    """List Nuage Policy groups"""

    def get_parser(self, prog_name):
        parser = super(ListNuagePolicyGroup, self).get_parser(prog_name)
        group = parser.add_mutually_exclusive_group(required=False)
        group.add_argument(
            '--for-subnet',
            help=_('ID or name of subnet to find policy_groups for'),
            required=False)
        group.add_argument(
            '--for-port',
            help=_('ID or name of port to find policy_groups for'),
            required=False)
        group.add_argument(
            '--ports', action='append',
            help=_('ID of port(s) which the policy groups are '
                   'associated with'),
            required=False)
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient
        neutronclient = self.app.client_manager.neutronclient

        attrs = {}
        if parsed_args.for_subnet:
            subnet_id = neutronclient.find_resource(
                'subnet', parsed_args.for_subnet)['id']
            attrs['for_subnet'] = subnet_id
        elif parsed_args.for_port:
            port_id = neutronclient.find_resource(
                'port', parsed_args.for_port)['id']
            attrs['for_port'] = port_id
        elif parsed_args.ports:
            attrs['ports'] = parsed_args.ports

        nuage_policy_groups = (
            client.list_nuage_policy_groups(**attrs)['nuage_policy_groups'])

        headers, columns = column_util.get_column_definitions(
            _attr_map, long_listing=False)
        return (headers, (utils.get_dict_properties(obj, columns,
                                                    formatters=_formatters)
                          for obj in nuage_policy_groups))


class ShowNuagePolicyGroup(command.ShowOne):
    """Show information of a given Nuage policy group"""

    def get_parser(self, prog_name):
        parser = super(ShowNuagePolicyGroup, self).get_parser(prog_name)

        parser.add_argument(
            'nuage_policy_group',
            metavar="<nuage_policy_group>",
            help=_("nuage_policy_group to display (name or ID)")
        )

        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient
        # At this time client.find_resource is implemented using list instead
        # of show, that's why we have to do two calls. Once this is fixed
        # upstream we can reduce the number of calls
        policy_group_id = client.find_resource(
            'nuage_policy_group', parsed_args.nuage_policy_group)['id']
        obj = client.show_nuage_policy_group(policy_group_id)
        columns, display_columns = column_util.get_columns(
            obj['nuage_policy_group'], _attr_map)
        data = utils.get_dict_properties(
            obj['nuage_policy_group'], columns, formatters=_formatters)
        return display_columns, data
