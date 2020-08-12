from twisted.application import service
from corepost.enums import Http
from corepost.web import route
from naggregator.utils import slugify
from corepost import Response
import simplejson as json


class Api(object):

    def __init__(self, client_control_service):
        self.cc_svc = client_control_service

    @route("/", Http.GET)
    def get_node_list(self, request, **kwargs):
        nodes_list = []
        for node_svc in service.IServiceCollection(self.cc_svc):
            node_dict = {
                'name': node_svc.name,
                'uri': node_svc.nagios_uri,
                'hosts': node_svc.for_json(),
            }

            node_dict['path'] = "/%s/" % slugify(node_svc.name)
            node_dict['hosts_lastupdate_utc'] = node_svc.hosts_lastupdate_utc.strftime("%d-%m-%Y %H:%M:%S")
            node_dict['hosts_error'] = node_svc.hosts_error
            node_dict['services_lastupdate_utc'] = node_svc.services_lastupdate_utc.strftime("%d-%m-%Y %H:%M:%S")
            node_dict['services_error'] = node_svc.services_error

            nodes_list.append(node_dict)
        data = json.dumps(nodes_list)
        return Response(200, data, {'Content-Type': 'application/json'})
