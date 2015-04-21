# Copyright 2014 Alcatel-Lucent USA Inc.
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

from __future__ import print_function

import re

from cliff import lister
from cliff import show
from oslo.serialization import jsonutils
import six

from neutronclient.common import exceptions
from neutronclient.common import extension
from neutronclient.i18n import _
from neutronclient.common import utils
from neutronclient.neutron import v2_0 as neutronV20


GW_RESOURCE = 'nuage_gateway'
GW_PORT_RESOURCE = 'nuage_gateway_port'
GW_PORT_VLAN_RESOURCE = 'nuage_gateway_vlan'
GW_VPORT_RESOURCE = 'nuage_gateway_vport'
HEX_ELEM = '[0-9A-Fa-f]'
UUID_PATTERN = '-'.join([HEX_ELEM + '{8}', HEX_ELEM + '{4}',
                         HEX_ELEM + '{4}', HEX_ELEM + '{4}',
                         HEX_ELEM + '{12}'])


def check_vlan_value(value):
    try:
        vlan_val = int(value)
        return vlan_val
    except ValueError:
        message = (_('Vlan value should be a valid integer '
                     'in 0-4095 range'))
        raise exceptions.CommandError(message=message)
    else:
        if vlan_val < 0 or vlan_val > 4095:
            message = (_('Vlan value should be in 0-4095 range'))
            raise exceptions.CommandError(message=message)


def get_gatway_info(parsed_args, neutron_client):
    res_id = parsed_args.id
    if res_id:
        if parsed_args.gatewayport and parsed_args.gateway:
            # id is vlan value
            check_vlan_value(res_id)

            gw_id = neutronV20.find_resourceid_by_name_or_id(
                neutron_client, GW_RESOURCE, parsed_args.gateway)
            gw_port_id = neutronV20.find_resourceid_by_name_or_id(
                neutron_client, GW_PORT_RESOURCE, parsed_args.gatewayport,
                parent_id=gw_id)
            res_id = neutronV20.find_resourceid_by_name_or_id(
                neutron_client, GW_PORT_VLAN_RESOURCE, res_id,
                parent_id=gw_port_id)
        elif parsed_args.gatewayport:
            # id is vlan value
            check_vlan_value(res_id)

            match = re.match(UUID_PATTERN, parsed_args.gatewayport)
            if not match:
                message = (_('--gatewayport should be a UUID'))
                raise exceptions.CommandError(message=message)

            gw_port_id = neutronV20.find_resourceid_by_name_or_id(
                neutron_client, GW_PORT_RESOURCE, parsed_args.gatewayport)
            res_id = neutronV20.find_resourceid_by_name_or_id(
                neutron_client, GW_PORT_VLAN_RESOURCE, res_id,
                parent_id=gw_port_id)
        else:
            # id is gw interface value
            res_id = neutronV20.find_resourceid_by_name_or_id(
                neutron_client, GW_PORT_VLAN_RESOURCE, res_id)

            obj_shower = getattr(neutron_client, "show_%s" %
                                 GW_PORT_VLAN_RESOURCE)
            params = {}
            data = obj_shower(res_id, **params)
            res_id = data[GW_PORT_VLAN_RESOURCE]['value']

    return res_id


class Gateway(extension.NeutronClientExtension):
    resource = GW_RESOURCE
    resource_plural = '%ss' % resource
    object_path = '/%ss' % resource.replace('_', '-')
    resource_path = '/%ss/%%s' % resource.replace('_', '-')
    versions = ['2.0']


class ListGateway(extension.ClientExtensionList, Gateway):
    shell_command = 'nuage-gateway-list'
    list_columns = ['id', 'name', 'type', 'status', 'template', 'systemid']


class ShowGateway(extension.ClientExtensionShow, Gateway):
    shell_command = 'nuage-gateway-show'


class GatewayPort(extension.NeutronClientExtension):
    parent_resource = 'gateway'
    resource = GW_PORT_RESOURCE
    resource_plural = '%ss' % resource
    object_path = '/%ss' % resource.replace('_', '-')
    resource_path = '/%ss/%%s' % resource.replace('_', '-')
    versions = ['2.0']


