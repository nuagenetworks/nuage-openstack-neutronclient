# Copyright 2017 NOKIA
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
from neutronclient.common import extension
from neutronclient.common import utils
from neutronclient.i18n import _
from neutronclient.neutron.v2_0 import router


class CreateRouter(extension.ClientExtensionCreate, router.CreateRouter):
    shell_command = 'router-create'
    object_path = '/routers'

    def add_known_arguments(self, parser):
        super(CreateRouter, self).add_known_arguments(parser)
        parser.add_argument(
            '--nuage-underlay',
            type=utils.convert_to_lowercase,
            choices=['off', 'route', 'snat'],
            help=_('Enable nuage underlay options.'))

    def args2body(self, parsed_args):
        body = super(CreateRouter, self).args2body(parsed_args)
        body['router']['nuage_underlay'] = parsed_args.nuage_underlay
        return body


class UpdateRouter(extension.ClientExtensionUpdate, router.UpdateRouter):
    shell_command = 'router-update'
    resource_path = '/routers/%s'

    def add_known_arguments(self, parser):
        super(UpdateRouter, self).add_known_arguments(parser)
        parser.add_argument(
            '--nuage-underlay',
            type=utils.convert_to_lowercase,
            choices=['off', 'route', 'snat'],
            help=_('Enable nuage underlay options.'))

    def args2body(self, parsed_args):
        body = super(UpdateRouter, self).args2body(parsed_args)
        body['router']['nuage_underlay'] = parsed_args.nuage_underlay
        return body
