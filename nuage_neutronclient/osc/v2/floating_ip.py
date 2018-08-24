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

from nuage_neutronclient.osc.v2.utils import update_dict
from openstack.network.v2.floating_ip import FloatingIP as OpenstackFloatingIP
from openstack import resource
from openstackclient.i18n import _
from openstackclient.network.v2 import floating_ip

openstack_get_attrs = floating_ip._get_attrs

# Add Nuage specific attributes to Openstack Floating IP
OpenstackFloatingIP.nuage_ingress_fip_rate_kbps = \
    resource.Body('nuage_ingress_fip_rate_kbps', type=int)
OpenstackFloatingIP.nuage_egress_fip_rate_kbps = \
    resource.Body('nuage_egress_fip_rate_kbps', type=int)


def nuage_get_attrs(client_manager, parsed_args):
    attrs = openstack_get_attrs(client_manager, parsed_args)

    update_dict(parsed_args, attrs,
                ['nuage_ingress_fip_rate_kbps', 'nuage_egress_fip_rate_kbps'])

    return attrs


def add_nuage_arguments(parser):
    parser.add_argument(
        '--nuage-ingress-fip-rate-kbps',
        type=int,
        help=_('Rate limiting applied to the floating IP in kbps for the '
               'ingress direction. Can be -1 for unlimited.'))
    parser.add_argument(
        '--nuage-egress-fip-rate-kbps',
        type=int,
        help=_('Rate limiting applied to the floating IP in kbps for the '
               'egress direction. Can be -1 for unlimited.'))


floating_ip._get_attrs = nuage_get_attrs


class CreateFloatingIP(floating_ip.CreateFloatingIP):

    def update_parser_common(self, parser):
        parser = super(CreateFloatingIP, self).update_parser_common(parser)
        add_nuage_arguments(parser)
        return parser


class SetFloatingIP(floating_ip.SetFloatingIP):

    def get_parser(self, prog_name):
        parser = super(SetFloatingIP, self).get_parser(prog_name)
        add_nuage_arguments(parser)
        return parser

    @staticmethod
    def _handle_nuage_specific_attributes(parsed_args, attrs):
        update_dict(parsed_args, attrs,
                    ['nuage_ingress_fip_rate_kbps',
                     'nuage_egress_fip_rate_kbps'])

    def take_action(self, parsed_args):
        """Same as method from base class but also handles nuage attrs"""
        client = self.app.client_manager.network
        attrs = {}
        # TODO(sindhu) Use client.find_ip() once SDK 0.9.15 is released
        obj = floating_ip._find_floating_ip(
            self.app.client_manager.sdk_connection.session,
            parsed_args.floating_ip,
            ignore_missing=False,
        )
        if parsed_args.port:
            port = client.find_port(parsed_args.port,
                                    ignore_missing=False)
            attrs['port_id'] = port.id

        if parsed_args.fixed_ip_address:
            attrs['fixed_ip_address'] = parsed_args.fixed_ip_address

        if parsed_args.qos_policy:
            attrs['qos_policy_id'] = client.find_qos_policy(
                parsed_args.qos_policy, ignore_missing=False).id

        if 'no_qos_policy' in parsed_args and parsed_args.no_qos_policy:
            attrs['qos_policy_id'] = None

        # Add Nuage specific attributes
        self._handle_nuage_specific_attributes(parsed_args, attrs)

        client.update_ip(obj, **attrs)


class ShowFloatingIP(floating_ip.ShowFloatingIP):
    pass
