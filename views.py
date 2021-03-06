from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from uwregistry.forms import *
from uwregistry.models import Service
from datetime import datetime
from django.core.mail import mail_admins
import sys

def home(request):
    top_services = Service.objects.order_by('-date_submitted').filter(status=Service.APPROVE_STAT)[:10]
    return render_to_response(
            "home.html",
            {
		'services' : top_services,
	    },
            RequestContext(request))

def service(request, nick):
    #service must have this nick and be approved:
    service = get_object_or_404(Service, nickname=nick, status=Service.APPROVE_STAT)
    return render_to_response(
            "service.html",
            {
                'service' : service,
            },
            RequestContext(request))

def browse(request):
    services_list = Service.objects.extra(select={'lower_name': 'lower(name)'}).order_by('lower_name').filter(status=Service.APPROVE_STAT)
    paginator = Paginator(services_list, 20)
    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        services = paginator.page(page)
    except (EmptyPage, InvalidPage):
        services = paginator.page(paginator.num_pages)

    return render_to_response("browse.html", {
        'services' : services,
        }, context_instance=RequestContext(request))


@login_required
def mine(request):
    my_services = Service.objects.filter(owner=request.user)
    return render_to_response("mine.html", {
        'services' : my_services,
        }, RequestContext(request))
 

@login_required
def edit(request, nick):
    service = get_object_or_404(Service, nickname=nick, owner=request.user)
    if request.method == 'POST':
        form = ServiceEditForm(instance=service, data=request.POST)
        if form.is_valid():
            form.save(commit=False)
            service.date_modified = datetime.now()
            service.save()
            request.user.message_set.create(message='Service updated.')
            return HttpResponseRedirect('/service/mine/')
    else:
        form = ServiceEditForm(instance=service)

    return render_to_response(
            "submit.html", 
            {
                'form' : form,
            }, 
            RequestContext(request))

 

@login_required
def submit(request):

    if request.method == 'POST':
        form = ServiceForm(data=request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.owner = request.user
            service.status = service.SUBMIT_STAT
            service.date_submitted = datetime.now()
            service.date_modified = datetime.now()
            service.save()
            request.user.message_set.create(message='Your service has been submitted for moderation.')
            subject = 'New service "%s" submitted to the registry' % service.name
            body = 'Please go to http://webservices.washington.edu/admin/uwregistry/service/%d to review it' % service.id
            try:
                mail_admins(subject, body, fail_silently=False)
            except:
                sys.stderr.write("Email is failing!\n")
            return HttpResponseRedirect('/service/mine')
    else:
        form = ServiceForm()

    return render_to_response(
            "submit.html", 
            {
                'form' : form,
                'new' : True,
            }, 
            RequestContext(request))
