__author__ = 'deathowl'

from twilio.rest import TwilioRestClient

class TwilioCallNotifier:

    def __init__(self, config):
        self.__config = config

    def notify(self, notification):
        client = TwilioRestClient(self.__config['SID'], self.__config['token'])
        try:
            client.calls.create(
                url=self.__config['twiml_url'],
                method="GET",
                to=notification.user_to_notify.profile.phone_number,
                from_=self.__config['phone_number'])
            print 'successfully sent the call'
        except :
            print 'failed to send the call'