# Copyright 2015 Alcatel-Lucent USA Inc.
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
#

import logging
import re
import six

from oslo.serialization import jsonutils
from neutronclient.common import exceptions
from neutronclient.common import extension
from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronV20

HEX_ELEM = '[0-9A-Fa-f]'
UUID_PATTERN = '-'.join([HEX_ELEM + '{8}', HEX_ELEM + '{4}',
                         HEX_ELEM + '{4}', HEX_ELEM + '{4}',
                         HEX_ELEM + '{12}'])


def _format_fixed_ips(appdport):
    try:
        return '\n'.join(
            [jsonutils.dumps(ip) for ip in appdport['fixed_ips']])
    except (TypeError, KeyError):
        return ''


def _format_fixed_ips_csv(appdport):
    try:
        return jsonutils.dumps(appdport['fixed_ips'])
    except (TypeError, KeyError):
        return ''


class ApplicationDomain(extension.NeutronClientExtension):

    resource = 'application_domain'
    resource_plural = '%ss' % resource
    object_path = '/%s' % 'application-domains'
    resource_path = '/%s/%%s' % 'application-domains'
    versions = ['2.0']


class ApplicationDomainList(extension.ClientExtensionList,
                            ApplicationDomain):
    """List all application domains."""
    shell_command = 'nuage-applicationdomain-list'
    list_columns = ['id', 'name', 'rd', 'rt', 'tunnel_type']
    pagination_support = True
    sorting_support = True


class ApplicationDomainDelete(extension.ClientExtensionDelete,
                              ApplicationDomain):
    """Delete an application domain."""
    shell_command = 'nuage-applicationdomain-delete'


class ApplicationDomainShow(extension.ClientExtensionShow,
                            ApplicationDomain):
    """Show information of a given application domain."""
    shell_command = 'nuage-applicationdomain-show'


class ApplicationDomainCreate(extension.ClientExtensionCreate,
                              ApplicationDomain):
    """Create an application domain."""
    shell_command = 'nuage-applicationdomain-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            'name', metavar='name',
            help='Name of domain for application deployment.')
        parser.add_argument(
            '--nuage-domain-template',
            help='ID of the domian template that will be used'
                 ' to instantiate the application domain'),
        parser.add_argument(
            '--rd',
            help='Route Distinguisher for application deployment.'),
        parser.add_argument(
            '--rt',
            help='Route Target for application deployment.'),
        parser.add_argument(
            '--tunnel-type',
            help='Tunnel type for application deployment.'),

    def args2body(self, parsed_args):
        body = {'application_domain': {'name': parsed_args.name}, }
        if parsed_args.nuage_domain_template:
            body['application_domain'].update(
                {'nuage_domain_template': parsed_args.nuage_domain_template})
        if parsed_args.rd:
            body['application_domain'].update({'rd': parsed_args.rd})
        if parsed_args.rt:
            body['application_domain'].update({'rt': parsed_args.rt})
        if parsed_args.tunnel_type:
            body['application_domain'].update({'tunnel_type': parsed_args.tunnel_type})
        return body


def add_appdomain_updatable_arguments(parser):
    parser.add_argument(
        '--name',
        help=_('Name of this application domain.'))
    parser.add_argument(
        '--description',
        help=_('Description of this application domain.'))


def appdomain_updatable_args2body(parsed_args, body):
    if parsed_args.name:
        body['application_domain'].update({'name': parsed_args.name})
    if parsed_args.description:
        body['application_domain'].update(
            {'description': parsed_args.description})


class ApplicationDomainUpdate(extension.ClientExtensionUpdate,
                              ApplicationDomain):
    """Update information of a given application domain."""
    shell_command = 'nuage-applicationdomain-update'

    def add_known_arguments(self, parser):
        add_appdomain_updatable_arguments(parser)

    def args2body(self, parsed_args):
        body = {'application_domain': {}}
        appdomain_updatable_args2body(parsed_args, body)
        return body


class Application(extension.NeutronClientExtension):

    resource = 'application'
    resource_plural = '%ss' % resource
    object_path = '/%s' % 'applications'
    resource_path = '/%s/%%s' % 'applications'
    versions = ['2.0']


