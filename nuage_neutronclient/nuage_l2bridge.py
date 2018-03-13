# Copyright 2018 NOKIA
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from oslo_serialization import jsonutils

from neutronclient.common import extension
from neutronclient.common import utils
from neutronclient.i18n import _


def _format_physnets(l2bridge):
    try:
        return '\n'.join([jsonutils.dumps(physnet) for physnet
                          in l2bridge['physnets']])
    except (TypeError, KeyError):
        return ''


class NuageL2Bridge(extension.NeutronClientExtension):
    resource = 'nuage_l2bridge'
    resource_plural = '%ss' % resource
    object_path = '/nuage-l2bridges'
    resource_path = '/nuage-l2bridges/%s'
    versions = ['2.0']
    allow_names = True


class NuageL2BridgeCreate(extension.ClientExtensionCreate, NuageL2Bridge):
    """Create Nuage L2Bridge"""
    shell_command = 'nuage-l2bridge-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            'name',
            metavar='name',
            help=_('Name of the Nuage L2Bridge.'))
        parser.add_argument(
            '--physnet', metavar='physnet_name=PHYSNET,'
                                 'segmentation_id=SEGMENTATIONID,'
                                 'segmentation_type=SEGMENTATIONTYPE',
            action='append',
            type=utils.str2dict_type(
                required_keys=['physnet_name', 'segmentation_id',
                               'segmentation_type']),
            help=_('Desired physnet and segmentation id for this l2bridge: '
                   'physnet_name=<name>,segmentation_id=<segmentation_id>, '
                   'segmentation_type=<segmentation_type>. '
                   'You can repeat this option.'))
        return parser

    def args2body(self, args):
        body = {}
        if args.name:
            body['name'] = args.name

        if args.physnet:
            physnets = []
            for physnet in args.physnet:
                physnets.append(physnet)
            body['physnets'] = physnets
        return {'nuage_l2bridge': body}


class NuageL2BridgeUpdate(extension.ClientExtensionUpdate, NuageL2Bridge):
    """Update Nuage L2Bridge"""
    shell_command = 'nuage-l2bridge-update'

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--name',
            metavar='name',
            help=_('Name of the Nuage L2Bridge.'))
        parser.add_argument(
            '--physnet', metavar='physnet_name=PHYSNET,'
                                 'segmentation_id=SEGMENTATIONID,'
                                 'segmentation_type=SEGMENTATIONTYPE',
            action='append',
            type=utils.str2dict_type(
                required_keys=['physnet_name', 'segmentation_id',
                               'segmentation_type']),
            help=_('Desired physnet and segmentation id for this l2bridge: '
                   'physnet_name=<name>,segmentation_id=<segmentation_id>, '
                   'segmentation_type=<segmentation_type>. '
                   'You can repeat this option.'))
        return parser

    def args2body(self, args):
        body = {}
        if args.name:
            body['name'] = args.name

        if args.physnet:
            physnets = []
            for physnet in args.physnet:
                physnets.append(physnet)
            body['physnets'] = physnets
        return {'nuage_l2bridge': body}


class NuageL2BridgeList(extension.ClientExtensionList, NuageL2Bridge):
    """List nuage L2Bridges."""

    shell_command = 'nuage-l2bridge-list'
    list_columns = ['id', 'name', 'nuage_subnet_id', 'physnets']
    _formatters = {'physnets': _format_physnets}

    pagination_support = True
    sorting_support = True


class NuageL2BridgeShow(extension.ClientExtensionShow,
                        NuageL2Bridge):
    """Show a given Nuage L2bridge."""
    shell_command = 'nuage-l2bridge-show'


class NuageL2Bridgedelete(extension.ClientExtensionDelete, NuageL2Bridge):
    """Delete a given Nuage L2bridge"""
    shell_command = 'nuage-l2bridge-delete'
