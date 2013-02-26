import sys
sys.path.append('app/scripts')
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context, loader, RequestContext
from django.utils import simplejson
#import  sample_plot_function as spf
from models import *
import hashlib
from django.contrib.auth import authenticate, login


def hello(request):
    return HttpResponse("Hello World")

def show_authentication_page(request):
    return render_to_response('authentication_page.html', {
    }, context_instance=RequestContext(request))

def showlog(request):
    try:
        username = request.POST['username']
        password = request.POST['password']
    except:
        # Either no username or no password supplied. They tried skipping the login and going
        # straight to the results!
        return HttpResponseRedirect('/log/')

    # try logging in
    user = authenticate(username=username, password=password)

    # Invalid login
    if user is None:
        return render_to_response('authentication_page.html', {
            'error_message': "Invalid username or password. Please try again.",
        }, context_instance=RequestContext(request))
    # De-activated user
    elif not user.is_active:
        return render_to_response('authentication_page.html', {
            'error_message': "The account you are trying ot use has been disabled.<br/>Please contact a system administrator.",
        }, context_instance=RequestContext(request))
    # Valid login, active user
    else:
        login(request, user)
        domain_list=Domains.objects.all()
        allaccess_list=Access.objects.all().order_by('-date')
        access_list=allaccess_list[:200]
        return render_to_response('showlog.html', {
            'domain_list': domain_list,
            'access_list': access_list,
        }, context_instance=RequestContext(request))
   
def insertlog(request,username,platform,source,action):
    ip=request.META['REMOTE_ADDR']
    ipsp=ip.split(".")
    ip1=ipsp[0]
    ip2=ipsp[1]
    try:
        name=request.META['REMOTE_HOST']
    except Exception, err:
        name='Unknown'
    user=hashlib.md5("%s.%s"%(ip,username)).hexdigest()
    domain=name
    try:
        domain_obj=Domains.objects.get(name=domain,ip1=ip1,ip2=ip2)
    except Exception, err:
        domain_obj=Domains()
        domain_obj.name=domain
        domain_obj.ip1=ip1
        domain_obj.ip2=ip2
        domain_obj.save()
    machine=hashlib.md5(ip).hexdigest()
    try:
        machine_obj=Machines.objects.get(md5=machine)
    except Exception, err:
        machine_obj=Machines()
        machine_obj.md5=machine
        machine_obj.domain=domain_obj
        machine_obj.platform=platform
        machine_obj.save()
    try:
        user_obj=Users.objects.get(md5=user)
    except Exception, err:
        user_obj=Users()
        user_obj.md5=user
        user_obj.machine=machine_obj
        user_obj.save()
    try:
        source_obj=Sources.objects.get(name=source)
    except Exception, err:
        source_obj=Sources()
        source_obj.name=source
        source_obj.save()
    try:
        action_obj=Actions.objects.get(name=action)
    except Exception, err:
        action_obj=Actions()
        action_obj.name=action
        action_obj.save()
    access_obj=Access()
    access_obj.user=user_obj
    access_obj.source=source_obj
    access_obj.action=action_obj
    access_obj.save()
        
    return HttpResponse("Log updated")