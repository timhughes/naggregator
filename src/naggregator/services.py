from twisted.application import service
from twisted.application.service import MultiService
from twisted.internet import reactor
from twisted.internet.defer import Deferred, inlineCallbacks
from twisted.internet.defer import succeed
from twisted.internet.protocol import Protocol
from twisted.internet.ssl import ClientContextFactory
from twisted.python import log
from twisted.web.client import Agent, HTTPConnectionPool
from twisted.web.iweb import IBodyProducer
from zope.interface import implements
from twisted.web.http_headers import Headers
from naggregator.utils import auth_header
# from naggregator.models import MonitoredHost, MonitoredService
from naggregator.models import Host, Service
from datetime import datetime
from bs4 import BeautifulSoup

class WebClientContextFactory(ClientContextFactory):
    def getContext(self, hostname, port):
        return ClientContextFactory.getContext(self)


class BodyProducer(object):
    ''' Not currently used '''
    implements(IBodyProducer)

    def __init__(self, body):
        self.body = body
        if self.body is None:
            self.length = 0
        else:
            self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass

    def resumeProducing(self):
        pass


class BodyConsumer(Protocol):

    def __init__(self, finished):
        self.finished = finished
        self.body = ''

    def dataReceived(self, data):
        self.body = self.body + data

    def connectionLost(self, reason):
        log.msg(reason.getErrorMessage())
        self.finished.callback(self.body)


