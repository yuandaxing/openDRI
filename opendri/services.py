__author__ = 'ydx'

from django.contrib.auth.decorators import login_required 
from .models import Service, ServiceTokens, SchedulePolicy, Token, User 
from django.http import Http404
from django.template.response import TemplateResponse
from django.http import Http404, HttpResponseRedirect
from django.contrib import messages 
from django.core.urlresolvers import reverse 
from django.views.decorators.http import require_http_methods 
from django.db import IntegrityError 

@login_required()
def list(request) :
    services = Service.objects.all()
    return TemplateResponse(request, 'services/list.html', {'services' : services})

@login_required()
def delete(request, id) :
    try :
        serv = Service.objects.get(id = id) 
        serv.delete()
        return HttpResponseRedirect('/services/')
    except Service.DoesNotExist :
        raise Http404 

@login_required()
def edit(request, id) :
    try :
        service = Service.objects.get(id = id)
        try :
            api_keys = ServiceTokens.objects.filter(service_id = service)
        except ServiceTokens.DoesNotExist :
            api_keys = []

        policy = service.policy if service.policy else None 
        all_policies = SchedulePolicy.objects.all()
        return TemplateResponse(request, 'services/edit.html', {
            'item' : service, 
            'policy' : policy, 
            'policies' : all_policies, 
            'api_keys' : api_keys,
            })
    except Service.DoesNotExist:
        raise Http404

@login_required() 
def new(request) :
    all_policies = SchedulePolicy.objects.all()
    return TemplateResponse(request, 'services/edit.html',
                            {'policies': all_policies })

@login_required()
@require_http_methods(['POST'])
def save(request):
    try:
        service = Service.objects.get(id = request.POST['id'])
    except Service.DoesNotExist :
        service = Service()

    service.name = request.POST['name']
    service.escalate_after = request.POST['escalate_after']
    service.retry = request.POST['retry']

    if(request.POST['policy']) :
        pol = SchedulePolicy.objects.get(id = request.POST['policy'])
    else :
        pol = None

    service.policy = pol 
    
    try :
        service.save()
    except IntegrityError :
        messages.error(request, 'Service validation failed')
        if len(request.POST['id']) > 0 :
            return HttpResponseRedirect(reverse('opendri.services.edit', None, [str(request.POST['id'])]))
        else :
            return HttpResponseRedirect(reverse('opendri.services.new'))
    return HttpResponseRedirect('/services/')

@login_required()
def token_delete(request, token_id) :
    try :
        token = ServiceTokens.objects.get(id = token_id)
        token.delete()
        return HttpResponseRedirect(reverse('opendri.services.edit',  None, [str(token.service_id.id)]))
    except Service.DoesNotExist :
        raise Http404

@login_required()
@require_http_methods(['POST'])
def token_create(request, service_id):
    try :
        service = Service.objects.get(id = service_id)
        token = Token()
        token.save()
        service_token = ServiceTokens.objects.create(service_id = service, 
                                                     token_id = token, 
                                                     name = request.POST['key_name'])
        service_token.save()
        return HttpResponseRedirect(reverse('opendri.services.edit', None, [str(service_id)]))
    except Service.DoesNotExist :
        raise Http404
