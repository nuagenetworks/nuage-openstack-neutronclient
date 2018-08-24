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

"""OpenStackClient plugin for Nuage service."""

import logging

# from nuage_neutronclient.api.v2 import octavia
from osc_lib import utils

LOG = logging.getLogger(__name__)

DEFAULT_API_VERSION = '2.0'
API_VERSION_OPTION = 'os_nuageclient_api_version'
API_NAME = 'nuageclient'
API_TYPE = 'nuageclient'
API_VERSIONS = {
    '2.0': 'nuage_neutronclient.osc.v2.client.Client',
    '2': 'nuage_neutronclient.osc.v2.client.Client',
}


def make_client(instance):
    """Returns a nuage service client"""
    nuage_client = utils.get_client_class(
        API_NAME,
        instance._api_version[API_NAME],
        API_VERSIONS)
    LOG.debug('Instantiating nuage client: %s', nuage_client)

    client = nuage_client(session=instance.session,
                          region_name=instance.region_name,
                          endpoint_type=instance.interface,
                          insecure=not instance.verify,
                          ca_cert=instance.cacert)
    return client


def build_option_parser(parser):
    """Hook to add global options

    Called from openstackclient.shell.OpenStackShell.__init__()
    after the builtin parser has been initialized. This is
    where a plugin can add global options such as an API version.

    :param argparse.ArgumentParser parser: The parser object that
        has been initialized by OpenStackShell.
    """
    parser.add_argument(
        '--os-nuageclient-api-version',
        metavar='<nuageclient-api-version>',
        default=utils.env(
            'OS_NUAGECLIENT_API_VERSION',
            default=DEFAULT_API_VERSION),
        help='OSC Plugin API version, default=' +
             DEFAULT_API_VERSION +
             ' (Env: OS_NUAGECLIENT_API_VERSION)')
    return parser
