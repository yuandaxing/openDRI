from datetime import datetime

from django.contrib.auth.models import User
from django.db import transaction
from django.utils.datastructures import MultiValueDictKeyError
from notification.models import ScheduledNotification
from escalation_helper import services_where_user_is_on_call


__author__ = 'deathowl'

from .models import Incident, Service, ServiceTokens, Token, EventLog
from rest_framework import viewsets
from .serializers import IncidentSerializer
from rest_framework import status
from rest_framework.response import Response
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from django.core.exceptions import ValidationError
from django.http import Http404
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from notification.helper import NotificationHelper
import uuid
import base64


class IncidentViewSet(viewsets.ModelViewSet):

    """
    API endpoint that allows incidents to be viewed or edited.
    """
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    def create(self, request, *args, **kwargs):
        try:
            token = Token.objects.get(key = request.DATA["service_key"])
            serviceToken = ServiceTokens.objects.get(token_id=token)
            service = serviceToken.service_id
        except ServiceTokens.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return Response({}, status=status.HTTP_403_FORBIDDEN)

        with transaction.atomic():
            try:
                incident = Incident.objects.get(incident_key =  request.DATA["incident_key"], service_key = service)

                event_log_message = "%s api key changed %s from %s to %s" % (serviceToken.name, incident.incident_key, incident.event_type, request.DATA['event_type'])
            except (Incident.DoesNotExist, KeyError):
                incident = Incident()
                try:
                    incident.incident_key = request.DATA["incident_key"]
                except KeyError:
                    if request.DATA["event_type"] == Incident.TRIGGER:
                        incident.incident_key = base64.urlsafe_b64encode(uuid.uuid1().bytes).replace('=', '')
                    else:
                        response = {}
                        response["status"] = "failure"
                        response["message"] = "Mandatory parameter missing"
                        return Response(response, status=status.HTTP_400_BAD_REQUEST)
                incident.service_key = service

                event_log_message = "%s api key created %s with status %s" % (serviceToken.name, incident.incident_key, request.DATA['event_type'])

            if incident.event_type != Incident.ACKNOWLEDGE or (incident.event_type == Incident.ACKNOWLEDGE and request.DATA["event_type"] == Incident.RESOLVE ):
                event_log = EventLog()
                event_log.service_key = incident.service_key
                event_log.data = event_log_message
                event_log.occurred_at = datetime.now()
                event_log.save()

                incident.event_type = request.DATA["event_type"]
                incident.description = request.DATA["description"][:100]
                incident.details =request.DATA["details"]
                incident.occurred_at = datetime.now()
                try:
                    incident.full_clean()
                except ValidationError as e:
                    return Response({'errors': e.messages}, status=status.HTTP_400_BAD_REQUEST)
                incident.save()

                if incident.event_type == Incident.TRIGGER:
                    NotificationHelper.notify_incident(incident)
                if incident.event_type == "resolve" or incident.event_type == Incident.ACKNOWLEDGE:
                    ScheduledNotification.remove_all_for_incident(incident)

            headers = self.get_success_headers(request.POST)

            response = {}
            response["status"] = "success"
            response["message"] = "Event processed"
            response["incident_key"] = incident.incident_key
            return Response(response, status=status.HTTP_201_CREATED, headers=headers)

@login_required()
def list(request):
    services = Service.objects.all()
    try:
        actualService = Service.objects.get(id = request.GET['service'])
        incidents = Incident.objects.filter(service_key = actualService).order_by("-occurred_at")
    except (Service.DoesNotExist, MultiValueDictKeyError):
        incidents = Incident.objects.all().order_by("-occurred_at")
        actualService = None
    return TemplateResponse(request, 'incidents/list.html', {'incidents': incidents, 'title': 'All incidents',
                             'url': request.get_full_path(), 'services': services, 'actual': actualService})

