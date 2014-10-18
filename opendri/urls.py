from django.conf import settings 
from django.conf.urls import patterns, include, url
from rest_framework import routers as rest_routers
from opendri import views 
from . import incidents 
from django.contrib import admin 
from schedule.periods import  Month, Week

admin.autodiscover()
rest_router = rest_routers.SimpleRouter(trailing_slash=False)
rest_router.register(r'users', views.UserViewSet)
rest_router.register(r'groups', views.GroupViewSet)
rest_router.register(r'schedule_policies', views.SchedulePolicyViewSet)
rest_router.register(r'schedule_policy_rules', views.SchedulePolicyRuleViewSet)
rest_router.register(r'create_event', incidents.IncidentViewSet)



urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'opendri.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^api/', include(rest_router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api-token-auth/', 'rest_framework.authtoken.views.obtain_auth_token'),    
    url(r'^login/$', 'opendri.auth.login'),
    url(r'^logout/$', 'opendri.auth.logout'),


    #users 
    url(r'^users/$', 'opendri.users.list'),
    url(r'users/new/$', 'opendri.users.new'),
    url(r'^users/edit/(?P<id>\d+)/$', 'opendri.users.edit'),
    url(r'^users/delete/(?P<id>\d+)/$', 'opendri.users.delete'),
    url(r'^users/save/$', 'opendri.users.save'),
   
    #SERVICE
    url(r'^services/$', 'opendri.services.list'),
    url(r'^services/new$', 'opendri.services.new'),
    url(r'^services/save$', 'opendri.services.save'),
    url(r'^services/edit/(.*)$', 'opendri.services.edit'),
    url(r'^services/delete/(.*)$', 'opendri.services.delete'),
    
    #SERVICES/API TOKEN
    url('^services/token_delete/(.*)$', 'opendri.services.token_delete'),
    url('^services/token_create/(.*)$', 'opendri.services.token_create'),
    # schedule 
    url(r'^schedule/', include('schedule.urls')),

    #SCHEDULES
    url(r'^schedules/$', 'opendri.schedules.list'),
    url(r'^schedules/new$', 'opendri.schedules.new'),
    url(r'^schedules/save', 'opendri.schedules.save'),
    url(r'^schedules/edit/(\d)$', 'opendri.schedules.edit'),
    url(r'^schedules/delete/(\d)$', 'opendri.schedules.delete'),
    url(r'^schedules/view/(.*)$', 'opendri.schedules.details',   kwargs={'periods': [Month]}),

    #EVENT
    url(r'^events/create/(?P<calendar_slug>[-\w]+)/$', 'opendri.events.create_or_edit_event', name='calendar_create_event'),
    url(r'^events/edit/(?P<calendar_slug>[-\w]+)/(?P<event_id>\d+)/$', 'opendri.events.create_or_edit_event', name='edit_event'),
    url(r'^events/destroy/(?P<calendar_slug>[-\w]+)/(?P<event_id>\d+)/$', 'opendri.events.destroy_event', name='destroy_event'),


    #Policies
    url(r'^policies/$', 'opendri.escalation.list'),
    url(r'^policies/new$', 'opendri.escalation.new'),
    url(r'^policies/save', 'opendri.escalation.save'),
    url(r'^policies/edit/(.*)$', 'opendri.escalation.edit'),
    url(r'^policies/delete/(.*)$', 'opendri.escalation.delete'),

    #url(r'^admin/', include(admin.site.urls)),
    #INCIDENTS
    url(r'^incidents/$', 'opendri.incidents.list'),
    url(r'^incidents/unhandled$', 'opendri.incidents.unhandled'),
    url(r'^incidents/unhandled/on-call$', 'opendri.incidents.unhandled_for_on_call_user'),
    url(r'^incidents/acknowledged$', 'opendri.incidents.acknowledged'),
    url(r'^incidents/details/(.*)$', 'opendri.incidents.details'),
    url(r'^incidents/update_type$', 'opendri.incidents.update_type'),
    url(r'^incidents/forward_incident', 'opendri.incidents.forward_incident'),
    url(r'^$', 'opendri.event_log.list'),
    url(r'^dashboard/$', 'opendri.event_log.list'),
    url(r'^dashboard/service/(.*)$', 'opendri.event_log.get'),

)
