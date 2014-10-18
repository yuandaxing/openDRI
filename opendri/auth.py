from django.contrib import auth
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse

def login(request) :
    username = request.POST.get('username', '')
    password = request.POST.get('password', '')
    user = auth.authenticate(username=username, password=password)
    if user and user.is_active :
        auth.login(request, user)
        return HttpResponseRedirect('/dashboard/')
    else :
        return TemplateResponse(request, 'auth/login.html')


def logout(request) :
    auth.logout(request)
    return HttpResponseRedirect('/login/')