class ApplicationList(extension.ClientExtensionList,
                      Application):
    """List all applications."""
    shell_command = 'nuage-application-list'
    list_columns = ['id', 'name', 'associateddomainid']
    pagination_support = True
    sorting_support = True


class ApplicationShow(extension.ClientExtensionShow,
                      Application):
    """Show information of a given application."""
    shell_command = 'nuage-application-show'


class ApplicationCreate(extension.ClientExtensionCreate,
                        Application):
    """Create an application."""
    shell_command = 'nuage-application-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            'name', metavar='name',
            help='Name of the application to be deployed.'
        )
        parser.add_argument(
            '--applicationdomain-id',
            help='Application Deployment router ID or name.'),
        parser.add_argument(
            '--description',
            help='Description of the Application being created.'),

    def args2body(self, parsed_args):
        body = {'application': {'name': parsed_args.name}, }
        if parsed_args.applicationdomain_id:
            body['application'].update(
                {'applicationdomain_id': parsed_args.applicationdomain_id})
        if parsed_args.description:
            body['application'].update(
                {'description': parsed_args.description})

        if not parsed_args.applicationdomain_id:
            raise exceptions.CommandError(_("Usage: neutron"
                                            " nuage-application-create"
                                            " --applicationdomain-id"
                                            " <apprtr-id>"))
        return body


class ApplicationDelete(extension.ClientExtensionDelete,
                        Application):
    """Delete an application."""
    shell_command = 'nuage-application-delete'


def add_app_updatable_arguments(parser):
    parser.add_argument(
        '--name',
        help=_('Name of this application.'))
    parser.add_argument(
        '--description',
        help=_('Description of this application.'))


def app_updatable_args2body(parsed_args, body):
    if parsed_args.name:
        body['application'].update(
            {'name': parsed_args.name})
    if parsed_args.description:
        body['application'].update(
            {'description': parsed_args.description})


class ApplicationUpdate(extension.ClientExtensionUpdate,
                        Application):
    """Update information of a given application."""
    shell_command = 'nuage-application-update'

    def add_known_arguments(self, parser):
        add_app_updatable_arguments(parser)

    def args2body(self, parsed_args):
        body = {'application': {}}
        app_updatable_args2body(parsed_args, body)
        return body


class Tier(extension.NeutronClientExtension):

    resource = 'tier'
    resource_plural = '%ss' % resource
    object_path = '/%s' % 'tiers'
    resource_path = '/%s/%%s' % 'tiers'
    versions = ['2.0']


class TierList(extension.ClientExtensionList, Tier):
    """List all tiers."""
    shell_command = 'nuage-tier-list'
    list_columns = ['id', 'name', 'type', 'associatedappid']
    pagination_support = True
    sorting_support = True

    def get_parser(self, prog_name):
        parser = super(TierList, self).get_parser(prog_name)
        parser.add_argument(
            'app_id', metavar='app-id',
            help=_('ID of the application where you'
                   ' want to look up for tiers.'))
        return parser

    def get_data(self, parsed_args):
        if not parsed_args.app_id:
            message = (_("Please provide the Aplication ID."
                         " Ex. neutron nuage-tier-list APP_ID"))
            raise exceptions.CommandError(message=message)
        self.values_specs.append('--app_id=%s' % parsed_args.app_id)
        return super(TierList, self).get_data(parsed_args)


class TierShow(extension.ClientExtensionShow, Tier):
    """Show information of a given tier."""
    shell_command = 'nuage-tier-show'
    log = logging.getLogger(__name__ + '.ShowTier')
    allow_names = False


