nodes = [
        {'name':'Nagios Core Demo',
         'uri': "http://nagioscore.demos.nagios.com/",
         'user':'readonly',
         'password':'readonly',
        },

]

static_files_dir = "/opt/naggregator/src/static_files"

from .local_settings import *