@login_required()
def unhandled(request):
    services = Service.objects.all()
    try:
        actualService = Service.objects.get(id = request.GET['service'])
        incidents = Incident.objects.filter(service_key = actualService, event_type = Incident.TRIGGER).all().order_by("-occurred_at")
    except (Service.DoesNotExist, MultiValueDictKeyError):
        incidents = Incident.objects.filter(event_type = Incident.TRIGGER).all().order_by("-occurred_at")
    return TemplateResponse(request, 'incidents/list.html', {'incidents': incidents, 'title': 'Current unhandled incidents', 'url': request.get_full_path(), 'services': services})

@login_required()
def unhandled_for_on_call_user(request):
    services = Service.objects.all()
    services_to_list = services_where_user_is_on_call(request.user)
    incidents = Incident.objects.filter(service_key__in = services_to_list, event_type = Incident.TRIGGER).all().order_by("-occurred_at")
    return TemplateResponse(request, 'incidents/list.html', {'incidents': incidents, 'title': 'Current unhandled incidents', 'url': request.get_full_path(), 'services': services})

@login_required()
def acknowledged(request):
    services = Service.objects.all()
    try:
        actualService = Service.objects.get(id = request.GET['service'])
        incidents = Incident.objects.filter(service_key = actualService, event_type = Incident.ACKNOWLEDGE).all().order_by("-occurred_at")
    except (Service.DoesNotExist, MultiValueDictKeyError):
        incidents = Incident.objects.filter(event_type = Incident.ACKNOWLEDGE).all().order_by("-occurred_at")
    return TemplateResponse(request, 'incidents/list.html', {'incidents': incidents, 'title': 'Current acknowledged incidents', 'url': request.get_full_path(), 'services': services})

@login_required()
def details(request, id):
    try:
        incident = Incident.objects.get(id = id)
        users = User.objects.all()
        return TemplateResponse(request, 'incidents/details.html', {'item': incident, 'users': users, 'url': request.get_full_path()})
    except Service.DoesNotExist:
        raise Http404

@login_required()
@require_http_methods(["POST"])
def update_type(request):
    try:
        with transaction.atomic():
            incident = Incident.objects.get(id = request.POST['id'])

            logmessage = EventLog()
            logmessage.service_key = incident.service_key
            logmessage.data = "%s changed %s from %s to %s" % (request.user.username, incident.incident_key, incident.event_type, request.POST['event_type'])
            logmessage.occurred_at = datetime.now()
            logmessage.save()

            incident.event_type = request.POST['event_type']
            incident.occurred_at = datetime.now()
            incident.save()

            if incident.event_type == "resolve" or incident.event_type == Incident.ACKNOWLEDGE:
                ScheduledNotification.remove_all_for_incident(incident)

    except Incident.DoesNotExist:
        messages.error(request, 'Incident not found')
        return HttpResponseRedirect(request.POST['url'])
    except ValidationError as e:
        messages.error(request, e.messages)
    return HttpResponseRedirect(request.POST['url'])

@login_required()
@require_http_methods(["POST"])
def forward_incident(request):
    try:
        with transaction.atomic():
            incident = Incident.objects.get(id = request.POST['id'])
            user = User.objects.get(id = request.POST['user_id'])
            ScheduledNotification.remove_all_for_incident(incident)
            NotificationHelper.notify_user_about_incident(incident, user)
            event_log_message = "%s  changed assignee of incident :  %s  to %s" % (request.user.username, incident.incident_key, user.username)
            event_log = EventLog()
            event_log.service_key = incident.service_key
            event_log.data = event_log_message
            event_log.occurred_at = datetime.now()
            event_log.save()

    except Incident.DoesNotExist:
        messages.error(request, 'Incident not found')
        return HttpResponseRedirect(request.POST['url'])
    except User.DoesNotExist:
        messages.error(request, 'Incident not found')
        return HttpResponseRedirect(request.POST['url'])
    except ValidationError as e:
        messages.error(request, e.messages)
    return HttpResponseRedirect(request.POST['url'])