class ListGatewayPort(extension.ClientExtensionList, GatewayPort):
    """List all gateway ports."""
    shell_command = 'nuage-gateway-port-list'
    list_columns = ['id', 'name', 'status', 'vlan', 'usermnemonic',
                    'physicalname']

    def get_parser(self, prog_name):
        parser = super(ListGatewayPort, self).get_parser(prog_name)
        parser.add_argument(
            '--gateway', metavar='gateway',
            help=_('ID or name of gateway to look up.'))
        return parser

    def get_data(self, parsed_args):
        neutron_client = self.get_client()
        neutron_client.format = parsed_args.request_format
        if not parsed_args.gateway:
            message = (_('--gateway option should be specified'))
            raise exceptions.CommandError(message=message)

        gw_id = neutronV20.find_resourceid_by_name_or_id(
            neutron_client, 'nuage_gateway', parsed_args.gateway)
        self.values_specs.append('--gateway=%s' % gw_id)
        return super(ListGatewayPort, self).get_data(parsed_args)


class ShowGatewayPort(extension.ClientExtensionShow, GatewayPort):
    """Show information of a given gateway."""
    shell_command = 'nuage-gateway-port-show'

    def get_parser(self, prog_name):
        parser = super(ShowGatewayPort, self).get_parser(prog_name)
        # parser.add_argument(
        #     'id', nargs='?', metavar='GATEWAYPORT',
        #     help=_('ID of the gateway port or Name/ID of the gateway port '
        #            'when used with --gateway option'))
        parser.add_argument(
            '--gateway', metavar='GATEWAY',
            help=_('Name or ID of the gateway'))
        return parser

    def get_data(self, parsed_args):
        neutron_client = self.get_client()
        neutron_client.format = parsed_args.request_format
        params = {}
        if parsed_args.id:
            if parsed_args.gateway:
                gw_id = neutronV20.find_resourceid_by_name_or_id(
                    neutron_client, GW_RESOURCE, parsed_args.gateway)

                _id = neutronV20.find_resourceid_by_name_or_id(
                    neutron_client, GW_PORT_RESOURCE, parsed_args.id,
                    parent_id=gw_id)
            else:
                _id = neutronV20.find_resourceid_by_name_or_id(
                    neutron_client, GW_PORT_RESOURCE, parsed_args.id)
        else:
            message = (_('gatewayport or gatewayport and --gateway option '
                         'should be specified'))
            raise exceptions.CommandError(message=message)
        obj_shower = getattr(neutron_client, "show_%s" % self.cmd_resource)
        data = obj_shower(_id, **params)
        self.format_output_data(data)
        if _id:
            resource = self.resource
            resp_dict = data[resource]
        else:
            resource = self.resource + 's'
            resp_dict = data[resource][0]

        if resource in data:
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


class GatewayPortVlan(extension.NeutronClientExtension):
    parent_resource = 'gatewayport'
    resource = GW_PORT_VLAN_RESOURCE
    resource_plural = '%ss' % resource
    object_path = '/%ss' % resource.replace('_', '-')
    resource_path = '/%ss/%%s' % resource.replace('_', '-')
    versions = ['2.0']


class ListGatewayPortVlan(extension.ClientExtensionList, GatewayPortVlan,
                          lister.Lister):
    """List all gateway port vlans."""
    list_columns = ['id', 'value', 'vport']
    shell_command = 'nuage-gateway-vlan-list'

    def get_parser(self, prog_name):
        parser = super(ListGatewayPortVlan, self).get_parser(prog_name)
        parser.add_argument(
            '--gateway', metavar='gateway',
            help=_('ID or name of gateway to look up.'))
        parser.add_argument(
            '--tenant-id', metavar='TENANT_ID',
            help=_('The owner tenant ID.'), )
        parser.add_argument(
            '--gatewayport', metavar='GATEWAYPORT',
            help=_('ID or name of gatewayport to look up.'))
        return parser

    def get_data(self, parsed_args):
        neutron_client = self.get_client()
        neutron_client.format = parsed_args.request_format
        params = dict()
        gw_id = None

        if parsed_args.tenant_id:
            if not parsed_args.gatewayport or not parsed_args.gateway:
                message = (_('--gatewayport or/and --gateway '
                             'option should be specified'))
                raise exceptions.CommandError(message=message)
            params['tenant'] = parsed_args.tenant_id
        else:
            params['tenant'] = ''

        if parsed_args.gateway:
            gw_id = neutronV20.find_resourceid_by_name_or_id(
                neutron_client, GW_RESOURCE, parsed_args.gateway)
            params['gateway'] = gw_id

        if parsed_args.gatewayport:
            gw_port_id = neutronV20.find_resourceid_by_name_or_id(
                neutron_client, GW_PORT_RESOURCE, parsed_args.gatewayport,
                parent_id=gw_id)
            params['gatewayport'] = gw_port_id

        obj_lister = getattr(neutron_client,
                             "list_%ss" % self.resource)
        data = obj_lister(**params)
        info = []
        collection = self.resource + "s"
        if collection in data:
            info = data[collection]
        _columns = len(info) > 0 and sorted(info[0].keys()) or []
        if 'tenant_id' in _columns:
            _columns.remove('tenant_id')
        return (_columns, (utils.get_item_properties(s, _columns)
                for s in info))


