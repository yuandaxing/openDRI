__author__ = 'ydx'

import uuid 
import hmac 
from hashlib import sha1

from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import models as auth_models
from django.contrib.auth.management import create_superuser
from django.conf import settings
from django.db.models import signals
from uuidfield import UUIDField
from schedule.models import Calendar
from django.utils.encoding import python_2_unicode_compatible

@python_2_unicode_compatible
class Token(models.Model) :
    '''
    the default authorization token model.
    '''
    key = models.CharField(max_length=40, primary_key = True)
    created = models.DateTimeField(auto_now_add=True) 
    
    def save(self, *args, **kwargs) :
        if not self.key :
            self.key = self.generate_key()
        return super(Token, self).save(*args, **kwargs)

    def generate_key(self) :
        unique = uuid.uuid4()
        return hmac.new(unique.bytes, digestmod=sha1).hexdigest()

    def __unicode__(self) :
        return self.key 
    
    def __str__(self) :
        return self.key 
@python_2_unicode_compatible
class SchedulePolicy(models.Model) :
    '''
    schedule policy
    '''
    name = models.CharField(max_length=80, unique=True)
    repeat_times = models.IntegerField()

    class Meta:
        verbose_name = 'schedule_policy'
        verbose_name_plural = 'schedule_policies'

    def __str__(self) :
        return self.name

    def natural_key(self):
        return self.name 
@python_2_unicode_compatible
class Service(models.Model) :
    '''
    incidents are representations of a malfunction in the system.
    '''
    name = models.CharField(max_length=80, unique=True)
    id = UUIDField(primary_key=True, auto=True)
    retry = models.IntegerField(blank=True, null=True)
    policy = models.ForeignKey(SchedulePolicy, blank=True, null=True)
    escalate_after = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name = 'service'
        verbose_name_plural = 'service'

    def __str__(self) :
        return self.name

    def __natural_key(self) :
        return self.id

@python_2_unicode_compatible
class EventLog(models.Model) :
    '''
    Event Log
    '''
    service_key = models.ForeignKey(Service)
    data = models.TextField()
    occurred_at = models.DateTimeField()

    class Meta :
        verbose_name = 'eventlog'
        verbose_name_plural = 'eventlog'

    def __str__(self) :
        return self.data 

    def natural_key(self) :
        return (self.service_key, self.id)
@python_2_unicode_compatible
class Incident(models.Model) :
    TRIGGER = 'trigger'
    RESOLVE = 'resolve'
    ACKNOWLEDGE = 'acknowledge'

    '''
    Incident are representations of a malfunction in the system
    '''
    service_key = models.ForeignKey(Service)
    incident_key = models.CharField(max_length=80)
    event_type = models.CharField(max_length=15)
    description = models.CharField(max_length=100)
    details = models.TextField()
    occurred_at = models.DateTimeField()

    class Meta :
        verbose_name = 'incidents'
        verbose_name_plural = 'incidents'
        unique_together = ('service_key', 'incident_key')

    def __str__(self) :
        return self.Incident_key 

    def natural_key(self) :
        return (self.service_key, self.incidents_key)

    def clean(self) :
        if self.event_type not in [TRIGGER, RESOLVE, ACKNOWLEDGE] :
            raise ValidationError("'%s' is an invalid event type, valid values are 'trigger', 'resolve', 'acknowledge'" % self.event_type)
@python_2_unicode_compatible
class SchedulePolicyRule(models.Model) :
    '''
    schedule rule
    '''
    schedule_policy = models.ForeignKey(SchedulePolicy, related_name='rules')
    position = models.IntegerField()
    user_id = models.ForeignKey(User, blank=True, null=True)
    schedule = models.ForeignKey(Calendar, blank=True, null=True)
    escalate_after = models.IntegerField()

    class Meta:
        verbose_name = 'schedule_policy_icy_rule'
        verbose_name_plural = 'schedule_policy_icy_rules'

    def __str__(self) :
        return self.id

    @classmethod 
    def getRulesForService(cls, service) :
        return cls.objects.filter(schedule_policy = service.policy)

@python_2_unicode_compatible
class ServiceTokens(models.Model) :
    '''
    service tokens
    '''
    name = models.CharField(max_length=80)
    service_id = models.ForeignKey(Service)
    token_id = models.ForeignKey(Token)

    class Meta:
        verbose_name = 'service_token'
        verbose_name_plural = 'service_tokens'

    def __str__(self) :
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField('auth.User', related_name='profile')
    phone_number = models.CharField(max_length=50)
    pushover_user_key = models.CharField(max_length=50)
    pushover_app_key = models.CharField(max_length=50)
    slack_room_name = models.CharField(max_length=50)

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)



signals.post_save.connect(create_user_profile, sender=User)

signals.post_syncdb.disconnect(
    create_superuser,
    sender=auth_models,
    dispatch_uid='django.contrib.auth.management.create_superuser')