class TierCreate(extension.ClientExtensionCreate, Tier):
    """Create a tier."""
    shell_command = 'nuage-tier-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            'name', metavar='name',
            help='Name of router for application deployment.'
        )
        parser.add_argument(
            '--app-id',
            help='Application ID where you want to attach'
                 ' the tier.'),
        parser.add_argument(
            '--fip-pool-id',
            help='Floating IP Pool ID you want to associate'
                 ' with the tier.'),
        parser.add_argument(
            '--cidr',
            help='CIDR of the tier to be attached.'),
        parser.add_argument(
            '--type',
            choices=['STANDARD', 'NETWORK_MACRO',
                     'APPLICATION', 'APPLICATION_EXTENDED_NETWORK'],
            help='Type of the tier to be attached.'),

    def args2body(self, parsed_args):
        body = {'tier': {'name': parsed_args.name}, }
        if parsed_args.app_id:
            body['tier'].update({'app_id': parsed_args.app_id})
        if parsed_args.fip_pool_id:
            body['tier'].update({'fip_pool_id': parsed_args.fip_pool_id})
        if parsed_args.cidr:
            if parsed_args.cidr.endswith('/32'):
                self.log.warning(_("An IPv4 subnet with a /32 CIDR will have "
                                   "only one usable IP address so the device "
                                   "attached to it will not have any IP "
                                   "connectivity."))
            body['tier'].update({'cidr': parsed_args.cidr})
        if parsed_args.type:
            body['tier'].update({'type': parsed_args.type})

        if not parsed_args.app_id or not parsed_args.type:
            raise exceptions.CommandError(_("Application ID and Type are"
                                            " mandatory parameters for tier"
                                            " creation."
                                            " Usage: neutron nuage-tier-create"
                                            " <tier-name>"
                                            " --app-id <Application ID>"
                                            " --type <Type of tier>"))

        if parsed_args.type != 'STANDARD' and parsed_args.fip_pool_id:
            raise exceptions.CommandError(_("FIP Pool ID is applicable only"
                                            " for tier creation of type"
                                            " 'STANDARD'"))

        if ((parsed_args.type == 'STANDARD'
                or parsed_args.type == 'NETWORK_MACRO')
                and not parsed_args.cidr):
            raise exceptions.CommandError(_("CIDR is a mandatory parameter for"
                                            " tier creation of type"
                                            " 'STANDARD' and 'NETWORK_MACRO'"))
        return body


class TierDelete(extension.ClientExtensionDelete, Tier):
    """Delete a tier."""
    shell_command = 'nuage-tier-delete'
    allow_names = False


def add_tier_updatable_arguments(parser):
    parser.add_argument(
        '--name',
        help=_('Name of this tier.'))
    parser.add_argument(
        '--description',
        help=_('Description of this tier.'))


def tier_updatable_args2body(parsed_args, body):
    if parsed_args.name:
        body['tier'].update({'name': parsed_args.name})
    if parsed_args.description:
        body['tier'].update(
            {'description': parsed_args.description})


class TierUpdate(extension.ClientExtensionUpdate, Tier):
    """Update information of a given tier."""
    shell_command = 'nuage-tier-update'

    def add_known_arguments(self, parser):
        add_tier_updatable_arguments(parser)

    def args2body(self, parsed_args):
        body = {'tier': {}}
        tier_updatable_args2body(parsed_args, body)
        return body


class Appdport(extension.NeutronClientExtension):

    resource = 'appdport'
    resource_plural = '%ss' % resource
    object_path = '/%s' % 'appdports'
    resource_path = '/%s/%%s' % 'appdports'
    versions = ['2.0']


class AppdportList(extension.ClientExtensionList, Appdport):
    """List all application designer ports."""
    shell_command = 'nuage-appdport-list'
    resource = 'appdport'
    _formatters = {'fixed_ips': _format_fixed_ips, }
    _formatters_csv = {'fixed_ips': _format_fixed_ips_csv, }
    list_columns = ['id', 'name', 'mac_address', 'fixed_ips', 'device_id']
    pagination_support = True
    sorting_support = True