class ShowGatewayPortVlan(extension.ClientExtensionShow,
                          GatewayPortVlan, show.ShowOne):
    """Show information of a given gateway port."""
    shell_command = 'nuage-gateway-vlan-show'

    def get_parser(self, prog_name):
        parser = super(ShowGatewayPortVlan, self).get_parser(prog_name)
        # parser.add_argument(
        #     'id',
        #     help=_('ID of the gateway interface or vlan value(0-4094) when '
        #            'used with --gatewayport or --gateway and --gatewayport '))
        parser.add_argument(
            '--gateway', metavar='GATEWAY',
            help=_('Name or ID of the gateway'))
        parser.add_argument(
            '--gatewayport', metavar='GATEWAYPORT',
            help=_('Name or ID of the gatewayport'))
        return parser

    def get_data(self, parsed_args):
        neutron_client = self.get_client()
        neutron_client.format = parsed_args.request_format
        params = {}
        _id = parsed_args.id
        if _id:
            if parsed_args.gatewayport and parsed_args.gateway:
                # id is vlan value
                check_vlan_value(_id)

                gw_id = neutronV20.find_resourceid_by_name_or_id(
                    neutron_client, GW_RESOURCE, parsed_args.gateway)
                gw_port_id = neutronV20.find_resourceid_by_name_or_id(
                    neutron_client, GW_PORT_RESOURCE, parsed_args.gatewayport,
                    parent_id=gw_id)
                _id = neutronV20.find_resourceid_by_name_or_id(
                    neutron_client, GW_PORT_VLAN_RESOURCE, _id,
                    parent_id=gw_port_id)
                params['gateway'] = gw_id
                params['gatewayport'] = gw_port_id
            elif parsed_args.gatewayport:
                # id is vlan value
                check_vlan_value(_id)

                match = re.match(UUID_PATTERN, parsed_args.gatewayport)
                if not match:
                    message = (_('--gatewayport should be a UUID'))
                    raise exceptions.CommandError(message=message)

                gw_port_id = neutronV20.find_resourceid_by_name_or_id(
                    neutron_client, GW_PORT_RESOURCE, parsed_args.gatewayport)
                _id = neutronV20.find_resourceid_by_name_or_id(
                    neutron_client, GW_PORT_VLAN_RESOURCE, _id,
                    parent_id=gw_port_id)
                params['gatewayport'] = gw_port_id
            else:
                # id is gw interface value
                _id = neutronV20.find_resourceid_by_name_or_id(
                    neutron_client, GW_PORT_VLAN_RESOURCE, _id)
        obj_shower = getattr(neutron_client, "show_%s" % self.cmd_resource)
        data = obj_shower(_id, **params)
        self.format_output_data(data)
        if _id:
            resource = self.resource
            resp_dict = data[resource]
        else:
            resource = self.resource + 's'
            resp_dict = data[resource][0]

        resp_dict.pop('tenant_id', None)

        if resource in data:
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