class WebClientService(service.Service):

    def __init__(self):
        connection_pool = HTTPConnectionPool(reactor, persistent=True)
        context_factory = WebClientContextFactory()
        self.agent = Agent(reactor, context_factory, pool=connection_pool)
        # self.agent = Agent(reactor, context_factory)
        self.user = None
        self.password = None
        self.refresh_interval = 10
        self.nagios_uri = None
        self.cgi_uri = None
        self.useragent = {'User-Agent': ['Naggregator/1.1 twisted.web.client.Agent/12.2'], }

        self.hosts = {}
        self.services = {}
        self.comments = {}
        self.downtimes = {}

        self.hosts_lastupdate_utc = datetime.utcfromtimestamp(0)  # Never updated
        # self.hosts_message = False
        self.hosts_error = False
        self.services_lastupdate_utc = datetime.utcfromtimestamp(0)  # Never updated
        # self.services_message = False
        self.services_error = False

    def _cb_request(self, response):
        finished = Deferred()
        log.msg("Received %s - %s: %s. " % (response.length,
                                            response.code,
                                            response.phrase))
        response.deliverBody(BodyConsumer(finished))
        return finished

    def request(self, method, uri, headers=None, body=None):
        log.msg("Requesting %s %s" % (method, uri))
        req = self.agent.request(method, uri, headers)
        req.addCallback(self._cb_request)
        return req

    @inlineCallbacks
    def refresh_data(self):
        # : TODO: work out the meaning of the numbers in the nagios uri
        #  so as to make it configurable

        _hosts = {}

        hosts_uri = self.cgi_uri + "status.cgi?hostgroup=all&style=hostdetail&hoststatustypes=12&hostprops=42&limit=0&start=1"
        services_uri = self.cgi_uri + "status.cgi?host=all&type=detail&hoststatustypes=3&serviceprops=42&servicestatustypes=28&limit=0&start=1"

        if self.user:
            authheader = auth_header(self.user, self.password)
            headers = Headers(dict(self.useragent.items() + authheader.items()))
        else:
            headers = Headers(self.useragent)

        # get the hosts data
        html_hosts = yield self.request('GET', hosts_uri, headers)

        soup = BeautifulSoup(str(html_hosts.strip()))
        table = soup.find_all('table', 'status')
        del soup
        if not table:
            self.services_error = True
            log.err("Could not find status table in %s" % hosts_uri)
        else:
            try:
                self.hosts_error = False
                rows = table[0].find_all('tr', recursive=False)

                rows.pop(0)
                for row in rows:
                    columns = row('td', recursive=False)

                    name = str(columns[0].table.td.a.string.strip())

                    data = {
                        'active_checks_enabled': None,
                        'current_attempt': None,
                        'current_state': unicode(columns[1].string).strip(),
                        'last_check': unicode(columns[2].string).strip(),
                        'last_hard_state': None,
                        'last_notification': None,
                        'last_state_change': None,
                        'max_attempts': None,
                        'notifications_enabled': None,
                        'performance_data': None,
                        'plugin_output': ''.join(unicode(item) for item in columns[4].contents[0:]),
                        'problem_has_been_acknowledged': None,
                        'scheduled_downtime_depth': None,
                        'duration': unicode(columns[3].string).strip(),
                        'name': name,
                        'uri': self.cgi_uri + "extinfo.cgi?type=1&host=%s" % name.replace(' ', '+')
                    }

                    _hosts[name] = Host(data)
                self.hosts_lastupdate_utc = datetime.utcnow()
            except:
                self.hosts_error = True
                log.err()
        # Get the services data
        html_services = yield self.request('GET', services_uri, headers)
        soup = BeautifulSoup(html_services)
        table = soup.find("table", "status")
        if not table:
            self.services_error = True
            log.err("Could not find status table in %s" % services_uri)
        else:
            try:
                self.services_error = False
                rows = table.find_all("tr", recursive=False)

                # remove the headers row
                rows.pop(0)
                last_host = None
                for row in rows:

                    columns = row.find_all('td', recursive=False)
                    if len(columns) > 1:
                        # service = Service()
                        try:
                            host = str(columns[0].table.td.a.string.strip())
                        except:
                            host = last_host
                        last_host = host

                        name = str(columns[1].table.td.a.string.strip())
                        data = {
                            'active_checks_enabled': None,
                            'current_attempt': unicode(columns[5].string).strip(),
                            'current_state': unicode(columns[2].string).strip(),
                            'last_check': unicode(columns[3].string).strip(),
                            'last_hard_state': None,
                            'last_notification': None,
                            'last_state_change': None,
                            'max_attempts': None,
                            'notifications_enabled': None,
                            'performance_data': None,
                            'plugin_output': ''.join(unicode(item) for item in columns[6].contents[0:]),
                            'problem_has_been_acknowledged': None,
                            'scheduled_downtime_depth': None,
                            'duration': unicode(columns[4].string).strip(),
                            'name': name,
                            'uri': self.cgi_uri + "extinfo.cgi?type=2&host=%s&service=%s" % (host, name.replace(' ', '+'))
                        }


                        # service.name = str(columns[1].table.td.a.string.strip())
                        # service.status = str(columns[2].string.strip())
                        # service.last_check = str(columns[3].string.strip())
                        # service.duration = str(columns[4].string.strip())
                        # service.attempt = str(columns[5].string.strip())
                        # service.status_information = str(columns[6].string.strip())
                        # service.uri = self.cgi_uri + "/extinfo.cgi?type=2&host=%s&service=%s" % (host, service.name)

                        if host not in _hosts:
                            _hosts[host] = Host({'name':host})

                        _hosts[host].attach_service(Service(data))

                        self.hosts = _hosts
                self.services_lastupdate_utc = datetime.utcnow()
            except:
                self.services_error = True
                log.err()

        # self.data = hosts
        # Set the timer to refresh the data
        reactor.callLater(self.refresh_interval, self.refresh_data)

    def host_or_service(self, host, service=None):
        '''Return a Host or Service object for the given host/service combo.
        Note that Service may be None, in which case we return a Host.
        '''
        if host not in self.hosts:
            return None
        if service is None:  # Only a Host if they really want it.
            return self.hosts[host]
        if host not in self.services or service not in self.services[host]:
            return None
        return self.services[host][service]

    def for_json(self):
        '''Given a Nagios state object, return a pruned down dict that is
        ready to be serialized to JSON.
        '''
        out = {}
        for host in self.hosts:
            out[host] = self.hosts[host].for_json()
        return out

    def startService(self):
        service.Service.startService(self)
        reactor.callWhenRunning(self.refresh_data)


class ClientControlService(MultiService):

    def __init__(self, application):

        # The following doesnt work because twisted uses old style classes
        # super(ClientControlService, self).__init__()
        MultiService.__init__(self)
        self.application = application
        self.data = []



