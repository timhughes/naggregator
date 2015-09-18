from twisted.application import service, internet
from twisted.cred import portal, checkers
from twisted.conch import manhole, manhole_ssh
from twisted.web import resource, server as webserver
from twisted.python import log, usage
from naggregator.services import ClientControlService, WebClientService
from naggregator.interface.web import AdminWebInterfaceService
from naggregator.interface.api import Api
# Setup Manhole debugging service
from conf.settings import nodes, static_files_dir
from corepost.web import RESTResource
from twisted.web.static import File

class Options(usage.Options):
    ''' Put the options that the twistd command line can take '''


def get_manhole_factory(namespace, **passwords):

    realm = manhole_ssh.TerminalRealm()

    def get_manhole(_):
        return manhole.ColoredManhole(namespace)
    realm.chainedProtocolFactory.protocolFactory = get_manhole
    p = portal.Portal(realm)
    p.registerChecker(
        checkers.InMemoryUsernamePasswordDatabaseDontUse(**passwords))
    f = manhole_ssh.ConchFactory(p)
    return f


def makeService(self):

    #application = service.Application("Nested Services Demo")
    multiservice = service.MultiService()
    admin_interface_resource = resource.Resource()
    admin_interface_resource.putChild('', AdminWebInterfaceService(multiservice))
    admin_interface_service = internet.TCPServer(8001, webserver.Site(admin_interface_resource))
    admin_interface_service.setName("Administration Interface")
    admin_interface_service.setServiceParent(multiservice)

    client_control_service = ClientControlService(multiservice)
    client_control_service.setName('Client Control')
    client_control_service.setServiceParent(multiservice)

    #web_interface_resource = resource.Resource()
    web_interface_resource = File(static_files_dir)
    api_resource = RESTResource((Api(client_control_service),))
    web_interface_resource.putChild('api', api_resource)
    web_interface_service = internet.TCPServer(8000, webserver.Site(web_interface_resource))
    web_interface_service.setName("Web Interface")
    web_interface_service.setServiceParent(multiservice)

    for node in nodes:
        client = WebClientService()
        log.msg(node['name'])
        client.setName(node['name'])
        client.nagios_uri = node['nagios_uri']
        client.cgi_uri = node['cgi_uri']
        if 'user' in node:
            client.user = node['user']
            client.password = node['password']
        client.setServiceParent(client_control_service)

    # Debugging manhole server
    namespace = {"Naggregator": client_control_service}
    manhole_service = internet.TCPServer(2223, get_manhole_factory(namespace, admin='aaa'))
    manhole_service.setServiceParent(multiservice)

    return multiservice
