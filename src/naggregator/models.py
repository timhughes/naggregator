class NagiosObject:
    '''A base class that does a little fancy parsing. That's it.
    '''
    def __init__(self, obj):
        '''Builder for the base.'''
        for key in obj:
            self.__dict__[key] = obj[key]
        self.host = getattr(self, 'host_name', None)
        self.service = getattr(self, 'service_description', None)
        self.essential_keys = []

    def for_json(self):
        '''Return a dict of ourselves that is ready to be serialized out
        to JSON. This only returns the data that we think is essential for
        any UI to show.
        '''
        obj = {}
        for key in self.essential_keys:
            obj[key] = getattr(self, key, None)
        return obj


class HostOrService(NagiosObject):
    '''Represent a single host or service.
    '''
    def __init__(self, obj):
        '''Custom build a HostOrService object.'''
        NagiosObject.__init__(self, obj)
        self.downtimes = {}
        self.comments = {}
        self.essential_keys = ['current_state', 'plugin_output',
            'notifications_enabled', 'last_check', 'last_notification',
            'active_checks_enabled', 'problem_has_been_acknowledged',
            'last_hard_state', 'scheduled_downtime_depth', 'performance_data',
            'last_state_change', 'current_attempt', 'max_attempts', 'uri',
            'name']

    def attach_downtime(self, dt):
        '''Given a Downtime object, store a record to it for lookup later.'''
        self.downtimes[dt.downtime_id] = dt

    def attach_comment(self, cmt):
        '''Given a Comment object, store a record to it for lookup later.'''
        self.comments[cmt.comment_id] = cmt


class Host(HostOrService):
    '''Represent a single host.
    '''
    def __init__(self, obj):
        '''Custom build a Host object.'''
        HostOrService.__init__(self, obj)
        self.services = {}

    def attach_service(self, svc):
        '''Attach a Service to this Host.'''
        self.services[svc.name] = svc

    def for_json(self):
        '''Represent ourselves and also get attached data.'''
        obj = NagiosObject.for_json(self)
        for key in ('services', 'comments', 'downtimes'):
            obj[key] = {}
            for idx in self.__dict__[key]:
                obj[key][idx] = self.__dict__[key][idx].for_json()
        return obj


class Service(HostOrService):
    '''Represent a single service.
    '''
    def for_json(self):
        '''Represent ourselves and also get attached data.'''
        obj = NagiosObject.for_json(self)
        for key in ('comments', 'downtimes'):
            obj[key] = {}
            for idx in self.__dict__[key]:
                obj[key][idx] = self.__dict__[key][idx].for_json()
        return obj


class Comment(NagiosObject):
    '''Represent a single comment.
    '''
    def __init__(self, obj):
        '''Custom build a Comment object.'''
        NagiosObject.__init__(self, obj)
        self.essential_keys = ['comment_id', 'entry_type', 'source',
            'persistent', 'entry_time', 'expires', 'expire_time', 'author',
            'comment_data']
        self.comment_id = int(self.comment_id)


class Downtime(NagiosObject):
    '''Represent a single downtime event.
    '''
    def __init__(self, obj):
        '''Custom build a Downtime object.'''
        NagiosObject.__init__(self, obj)
        self.essential_keys = ['downtime_id', 'entry_time', 'start_time',
            'end_time', 'triggered_by', 'fixed', 'duration', 'author',
            'comment']
        self.downtime_id = int(self.downtime_id)