class AppdportShow(extension.ClientExtensionShow, Appdport):
    """Show information of a given application designer port."""
    shell_command = 'nuage-appdport-show'
    resource = 'appdport'

    def execute(self, parsed_args):
        neutron_client = self.get_client()
        neutron_client.format = parsed_args.request_format
        params = {}
        res_id = neutronV20.find_resourceid_by_name_or_id(
            neutron_client, 'port', parsed_args.id)
        obj_shower = getattr(neutron_client, "show_%s" % 'appdport')
        data = obj_shower(res_id, **params)
        self.format_output_data(data)
        resp_dict = data[self.resource]
        if self.resource in data:
            for k, v in six.iteritems(resp_dict):
                if isinstance(v, list):
                    value = ""
                    for _item in v:
                        if value:
                            value += "\n"
                        if isinstance(_item, dict):
                            value += jsonutils.dumps(_item)
                        else:
                            value += str(_item)
                    resp_dict[k] = value
                elif v is None:
                    resp_dict[k] = ''
            return zip(*sorted(six.iteritems(resp_dict)))
        else:
            return None


class AppdportCreate(extension.ClientExtensionCreate, Appdport):
    """Create an application designer port."""
    shell_command = 'nuage-appdport-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            'name', metavar='name',
            help='Name of router for application deployment.'
        )
        parser.add_argument(
            '--tier-id',
            help='Application Deployment tier ID.'),

    def args2body(self, parsed_args):
        body = {'appdport': {'name': parsed_args.name}, }
        if parsed_args.tier_id:
            body['appdport'].update({'tier_id': parsed_args.tier_id})
        else:
            raise exceptions.CommandError(_("Tier-Id is a mandatory"
                                            " parameter to create a"
                                            " App. Designer port on a tier."
                                            " Usage: neutron"
                                            " nuage-appdport-create"
                                            " --tier-id <tier-id>"))
        return body


class AppdportDelete(extension.ClientExtensionDelete, Appdport):
    """Delete an application designer port."""
    shell_command = 'nuage-appdport-delete'
    resource = 'appdport'

    def run(self, parsed_args):
        neutron_client = self.get_client()
        neutron_client.format = parsed_args.request_format
        res_id = neutronV20.find_resourceid_by_name_or_id(neutron_client,
                                                          'port',
                                                          parsed_args.id)
        obj_deleter = getattr(neutron_client, "delete_%s" % 'appdport')
        match = re.match(UUID_PATTERN, str(res_id))
        if match:
            obj_deleter(res_id)
            print((_('Deleted %(resource)s: %(res_id)s')
                   % {'res_id': parsed_args.id,
                      'resource': self.resource}))
        else:
            obj_deleter(parsed_args.id)
            print((_('Deleted %(resource)s: %(res_id)s')
                   % {'res_id': res_id,
                      'resource': self.resource}))


def add_appdport_updatable_arguments(parser):
    parser.add_argument(
        '--name',
        help=_('Name of the application designer port.'))
    parser.add_argument(
        '--description',
        help=_('Description of the application designer port.'))


def appdport_updatable_args2body(parsed_args, body):
    if parsed_args.name:
        body['appdport'].update({'name': parsed_args.name})
    if parsed_args.description:
        body['appdport'].update({'description': parsed_args.description})


class AppdportUpdate(extension.ClientExtensionUpdate, Appdport):
    """Update information of a given application designer port."""
    shell_command = 'nuage-appdport-update'

    def add_known_arguments(self, parser):
        add_appdport_updatable_arguments(parser)

    def args2body(self, parsed_args):
        body = {'appdport': {}}
        appdport_updatable_args2body(parsed_args, body)
        return body


class Service(extension.NeutronClientExtension):
    resource = 'service'
    resource_plural = '%ss' % resource
    object_path = '/%s' % 'services'
    resource_path = '/%s/%%s' % 'services'
    versions = ['2.0']


class ServiceList(extension.ClientExtensionList, Service):
    """List all services."""
    shell_command = 'nuage-service-list'

    list_columns = ['id', 'name', 'direction', 'protocol',
                    'dscp', 'ethertype', 'src_port', 'dest_port']
    pagination_support = True
    sorting_support = True


class ServiceShow(extension.ClientExtensionShow, Service):
    """Show information of a given service."""
    shell_command = 'nuage-service-show'


