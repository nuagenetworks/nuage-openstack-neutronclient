# Copyright 2016 NEC Corporation
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

from openstack.network.v2.router import Router as router_resource
from openstack import resource
from openstackclient.network.v2 import router
from osc_lib import utils as osc_lib_utils

from nuage_neutronclient._i18n import _


# Add Nuage specific attributes
router_resource.nuage_net_partition = resource.Body('net_partition')
router_resource.nuage_rt = resource.Body('rt')
router_resource.nuage_rd = resource.Body('rd')
router_resource.nuage_backhaul_vnid = resource.Body('nuage_backhaul_vnid')
router_resource.nuage_backhaul_rd = resource.Body('nuage_backhaul_rd')
router_resource.nuage_backhaul_rt = resource.Body('nuage_backhaul_rt')
router_resource.nuage_router_template = resource.Body('nuage_router_template')
router_resource.nuage_tunnel_type = resource.Body('tunnel_type')
router_resource.nuage_ecmp_count = resource.Body('ecmp_count')
router_resource.nuage_underlay = resource.Body('nuage_underlay')
router_resource.nuage_aggregate_flows = resource.Body('nuage_aggregate_flows')


def add_create_update_attributes(parser):
    parser.add_argument(
        '--nuage-net-partition',
        metavar='<nuage-net-partition>',
        help=_('Nuage net partition'))

    parser.add_argument(
        '--nuage-rd',
        metavar='<nuage-rd>',
        help=_('Nuage Route Distinguisher'))

    parser.add_argument(
        '--nuage-rt',
        metavar='<nuage-rt>',
        help=_('Nuage Route Target'))

    parser.add_argument(
        '--nuage-backhaul-vnid',
        metavar='<nuage-backhaul-vnid>',
        help=_('Nuage Backhaul VNID'))

    parser.add_argument(
        '--nuage-backhaul-rd',
        metavar='<nuage-backhaul-rd>',
        help=_('Nuage Backhaul Route Distinguisher'))

    parser.add_argument(
        '--nuage-backhaul-rt',
        metavar='<nuage-backhaul-rt>',
        help=_('Nuage Backhaul Route Target'))

    parser.add_argument(
        '--nuage-tunnel-type',
        choices=['VXLAN', 'GRE', 'DEFAULT'],
        help=_('Nuage tunnel type'))

    parser.add_argument(
        '--nuage-ecmp-count',
        metavar='<nuage-ecmp-count>',
        help=_('Nuage ECMP count'))

    parser.add_argument(
        '--nuage-underlay',
        choices=['off', 'route', 'snat'],
        help=_('Enable nuage underlay options'))

    parser.add_argument(
        '--nuage-aggregate-flows',
        choices=['off', 'route', 'pbr'],
        help=_('Enable nuage aggregate flow options: Choose between no '
               'aggregate flows or route/pbr based aggragate flows enabled.'))


super_get_attrs = router._get_attrs


def _get_attrs(client_manager, parsed_args):
    attrs = super_get_attrs(client_manager, parsed_args)
    if parsed_args.nuage_net_partition:
        attrs['net_partition'] = parsed_args.nuage_net_partition
    if parsed_args.nuage_rt:
        attrs['rt'] = parsed_args.nuage_rt
    if parsed_args.nuage_rd:
        attrs['rd'] = parsed_args.nuage_rd
    if parsed_args.nuage_backhaul_vnid:
        attrs['nuage_backhaul_vnid'] = parsed_args.nuage_backhaul_vnid
    if parsed_args.nuage_backhaul_rd:
        attrs['nuage_backhaul_rd'] = parsed_args.nuage_backhaul_rd
    if parsed_args.nuage_backhaul_rt:
        attrs['nuage_backhaul_rt'] = parsed_args.nuage_backhaul_rt
    if getattr(parsed_args, 'nuage_router_template', None):  # only for create
        attrs['nuage_router_template'] = parsed_args.nuage_router_template
    if parsed_args.nuage_tunnel_type:
        attrs['tunnel_type'] = parsed_args.nuage_tunnel_type
    if parsed_args.nuage_ecmp_count:
        attrs['ecmp_count'] = parsed_args.nuage_ecmp_count
    if parsed_args.nuage_underlay:
        attrs['nuage_underlay'] = parsed_args.nuage_underlay
    if parsed_args.nuage_aggregate_flows:
        attrs['nuage_aggregate_flows'] = parsed_args.nuage_aggregate_flows

    return attrs


# router._get_columns = _get_columns
router._get_attrs = _get_attrs


class CreateRouter(router.CreateRouter):
    def get_parser(self, prog_name):
        parser = super(CreateRouter, self).get_parser(prog_name)

        add_create_update_attributes(parser)

        parser.add_argument(
            '--nuage-router-template',
            metavar='<nuage-router-template>',
            help=_('Nuage Router Template'))

        return parser


class ShowRouter(router.ShowRouter):

    def _handle_nuage_specific_attributes(self, router):
        """Fetch extra Nuage attributes for the router that we have to show"""

        if not router:
            return

        nuageclient = self.app.client_manager.nuageclient

        # Fetch l3domain
        domain = nuageclient.get_l3domain(router.id)

        if domain:
            router.nuage_net_partition = domain.get('net_partition_id')
            router.nuage_rd = domain.get('rd')
            router.nuage_rt = domain.get('rt')
            router.nuage_backhaul_vnid = domain.get('backhaul_vnid')
            router.nuage_backhaul_rd = domain.get('backhaul_rd')
            router.nuage_backhaul_rt = domain.get('backhaul_rt')
            router.nuage_router_template = domain.get('router_template_id')
            router.nuage_tunnel_type = domain.get('tunnel_type')
            router.nuage_ecmp_count = domain.get('ecmp_count')

    def take_action(self, parsed_args):
        """Adaptation of the upstream method supporting nuage data"""

        client = self.app.client_manager.network
        obj = client.find_router(parsed_args.router, ignore_missing=False)
        interfaces_info = []
        filters = {}
        filters['device_id'] = obj.id
        for port in client.ports(**filters):
            if port.device_owner != "network:router_gateway":
                for ip_spec in port.fixed_ips:
                    int_info = {
                        'port_id': port.id,
                        'ip_address': ip_spec.get('ip_address'),
                        'subnet_id': ip_spec.get('subnet_id')
                    }
                    interfaces_info.append(int_info)

        setattr(obj, 'interfaces_info', interfaces_info)

        self._handle_nuage_specific_attributes(obj)

        display_columns, columns = router._get_columns(obj)
        router._formatters['interfaces_info'] = router._format_router_info
        data = osc_lib_utils.get_item_properties(obj, columns,
                                                 formatters=router._formatters)

        return display_columns, data


class SetRouter(router.SetRouter):
    def get_parser(self, prog_name):
        parser = super(SetRouter, self).get_parser(prog_name)
        add_create_update_attributes(parser)
        return parser
