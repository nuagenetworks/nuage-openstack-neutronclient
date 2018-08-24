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

from neutronclient.common import utils as neutron_utils
from nuage_neutronclient.osc.v2.utils import format_list_of_dicts

from openstackclient.network import sdk_utils
from osc_lib.command import command
from osc_lib import exceptions
from osc_lib import utils
from osc_lib.utils import columns as column_util

from nuage_neutronclient._i18n import _

LOG = logging.getLogger(__name__)

L2BRIDGE_RESOURCE = 'nuage_l2bridge'
L2BRIDGES_RESOURCE = 'nuage_l2bridges'

_formatters = {
    'physnets': format_list_of_dicts
}

# This is not a dict because order is important in nuage l2bridge list / show
_column_map = [('ID', 'id'), ('Name', 'name'),
               ('Nuage_subnet_id', 'nuage_subnet_id'),
               ('Physnets', 'physnets')]


def _get_columns(item):
    return sdk_utils.get_osc_show_columns_for_sdk_resource(item,
                                                           dict(_column_map))


def _parse_nuage_l2bridge_params(parsed_args):
    parsed = {}
    if parsed_args.name:
        parsed['name'] = parsed_args.name
    if parsed_args.physnet or getattr(parsed_args, 'no_physnet', None):
        parsed['physnets'] = parsed_args.physnet if parsed_args.physnet else []
    return parsed


def add_name_argument(parser, is_required):
    parser.add_argument(
        'name' if is_required else '--name',
        metavar='<name>',
        help=_('Name of the Nuage L2Bridge.'))


def add_physnet_argument(parser):
    parser.add_argument(
        '--physnet', metavar='physnet_name=PHYSNET,'
                             'segmentation_id=SEGMENTATIONID,'
                             'segmentation_type=SEGMENTATIONTYPE',
        action='append',
        type=neutron_utils.str2dict_type(
            required_keys=['physnet_name', 'segmentation_id',
                           'segmentation_type']),
        help=_('Desired physnet and segmentation id for this l2bridge: '
               'physnet_name=<name>,segmentation_id=<segmentation_id>, '
               'segmentation_type=<segmentation_type>. '
               'You can repeat this option.'))


class CreateNuageL2Bridge(command.ShowOne):
    """Create a new Nuage L2bridge"""

    def get_parser(self, prog_name):
        parser = super(CreateNuageL2Bridge, self).get_parser(prog_name)
        add_name_argument(parser, is_required=True)
        add_physnet_argument(parser)
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient
        attrs = _parse_nuage_l2bridge_params(parsed_args)
        obj = client.create_nuage_l2bridge({L2BRIDGE_RESOURCE: attrs})
        display_columns, columns = column_util.get_columns(
            obj[L2BRIDGE_RESOURCE])
        data = utils.get_dict_properties(obj[L2BRIDGE_RESOURCE], columns,
                                         formatters=_formatters)
        return display_columns, data


class DeleteNuageL2Bridge(command.Command):
    """Delete a given Nuage L2bridge"""

    def get_parser(self, prog_name):
        parser = super(DeleteNuageL2Bridge, self).get_parser(prog_name)
        parser.add_argument(
            L2BRIDGES_RESOURCE,
            metavar='<nuage-l2bridge>',
            nargs='+',
            help=_('Nuage L2bridge to delete (name or ID)'))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient
        result = 0
        for l2bridge in parsed_args.nuage_l2bridges:
            try:
                l2bridge_id = client.find_resource(
                    L2BRIDGE_RESOURCE, l2bridge)['id']
                client.delete_nuage_l2bridge(l2bridge_id)
            except Exception as e:
                result += 1
                LOG.error(_("Failed to delete nuage l2bridge with "
                            "name or ID '%(nuage_l2bridge)s': %(e)s"),
                          {L2BRIDGE_RESOURCE: l2bridge, 'e': e})

        if result > 0:
            total = len(parsed_args.nuage_l2bridges)
            msg = (_("%(result)s of %(total)s nuage l2bridge(s) "
                     "failed to delete.") % {'result': result, 'total': total})
            raise exceptions.CommandError(msg)


class SetNuageL2Bridge(command.Command):
    """Set Nuage L2bridge properties"""

    def get_parser(self, prog_name):
        parser = super(SetNuageL2Bridge, self).get_parser(prog_name)
        parser.add_argument(
            'nuage_l2bridge',
            metavar="<nuage_l2bridge>",
            help=_("nuage_l2bridge to set (name or ID)")
        )
        add_name_argument(parser, is_required=False)
        add_physnet_argument(parser)
        parser.add_argument(
            '--no-physnet',
            action='store_true',
            help=_("Clear existing information of physnets."
                   "Specify both --physnet and --no-physnet "
                   "to overwrite the current physnet(s).")
        )
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient
        obj = client.find_resource(L2BRIDGE_RESOURCE,
                                   parsed_args.nuage_l2bridge)
        # BUG OPENSTACK-2500
        for i in range(len(obj['physnets'])):
            physnet = obj['physnets'][i]
            physnet['physnet_name'] = physnet.pop('physnet')

        attrs = _parse_nuage_l2bridge_params(parsed_args)

        if not parsed_args.no_physnet and parsed_args.physnet:
            attrs['physnets'].extend(obj['physnets'])

        try:
            client.update_nuage_l2bridge(obj['id'],
                                         {L2BRIDGE_RESOURCE: attrs})
        except Exception as e:
            msg = (_("Failed to set Nuage L2bridge '%(l2bridge)s': %(e)s")
                   % {'l2bridge': parsed_args.nuage_l2bridge, 'e': e})
            raise exceptions.CommandError(msg)


class ListNuageL2Bridge(command.Lister):
    """List Nuage L2bridges"""

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient

        headers, attrs = utils.calculate_header_and_attrs(
            column_headers=[x[0] for x in _column_map],
            attrs=[x[1] for x in _column_map],
            parsed_args=parsed_args)

        obj = client.list_nuage_l2bridges()[L2BRIDGES_RESOURCE]
        return (headers, (utils.get_dict_properties(
            s, attrs, formatters=_formatters) for s in obj))


class ShowNuageL2Bridge(command.ShowOne):
    """Show information of a given Nuage l2bridge"""

    def get_parser(self, prog_name):
        parser = super(ShowNuageL2Bridge, self).get_parser(prog_name)

        parser.add_argument(
            'nuage_l2bridge',
            metavar="<nuage_l2bridge>",
            help=_("nuage_l2bridge to display (name or ID)")
        )

        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient
        # At this time client.find_resource is implemented using list instead
        # of show, that's why we have to do two calls. Once this is fixed
        # upstream we can reduce the number of calls
        l2bridge_id = client.find_resource(L2BRIDGE_RESOURCE,
                                           parsed_args.nuage_l2bridge)['id']
        obj = client.show_nuage_l2bridge(l2bridge_id)[L2BRIDGE_RESOURCE]
        display_columns, columns = _get_columns(obj)
        data = utils.get_dict_properties(obj, columns, formatters=_formatters)
        return display_columns, data
