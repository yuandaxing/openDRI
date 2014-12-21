from django.test import TestCase
import datetime
from opendri.models import Token, SchedulePolicy, Service

class TokenTestCase(TestCase):
    def setUp(self):
        super(TokenTest, self).setUp()
        self.tokens = Token.objects.get()
    def test_token(self):
        print self.tokens
        print datetime.datetime.now()
        self.assertEqual(1, 1)