class CreateGatewayPortVlan(extension.ClientExtensionCreate,
                            GatewayPortVlan):
    """Create a vlan on gateway port."""
    shell_command = 'nuage-gateway-vlan-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            'id', metavar='VLAN_VALUE', type=check_vlan_value,
            help=_('Vlan value in 0-4095 range'))
        parser.add_argument(
            '--gateway', metavar='GATEWAY',
            help=_('Name or ID of the gateway'))
        parser.add_argument(
            '--gatewayport', metavar='GATEWAYPORT',
            help=_('Name or ID of the gatewayport'))

    def args2body(self, parsed_args):
        body = {self.resource: {
            'value': parsed_args.id}}

        if parsed_args.gateway and parsed_args.gatewayport:
            body[self.resource].update({'gateway': parsed_args.gateway})
            gw_id = neutronV20.find_resourceid_by_name_or_id(
                self.get_client(), GW_RESOURCE, parsed_args.gateway)
            body[self.resource].update(
                {'gateway': gw_id})

            gw_port_id = neutronV20.find_resourceid_by_name_or_id(
                self.get_client(), GW_PORT_RESOURCE, parsed_args.gatewayport,
                parent_id=gw_id)

            body[self.resource].update(
                {'gatewayport': gw_port_id})

        elif parsed_args.gatewayport:
            match = re.match(UUID_PATTERN, parsed_args.gatewayport)
            if not match:
                message = (_('--gatewayport should be a UUID'))
                raise exceptions.CommandError(message=message)

            gw_port_id = neutronV20.find_resourceid_by_name_or_id(
                self.get_client(), GW_PORT_RESOURCE, parsed_args.gatewayport)

            body[self.resource].update(
                {'gatewayport': gw_port_id})
        else:
            message = (_('--gatewayport should be specified'))
            raise exceptions.CommandError(message=message)

        return body

    def cleanup_output_data(self, data):
        info = data[self.resource]
        info.pop('tenant_id', None)


class DeleteGatewayPortVlan(extension.ClientExtensionDelete,
                            GatewayPortVlan):
    """Delete a given nuage gateway port vlan."""

    shell_command = 'nuage-gateway-vlan-delete'

    def get_parser(self, prog_name):
        parser = super(DeleteGatewayPortVlan, self).get_parser(prog_name)
        # parser.add_argument(
        #     'id',
        #     help=_('ID of the gateway interface or vlan value(0-4094) when '
        #            'used with --gatewayport or --gateway and --gatewayport '))
        parser.add_argument(
            '--gateway', metavar='GATEWAY',
            help=_('Name or ID of the gateway'))
        parser.add_argument(
            '--gatewayport', metavar='GATEWAYPORT',
            help=_('Name or ID of the gatewayport'))
        return parser

    def run(self, parsed_args):
        self.log.debug('run(%s)' % parsed_args)
        neutron_client = self.get_client()
        neutron_client.format = parsed_args.request_format
        res_id = get_gatway_info(parsed_args, neutron_client)
        obj_deleter = getattr(neutron_client, "delete_%s" % self.resource)
        match = re.match(UUID_PATTERN, str(res_id))
        if match:
            obj_deleter(res_id)
            print((_('Deleted %(resource)s with value %(res_id)s')
                   % {'res_id': parsed_args.id,
                      'resource': self.resource}),
                  file=self.app.stdout)
        else:
            obj_deleter(parsed_args.id)
            print((_('Deleted %(resource)s with value %(res_id)s')
                   % {'res_id': res_id,
                      'resource': self.resource}),
                  file=self.app.stdout)


class AssignGatewayPortVlan(extension.ClientExtensionUpdate,
                            GatewayPortVlan):
    """Assign a given nuage gateway port vlan."""

    shell_command = 'nuage-gateway-vlan-assign'

    def get_parser(self, prog_name):
        parser = super(AssignGatewayPortVlan, self).get_parser(prog_name)
        # parser.add_argument(
        #     'id',
        #     help=_('ID of the gateway interface or vlan value(0-4094) when '
        #            'used with --gatewayport or --gateway and --gatewayport '))
        parser.add_argument(
            'tenant_id', metavar='TENANT_ID',
            help=_('The owner tenant ID.'), )
        parser.add_argument(
            '--gateway', metavar='GATEWAY',
            help=_('Name or ID of the gateway'))
        parser.add_argument(
            '--gatewayport', metavar='GATEWAYPORT',
            help=_('Name or ID of the gatewayport'))
        return parser

    def run(self, parsed_args):
        self.log.debug('run(%s)' % parsed_args)
        neutron_client = self.get_client()
        neutron_client.format = parsed_args.request_format
        res_id = get_gatway_info(parsed_args, neutron_client)
        body = {self.resource: {
            'tenant': parsed_args.tenant_id,
            'action': 'assign'}}

        import pdb;pdb.set_trace()
        match = re.match(UUID_PATTERN, str(res_id))
        if match:
            neutron_client.update_nuage_gateway_vlan(res_id, body)
            print((_('Assigned %(resource)s %(res_id)s to tenant %(tenant)s')
                   % {'res_id': parsed_args.id,
                      'resource': self.resource,
                      'tenant': parsed_args.tenant_id}),
                  file=self.app.stdout)
        else:
            neutron_client.update_nuage_gateway_vlan(parsed_args.id, body)
            print((_('Assigned %(resource)s %(res_id)s to tenant %(tenant)s')
                   % {'res_id': res_id,
                      'resource': self.resource,
                      'tenant': parsed_args.tenant_id}),
                  file=self.app.stdout)


