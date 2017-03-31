# Copyright 2017 Nokia.
# All Rights Reserved.
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

from networking_sfc._i18n import _
from networking_sfc.cli import flow_classifier as neutron_flw_classifier

neutron_parser = (neutron_flw_classifier.FlowClassifierCreate.
                  add_known_arguments)
neutron_arg2body = neutron_flw_classifier.FlowClassifierCreate.args2body


def _fill_protocol_vlan_info(body, vlan_val):
    min_vlan, sep, max_vlan = vlan_val.partition(":")
    if not min_vlan:
        min_vlan = '1'
    if not max_vlan and ":" not in vlan_val:
        max_vlan = min_vlan
    if not max_vlan and ":" in vlan_val:
        max_vlan = '4094'
    body['vlan_range_min'] = int(min_vlan)
    body['vlan_range_max'] = int(max_vlan)


def nuage_add_known_arguments(self, parser):
    neutron_parser(self, parser)
    parser.add_argument(
        '--vlan',
        help=_('VLAN range. Must be specified as a:b,'
               ' where a=min-vlan and b=max-vlan.'))


def nuage_args2body(self, parsed_args):
    body = neutron_arg2body(self, parsed_args)
    if parsed_args.vlan:
        _fill_protocol_vlan_info(body[self.resource],
                                 parsed_args.vlan)
    return body

neutron_flw_classifier.FlowClassifierCreate.add_known_arguments =\
    nuage_add_known_arguments
neutron_flw_classifier.FlowClassifierCreate.args2body = nuage_args2body
