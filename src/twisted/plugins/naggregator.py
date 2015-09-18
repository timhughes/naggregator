from twisted.application.service import ServiceMaker

naggregator= ServiceMaker(
    'naggregator', 'naggregator.tap', 'Run the Naggregator service', 'naggregator')
