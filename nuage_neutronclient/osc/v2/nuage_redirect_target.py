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
             ('redundancy_enabled', 'Redundancy Enabled',
              column_util.LIST_BOTH),
             ('insertion_mode', 'Insertion Mode', column_util.LIST_BOTH),
             ('ports', 'Ports', column_util.LIST_LONG_ONLY))


class ListNuageRedirectTarget(command.Lister):
    """List Nuage Redirect Target"""

    def get_parser(self, prog_name):
        parser = super(ListNuageRedirectTarget, self).get_parser(prog_name)
        parser.add_argument(
            'subnet', metavar='<subnet>',
            help=_('ID or name of subnet to look up Redirect Target for.'))
        return parser

    def take_action(self, parsed_args):
        neutronclient = self.app.client_manager.neutronclient
        nuageclient = self.app.client_manager.nuageclient

        subnet_id = neutronclient.find_resource('subnet',
                                                parsed_args.subnet)['id']
        nuage_redirect_targets = nuageclient.list_nuage_redirect_targets(
            subnet=subnet_id)['nuage_redirect_targets']

        headers, columns = column_util.get_column_definitions(
            _attr_map, long_listing=False)
        return (headers, (utils.get_dict_properties(obj, columns,
                                                    formatters=_formatters)
                          for obj in nuage_redirect_targets))


class ShowNuageRedirectTarget(command.ShowOne):
    """Show information of a given Nuage Redirect Target"""

    def get_parser(self, prog_name):
        parser = super(ShowNuageRedirectTarget, self).get_parser(prog_name)

        parser.add_argument(
            'nuage_redirect_target',
            metavar="<nuage_redirect_target>",
            help=_("nuage_redirect_target to display (name or ID)")
        )

        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient
        # At this time client.find_resource is implemented using list instead
        # of show, that's why we have to do two calls. Once this is fixed
        # upstream we can reduce the number of calls
        redirect_target_id = client.find_resource(
            'nuage_redirect_target', parsed_args.nuage_redirect_target)['id']

        obj = client.show_nuage_redirect_target(redirect_target_id)
        columns, display_columns = column_util.get_columns(
            obj['nuage_redirect_target'], _attr_map)
        data = utils.get_dict_properties(
            obj['nuage_redirect_target'], columns, formatters=_formatters)
        return display_columns, data
