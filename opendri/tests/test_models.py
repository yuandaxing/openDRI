from django.test import TestCase
import datetime
from opendri.models import Token, SchedulePolicy, Service

class TokenTestCase(TestCase):
    fixtures = ['alldata.json']
    def setUp(self):
        super(TokenTestCase, self).setUp()
        self.tokens = Token.objects.all()
    def test_token(self):
        print self.tokens
        print datetime.datetime.now()
        self.assertEqual(1, 1)