class ServiceCreate(extension.ClientExtensionCreate, Service):
    """Create a service"""
    shell_command = 'nuage-service-create'

    @staticmethod
    def _validate_args(parsed_args):
        if not parsed_args.protocol:
            raise exceptions.CommandError(_("Protocol is a mandatory"
                                            " parameter for service creation"))
        if ((parsed_args.protocol == 'ICMP'
            or parsed_args.protocol == 'icmp'
            or parsed_args.protocol == '1')
            and (parsed_args.src_port or parsed_args.dest_port)):
            raise exceptions.CommandError(_("Source port and "
                                            "destination port"
                                            " are applicable only when "
                                            "protocol is TCP or UDP"))

        if ((parsed_args.protocol == 'TCP' or parsed_args.protocol == 'tcp'
                or parsed_args.protocol == '6') or
            (parsed_args.protocol == 'UDP' or parsed_args.protocol == 'udp'
                or parsed_args.protocol == '17')) \
                and (not (parsed_args.src_port or parsed_args.dest_port) or
                         (parsed_args.src_port == 'N/A' or
                                  parsed_args.dest_port == 'N/A')):
            raise exceptions.CommandError(_("Source port and "
                                            "destination port"
                                            " are mandatory parameters"
                                            " when protocol is TCP or UDP"
                                            " Usage: neutron "
                                            "nuage-service-create <svc-name>"
                                            " --src-port <src-port>"
                                            " --dest-port <dest-port>"))

    def add_known_arguments(self, parser):
        parser.add_argument(
            'name', metavar='name',
            help='Name of router for application deployment.'
        )
        parser.add_argument(
            '--protocol',
            help='Protocol to match.'),
        parser.add_argument(
            '--ethertype',
            help='Ethertype to match.'),
        parser.add_argument(
            '--dscp',
            help='DSCP value to match.'),
        parser.add_argument(
            '--direction',
            choices=['REFLEXIVE', 'UNIDIRECTIONAL'],
            help='Direction to be applied.'),
        parser.add_argument(
            '--description',
            help='Description of the Service being created.'),
        parser.add_argument(
            '--src-port',
            help='Source port to match. It can '
                 'be a number, range(x-y) or *.'),
        parser.add_argument(
            '--dest-port',
            help='Destination port to match. '
                 'It can be a number, range(x-y) or *.'),

    def args2body(self, parsed_args):
        self._validate_args(parsed_args)
        body = {'service': {'name': parsed_args.name}, }
        if parsed_args.protocol:
            body['service'].update(
                {'protocol': parsed_args.protocol})
        if parsed_args.ethertype:
            body['service'].update(
                {'ethertype': parsed_args.ethertype})
        if parsed_args.dscp:
            body['service'].update(
                {'dscp': parsed_args.dscp})
        if parsed_args.direction:
            body['service'].update(
                {'direction': parsed_args.direction})
        if parsed_args.src_port:
            body['service'].update(
                {'src_port': parsed_args.src_port})
        if parsed_args.dest_port:
            body['service'].update(
                {'dest_port': parsed_args.dest_port})
        if parsed_args.description:
            body['service'].update(
                {'description': parsed_args.description})
        return body


class ServiceDelete(extension.ClientExtensionDelete, Service):
    """Delete a service"""
    shell_command = 'nuage-service-delete'


def add_service_updatable_arguments(parser):
    parser.add_argument(
        '--name',
        help=_('Name of this application service.'))
    parser.add_argument(
        '--description',
        help=_('Description of this application service.'))


def service_updatable_args2body(parsed_args, body):
    if parsed_args.name:
        body['service'].update({'name': parsed_args.name})
    if parsed_args.description:
        body['service'].update({'description': parsed_args.description})


class ServiceUpdate(extension.ClientExtensionUpdate, Service):
    """Update information of a given service."""
    shell_command = 'nuage-service-update'

    def add_known_arguments(self, parser):
        add_service_updatable_arguments(parser)

    def args2body(self, parsed_args):
        body = {'service': {}}
        service_updatable_args2body(parsed_args, body)
        return body


class Flow(extension.NeutronClientExtension):

    resource = 'flow'
    resource_plural = '%ss' % resource
    object_path = '/%s' % 'flows'
    resource_path = '/%s/%%s' % 'flows'
    versions = ['2.0']


