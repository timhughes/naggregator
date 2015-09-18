
from twisted.application import service
from twisted.web import resource
import simplejson as json
#from naggregator.models import MontoredObjectJSONEncoder


class AdminWebInterfaceService(resource.Resource):

    isLeaf = True

    def __init__(self, application):
        self.application = application

#    def render_GET(self, request):
#        service_list = []
#        client_control_service = service.IServiceCollection(self.application)
#
#        request.write('<html><body>')
#        cc_srv = client_control_service.getServiceNamed('Client Control')
#        for srv in service.IServiceCollection(cc_srv):
#            service_list.append(srv.name)
#            request.write("<h2><a href=\"%s\">%s</a></h2>" % (srv.nagios_uri, srv.name))
#            #request.write("<p><pre>%s</pre></p>" % (str(srv.data)))
#            request.write("<pre>" + json.dumps(srv.data, cls=MontoredObjectJSONEncoder,
#                               sort_keys=True,
#                               indent=2) + "</pre>")
#        request.write('</body></html>')
#        return ''