class UnassignGatewayPortVlan(extension.ClientExtensionUpdate,
                              GatewayPortVlan):
    """Unassign a given nuage gateway port vlan."""

    shell_command = 'nuage-gateway-vlan-unassign'

    def get_parser(self, prog_name):
        parser = super(UnassignGatewayPortVlan, self).get_parser(prog_name)
        # parser.add_argument(
        #     'id',
        #     help=_('ID of the gateway interface or vlan value(0-4094) when '
        #            'used with --gatewayport or --gateway and --gatewayport '))
        parser.add_argument(
            'tenant_id', metavar='TENANT_ID',
            help=_('The owner tenant ID.'), )
        parser.add_argument(
            '--gateway', metavar='GATEWAY',
            help=_('Name or ID of the gateway'))
        parser.add_argument(
            '--gatewayport', metavar='GATEWAYPORT',
            help=_('Name or ID of the gatewayport'))
        return parser

    def run(self, parsed_args):
        self.log.debug('run(%s)' % parsed_args)
        neutron_client = self.get_client()
        neutron_client.format = parsed_args.request_format
        res_id = get_gatway_info(parsed_args, neutron_client)
        body = {self.resource: {
            'tenant': parsed_args.tenant_id,
            'action': 'unassign'}}
        match = re.match(UUID_PATTERN, str(res_id))
        if match:
            neutron_client.update_nuage_gateway_vlan(res_id, body)
            print((_('Unassigned %(resource)s %(res_id)s from tenant '
                     '%(tenant)s')
                   % {'res_id': parsed_args.id,
                      'resource': self.resource,
                      'tenant': parsed_args.tenant_id}),
                  file=self.app.stdout)
        else:
            neutron_client.update_nuage_gateway_vlan(parsed_args.id,
                                                       body)
            print((_('Unassigned %(resource)s %(res_id)s from tenant '
                     '%(tenant)s')
                   % {'res_id': res_id,
                      'resource': self.resource,
                      'tenant': parsed_args.tenant_id}),
                  file=self.app.stdout)


class GatewayVPort(extension.NeutronClientExtension):
    parent_resource = 'subnet'
    resource = GW_VPORT_RESOURCE
    resource_plural = '%ss' % resource
    object_path = '/%ss' % resource.replace('_', '-')
    resource_path = '/%ss/%%s' % resource.replace('_', '-')
    versions = ['2.0']


class CreateGatewayVPort(extension.ClientExtensionCreate, GatewayVPort):
    """Create a nuage gateway vport."""

    shell_command = 'nuage-gateway-vport-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            'gatewayvlan', metavar='GATEWAYVLAN',
            help=_('ID of the gateway interface'))
        parser.add_argument(
            '--subnet', metavar='SUBNET',
            help=_('ID of the subnet'))
        parser.add_argument(
            '--port', metavar='SUBNET',
            help=_('ID of the port'))

    def args2body(self, parsed_args):
        body = {self.resource: {
            'gatewayvlan': parsed_args.gatewayvlan}}

        if (parsed_args.subnet and parsed_args.port) or not (
                parsed_args.subnet or parsed_args.port):
            message = (_('Specify subnet or port'))
            raise exceptions.CommandError(message=message)

        if parsed_args.subnet:
            subn_id = neutronV20.find_resourceid_by_name_or_id(
                self.get_client(), 'subnet', parsed_args.subnet)
            body[self.resource].update({'subnet': subn_id})

        if parsed_args.port:
            body[self.resource].update({'port': parsed_args.port})

        if parsed_args.tenant_id:
            body[self.resource].update({'tenant': parsed_args.tenant_id})
        else:
            body[self.resource].update({'tenant': ''})

        return body

    def cleanup_output_data(self, data):
        info = data[self.resource]
        info.pop('tenant_id', None)