class FlowList(extension.ClientExtensionList, Flow):
    """List all flows"""
    shell_command = 'nuage-flow-list'
    list_columns = ['id', 'name', 'origin_tier',
                    'dest_tier', 'application_id']
    pagination_support = True
    sorting_support = True

    def get_parser(self, prog_name):
        parser = super(FlowList, self).get_parser(prog_name)
        parser.add_argument(
            'app_id', metavar='app-id',
            help=_('ID of the application where you want'
                   ' to look up for tiers.'))
        return parser

    def get_data(self, parsed_args):
        if not parsed_args.app_id:
            message = (_("Please provide the Aplication ID."
                         " Ex. neutron nuage-tier-list APP_ID"))
            raise exceptions.CommandError(message=message)
        self.values_specs.append('--app_id=%s' % parsed_args.app_id)
        return super(FlowList, self).get_data(parsed_args)


class FlowShow(extension.ClientExtensionShow, Flow):
    """Show information of a given flow."""
    shell_command = 'nuage-flow-show'
    allow_names = False


class FlowCreate(extension.ClientExtensionCreate, Flow):
    """Create a flow"""
    shell_command = 'nuage-flow-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            'name', metavar='name',
            help='Name of router for application deployment.'
        )
        parser.add_argument(
            '--origin-tier',
            help='Application Deployment App. ID.'),
        parser.add_argument(
            '--dest-tier',
            help='Application Deployment tier ID.'),
        parser.add_argument(
            '--src-addr-overwrite',
            help='The source address overwrite.'),
        parser.add_argument(
            '--dest-addr-overwrite',
            help='The destination address overwrite.'),
        parser.add_argument(
            '--nuage-services',
            help='Application Deployment tier ID.'),

    def args2body(self, parsed_args):
        if not parsed_args.origin_tier or \
                not parsed_args.dest_tier:
            raise exceptions.CommandError(_("Origin tier and"
                                            " Destination tier are"
                                            " mandatory for"
                                            " flow creation. Usage:"
                                            " neutron nuage-flow-create"
                                            " <flow-name>"
                                            " --origin-tier <tier-id>"
                                            " --dest-tier <tier-id>"))

        if (parsed_args.src_addr_overwrite or
                parsed_args.dest_addr_overwrite) \
                and not parsed_args.nuage_services:
            raise exceptions.CommandError(_("nuage-services is a mandatory"
                                            " parameter if you provide"
                                            " either src-addr-overwrite"
                                            " or dest-addr-overwrite as"
                                            " parameters"))
        body = {'flow': {'name': parsed_args.name}, }
        if parsed_args.origin_tier:
            body['flow'].update(
                {'origin_tier': parsed_args.origin_tier})
        if parsed_args.dest_tier:
            body['flow'].update(
                {'dest_tier': parsed_args.dest_tier})
        if parsed_args.src_addr_overwrite:
            body['flow'].update(
                {'src_addr_overwrite': parsed_args.src_addr_overwrite})
        if parsed_args.dest_addr_overwrite:
            body['flow'].update(
                {'dest_addr_overwrite': parsed_args.dest_addr_overwrite})
        if parsed_args.nuage_services:
            body['flow'].update(
                {'nuage_services': parsed_args.nuage_services})
        return body


class FlowDelete(extension.ClientExtensionDelete, Flow):
    """Delete a flow"""
    shell_command = 'nuage-flow-delete'
    allow_names = False


def add_flow_updatable_arguments(parser):
    parser.add_argument(
        '--name',
        help=_('Name of this application flow.'))
    parser.add_argument(
        '--description',
        help=_('Description of this application flow.'))


def flow_updatable_args2body(parsed_args, body):
    if parsed_args.name:
        body['flow'].update({'name': parsed_args.name})
    if parsed_args.description:
        body['flow'].update({'description': parsed_args.description})


class FlowUpdate(extension.ClientExtensionUpdate, Flow):
    """Update information of a given flow."""
    shell_command = 'nuage-flow-update'

    def add_known_arguments(self, parser):
        add_flow_updatable_arguments(parser)

    def args2body(self, parsed_args):
        body = {'flow': {}}
        flow_updatable_args2body(parsed_args, body)
        return body
