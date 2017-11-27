# Copyright 2016 Alcatel-Lucent USA Inc.
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
from neutronclient.common import exceptions
from neutronclient.common import extension
from neutronclient.common import utils
from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronV20
from neutronclient.neutron.v2_0 import subnet


class CreateSubnet(extension.ClientExtensionCreate,
                   subnet.CreateSubnet):
    shell_command = 'subnet-create'
    object_path = '/subnets'

    def add_known_arguments(self, parser):
        super(CreateSubnet, self).add_known_arguments(parser)
        parser.add_argument(
            '--net-partition',
            help=_('ID or name of the net partition.'))
        parser.add_argument(
            '--nuagenet',
            help=_('ID of the subnet or l2domain on the VSD.'))
        parser.add_argument(
            '--nuage-uplink',
            help=_('ID of the shared resource zone on the VSD.'))
        utils.add_boolean_argument(
            parser, '--underlay',
            help=_('Whether to enable or disable underlay for shared '
                   'networks'))

    def args2body(self, parsed_args):
        body = super(CreateSubnet, self).args2body(parsed_args)
        if ((parsed_args.nuagenet is not None) and
                (parsed_args.net_partition is None)):
            msg = _("'nuagenet' and 'net_partition' parameters should both be "
                    "given for creating a vsd-managed subnet.")
            raise exceptions.NeutronClientException(message=msg,
                                                    status_code=400)
        neutronV20.update_dict(parsed_args, body['subnet'],
                               ['net_partition', 'nuagenet', 'nuage_uplink',
                                'underlay'])
        return body


class UpdateSubnet(extension.ClientExtensionUpdate,
                   subnet.UpdateSubnet):
    shell_command = 'subnet-update'
    resource_path = '/subnets/%s'

    def add_known_arguments(self, parser):
        super(UpdateSubnet, self).add_known_arguments(parser)
        parser.add_argument(
            '--nuage-underlay',
            type=utils.convert_to_lowercase,
            choices=['off', 'route', 'snat', 'inherited'],
            help=_('Enable nuage underlay options.'))

    def args2body(self, parsed_args):
        body = super(UpdateSubnet, self).args2body(parsed_args)
        body['subnet']['nuage_underlay'] = parsed_args.nuage_underlay
        return body