class DeleteGatewayVPort(extension.ClientExtensionDelete, GatewayVPort):
    """Delete a nuage gateway vport."""

    shell_command = 'nuage-gateway-vport-delete'

    def get_parser(self, prog_name):
        parser = super(DeleteGatewayVPort, self).get_parser(prog_name)
        # parser.add_argument(
        #     'id', metavar='GATEWAYVPORT',
        #     help=_('ID of the gateway vport'))
        parser.add_argument(
            'subnet', metavar='SUBNET',
            help=_('ID of the subnet'))
        return parser

    def run(self, parsed_args):
        self.log.debug('run(%s)' % parsed_args)
        neutron_client = self.get_client()
        neutron_client.format = parsed_args.request_format
        subn_id = neutronV20.find_resourceid_by_name_or_id(
            neutron_client, 'subnet', parsed_args.subnet)

        vport_id = neutronV20.find_resourceid_by_name_or_id(
            neutron_client, GW_VPORT_RESOURCE, parsed_args.id,
            parent_id=subn_id)

        neutron_client.delete_nuage_gateway_vport(vport_id)
        print((_('Vport %s deleted successfully') %
               parsed_args.id),
              file=self.app.stdout)


class ShowGatewayVPort(extension.ClientExtensionShow, GatewayVPort):
    """Show information of a given nuage gateway vport."""

    shell_command = 'nuage-gateway-vport-show'

    def get_parser(self, prog_name):
        parser = super(ShowGatewayVPort, self).get_parser(prog_name)
        # parser.add_argument(
        #     'id', metavar='GATEWAYVPORT',
        #     help=_('ID of the gateway vport'))
        parser.add_argument(
            'subnet', metavar='SUBNET',
            help=_('ID of the subnet'))
        return parser

    def get_data(self, parsed_args):
        neutron_client = self.get_client()
        neutron_client.format = parsed_args.request_format
        params = {}
        subn_id = neutronV20.find_resourceid_by_name_or_id(
            neutron_client, 'subnet', parsed_args.subnet)
        params['subnet'] = subn_id

        vport_id = neutronV20.find_resourceid_by_name_or_id(
            neutron_client, GW_VPORT_RESOURCE, parsed_args.id,
            parent_id=subn_id)

        obj_shower = getattr(neutron_client, "show_%s" % self.cmd_resource)
        data = obj_shower(vport_id, **params)
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


class ListGatewayVPort(extension.ClientExtensionList, GatewayVPort):
    """List all gateway vports."""

    shell_command = 'nuage-gateway-vport-list'
    list_columns = ['id', 'type', 'interface', 'subnet', 'port', 'vlan',
                    'gateway', 'gatewayport']

    def extend_list(self, data, parsed_args):
        for d in data:
            if d.get('value'):
                d['vlan'] = d.get('value')

    def get_parser(self, prog_name):
        parser = super(ListGatewayVPort, self).get_parser(prog_name)
        parser.add_argument(
            'id', metavar='SUBNET',
            help=_('ID of the subnet'))
        parser.add_argument(
            '--tenant-id', metavar='TENANT',
            help=_('ID of the tenant.'))
        return parser

    def get_data(self, parsed_args):
        neutron_client = self.get_client()
        neutron_client.format = parsed_args.request_format
        # if not parsed_args.subnet:
        #     message = (_('Specify --subnet option'))
        #     raise exceptions.CommandError(message=message)
        subn_id = neutronV20.find_resourceid_by_name_or_id(
            neutron_client, 'subnet', parsed_args.id)
        self.values_specs.append('--subnet=%s' % subn_id)
        if parsed_args.tenant_id:
            self.values_specs.append('--tenant=%s' % parsed_args.tenant_id)
        return super(ListGatewayVPort, self).get_data(parsed_args)
