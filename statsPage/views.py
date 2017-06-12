import datetime
import numpy
import hashlib
from pygeoip import GeoIP, GeoIPError
from random import choice, randint
import os
import re
import socket
import sys
import threading
import random
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Count
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context, loader, RequestContext
import requests
import json
from django.utils import timezone
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.csrf import csrf_exempt
from stats.models import *
from django.conf import settings
import dateutil.parser
import pycountry
import operator
import reverse_geocoder as rg
import math
from world_regions.models import Region
import copy
from ast import literal_eval
from itertools import tee, islice, chain, izip
from six import string_types
import time
from urllib import urlopen
import collections
import csv
# from itertools import izip



if not settings.configured:
    settings.configure()


####### TEMPLATE RENDERERS #######
def show_sign_in_page(request):
    '''
    Shows login page.
    '''
    try:
        username = request.POST['username']
        password = request.POST['password']
    except:
        return render_to_response('authentication_page.html', {
        }, context_instance=RequestContext(request))

    # try logging in
    user = authenticate(username = username, password = password)

    # Invalid login
    if user is None:
        return render_to_response('authentication_page.html', {
            'error_message': "Invalid username or password. Please try again.",
        }, context_instance=RequestContext(request))
    # De-activated user
    elif not user.is_active:
        return render_to_response('authentication_page.html', {
            'error_message': "The account you are trying to use has been disabled.<br/>" +
            "Please contact a system administrator.",
        }, context_instance=RequestContext(request))
    # Valid login, active user
    else:
        login(request, user)
        return HttpResponseRedirect('../')


def platform_bar(request):
    if request.user.is_authenticated():
        machine = Machine.objects.all()

        d_count = 0
        l_count = 0
        m_count = 0
        for mach in machine:
            if mach.platform == 'Darwin':
                d_count += 1
            elif mach.platform == 'Linux':
                l_count += 1
            elif mach.platform == 'Mozilla':
                m_count += 1

        sl_graph = l_count*2
        sm_graph = m_count*2
        sd_graph = d_count*2
        l_graph = l_count*4
        m_graph = m_count*4
        d_graph = d_count*4

        return render_to_response('session_stats/platform_bar.html', {'machine': machine, 'd_count': d_count, 'l_count': l_count, 'm_count': m_count, 'l_graph': l_graph, 'm_graph': m_graph, 'd_graph': d_graph, 'sl_graph': sl_graph, 'sm_graph': sm_graph, 'sd_graph': sd_graph }, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))


def all_years_pie(request):
    if request.user.is_authenticated():
        session = Session.objects.all()
        i = 0
        for sesh in session:
            if i == 0:
                stuff = dateutil.parser.parse(str(sesh.startDate))
                i = 1

        january = february = march = april = may = june = july = august = september = october = november = december = 0

        for sesh in session:
            if sesh.startDate.month == 1:
                january += 1
            if sesh.startDate.month == 2:
                february += 1
            if sesh.startDate.month == 3:
                march += 1
            if sesh.startDate.month == 4:
                april += 1
            if sesh.startDate.month == 5:
                may += 1
            if sesh.startDate.month == 6:
                june += 1
            if sesh.startDate.month == 7:
                july += 1
            if sesh.startDate.month == 8:
                august += 1
            if sesh.startDate.month == 9:
                september += 1
            if sesh.startDate.month == 10:
                october += 1
            if sesh.startDate.month == 11:
                november += 1
            if sesh.startDate.month == 12:
                december += 1

            months =[0,1,2,3,4,5,6,7,8,9,10,11]
            monthdata = [january,february,march,april,may,june,july,august,september,october,november,december]
            lineData = [[0,january],[1,february],[2, march],[3,april],[4, may],[5, june],[6, july],[7, august],[8, september],[9, october],[10, november],[11, december]]

        return render_to_response('time_stats/all_years_pie.html', { 'lineData': lineData, 'months': months, 'monthdata': monthdata }, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))


def world_stats(request):
    if request.user.is_authenticated():
        netinfo = NetInfo.objects.all()
        countries = []
        cities = []
        country_abbr = []
        for_country_names = []
        rement = 0
        # adds country names and respective cities to lists
        # these lists will be used later to help build the necessary structures.
        # duplicated lists are necessary for later comparing values to
        # determines number of users
        for net in netinfo:
            tmp_country_city = []
            tmp_country_city.append(net.country)
            tmp_country_city.append(net.city)
            cities.append(tmp_country_city)
            if net.country not in countries:
                # inc = []
                tmp_country = []
                countries.append(net.country)
                tmp_country.append(net.country)
                tmp_country.append(rement)
                # testing.append(tmp_country)
                country_abbr.append(tmp_country)
                dup_region = []
                d_region = "duplicate"
                dup_region.append(d_region)
                dup_region.append(tmp_country)
                # dup_testing.append(dup_region)
                for_country_names.append(dup_region)
                rement += 25

        countries.pop(0)
        country_abbr.pop(0)
        for_country_names.pop(0)
        the_size = len(countries)

        # this for loop gets the region name based on the country
        for country in for_country_names:
            region = Region.objects.get(countries__country=country[1][0])
            country[0] = region.name

        cities.pop(0)
        new_cities = []
        no_reps = []

        the_length = len(countries);
        sub_city = float(1000)/the_length
        mini_sub_city = 10

        # this for loop adds all the city names to a list such that there aren't
        # any duplicate city names. Moreover, this list gets the appropriate
        # country name associated with the respective city and adds it to the
        # new cities list -- it contains duplicates but the duplicates are
        # removed later in this function/action
        for cit in cities:
            if cit[1] != "Unknown":
                if cit[1] not in no_reps:
                    no_reps.append(cit[1])
                    c_name = pycountry.countries.get(alpha_2=cit[0])
                    cit[0] = c_name.name
                    new_c = []
                    new_c.append(cit[0])
                    new_c.append(cit[1])
                    new_c.append(mini_sub_city)
                    mini_sub_city += 14
                    new_cities.append(new_c)

        # translates country abbreviation to actual country name for list of countries
        for country in country_abbr:
            c_name = pycountry.countries.get(alpha_2=country[0])
            country[0] = c_name.name

        total = []
        dup_total = []
        dup_size = 25
        la_size = 25
        sub_num = sub_city
        circle_num = 0
        # this for loop figures out how many times a user from that particular
        # country have used the software
        for country in countries:
            rgb_num = random.randint(112, 220)
            sec_rgb_num = random.randint(79, 220)
            third_rgb_num = random.randint(79, 220)
            la_count = 0
            # okay = []
            country_count = []
            # dup_okay = []
            dup_country_count = []
            for net in netinfo:
                if net.country == country:
                   la_count += 1
            country_count.append(country)
            country_count.append(la_count)
            country_count.append(la_size)

            dup_country_count.append(country)
            dup_country_count.append(la_count)
            dup_country_count.append(la_size)
            stuff = "Hello"
            country_count.append(stuff)
            country_count.append(sub_num)
            country_count.append(rgb_num)
            country_count.append(sec_rgb_num)
            country_count.append(third_rgb_num)
            country_count.append(circle_num)

            dup_country_count.append(stuff)
            dup_country_count.append(sub_num)
            dup_country_count.append(rgb_num)
            dup_country_count.append(sec_rgb_num)
            dup_country_count.append(third_rgb_num)
            dup_country_count.append(circle_num)
            sub_num += sub_city
            la_size += 25
            la_future_region = "placement"
            region = Region.objects.get(countries__country=country)
            ala_region = region.name
            la_region = ala_region.encode('ascii', 'ignore')
            dup_all = []
            dup_region = []
            dup_region.append(la_region)
            dup_region.append(dup_size)
            dup_all.append(dup_region)
            dup_all.append(dup_country_count)
            dup_total.append(dup_all)
            dup_size += 25
            total.append(country_count)

        # needed to compute size of circles
        all_hits = 0
        for tot in total:
            all_hits += tot[1]

        # computes size of region circle
        for tot in total:
            num_circ = float(tot[1])/all_hits
            num_circ = num_circ * 100
            num_circ = math.ceil(num_circ)
            num_circ += 3.5
            tot[8] = num_circ

        # computes size of region circle
        for dup_tot in dup_total:
            num_circ = float(dup_tot[1][1])/all_hits
            num_circ = num_circ * 100
            num_circ = math.ceil(num_circ)
            num_circ += 3.5
            dup_tot[1][8] = num_circ

        for city in new_cities:
            city_count = 0
            for net in netinfo:
                if city[1] == net.city:
                    city_count += 1
            city.append(city_count)

        # translates country abbreviation to actual country name for list of countries
        for tot in total:
            c_name = pycountry.countries.get(alpha_2=tot[0])
            tot[0] = c_name.name

        # translates country abbreviation to actual country name for list of countries
        for dup_tot in dup_total:
            c_name = pycountry.countries.get(alpha_2=dup_tot[1][0])
            dup_tot[1][0] = c_name.name

        # this for loop iterates through the duplicated lists and decides
        # where to add the city (i.e. what nested list to add it to)
        # note: ciuded translates to city
        for dup_tot in dup_total:
            ciu = []
            for city in new_cities:
                ciudad =[]
                if city[0] == dup_tot[1][0]:
                    ciudad.append(city[1])
                    ciudad.append(city[2])
                    ciudad.append(city[3])
                    ciu.append(ciudad)
            dup_tot[1][3] = ciu

        # this for loop iterates through the duplicated lists and decides
        # where to add the city (i.e. what nested list to add it to)
        # note: ciuded translates to city
        for tot in total:
            ciu = []
            for city in new_cities:
                ciudad =[]
                if city[0] == tot[0]:
                    ciudad.append(city[1])
                    ciudad.append(city[2])
                    ciudad.append(city[3])
                    ciu.append(ciudad)
            tot[3] = ciu

        total = sorted(total, key=operator.itemgetter(1), reverse=True)
        dup_total = sorted(dup_total, key=operator.itemgetter(1), reverse=True)
        # dup_total = sorted(dup_total, key=lambda x : x[1][0])

        # necessary for figuring out hwere to place the region for dendogram
        dupregion_size = 67
        for duptot in dup_total:
            duptot[0][1] = dupregion_size
            dupregion_size += 67

        # necessary for figuring out hwere to place the region for dendogram
        dupthis_size = 67
        for duptot in dup_total:
            duptot[1][2] = dupthis_size
            dupthis_size += 67

        # necessary for figuring out hwere to place the region for dendogram
        this_size = 67
        for tot in total:
            tot[2] = this_size
            this_size += 67

        # necessary for figuring out hwere to place the city for dendogram
        dupla_mini_sub_city = 10
        for tot in dup_total:
             tot[1][3] = sorted(tot[1][3], key=operator.itemgetter(2), reverse=True)
             for each in tot[1][3]:
                 each[1] = dupla_mini_sub_city
                 dupla_mini_sub_city += 14

        # necessary for figuring out hwere to place the city for dendogram
        la_mini_sub_city = 10
        for tot in total:
            for each in tot[3]:
                each[1] = la_mini_sub_city
                la_mini_sub_city += 14

        all_regions = []
        for duptot in dup_total:
            all_regions.append(duptot[0][0])

        # six_jobs = []
        temporary_list = []
        # usually = []
        final_list = []
        for duptot in dup_total:
            if duptot[0][0] not in temporary_list:
                temporary_list.append(duptot[0][0])
                final_list.append(duptot)
            if duptot[0][0] in temporary_list:
                for ush in final_list:
                    if ush[0][0] == duptot[0][0]:
                        if ush[1][0] != duptot[1][0]:
                            ush.append(duptot[1])


        # tijuana = copy.deepcopy(final_list)
        finalFinalList = copy.deepcopy(final_list)
        # rollie = copy.deepcopy(dup_total)
        copy_dupTotal = copy.deepcopy(dup_total)
        # better = []
        listWithRgb = []
        tots = 0
        # for roll in copy_dupTotal:
        for cp_dT in copy_dupTotal:
           dup_rgb_num = random.randint(112, 220)
           dup_sec_rgb_num = random.randint(79, 220)
           dup_third_rgb_num = random.randint(79, 220)
           que_bueno = len(cp_dT)
           # bro = []
           tmp_rgb = []
           ice = []
           i = 1
           while i < que_bueno:
               ice.append(cp_dT[i])
               i = i+1
           tmp_rgb.append(cp_dT[0][0])
           tmp_rgb.append(cp_dT[0][1])
           tmp_rgb.append(ice)
           tmp_rgb.append(dup_rgb_num)
           tmp_rgb.append(dup_sec_rgb_num)
           tmp_rgb.append(dup_third_rgb_num)
           tmp_rgb.append(tots)
           listWithRgb.append(tmp_rgb)


        change_this = 107
        dont_lose = copy.deepcopy(listWithRgb)
        checked = []
        gaame = []
        for dont in dont_lose:
            if dont[0] not in gaame:
                thiiis = copy.deepcopy(dont)
                thiiis.pop(0)
                thiiis.pop(0)
                que = thiiis[0]
                que_length = len(que)
                total = 0
                for each in que:
                    total += each[1]
                dont[6] = total
                gaame.append(dont[0])
                checked.append(dont)

        for cp in finalFinalList:
            cp.pop(0)

        checked = sorted(checked, key=operator.itemgetter(6), reverse=True)

        for each in checked:
            each[1] = change_this
            change_this += 106

        switch = 67
        for each in checked:
            for each_country in each[2]:
                each_country[2] = switch
                switch += 67

        chase = 10
        for perk in checked:
            for switch in perk[2]:
               for proof in switch[3]:
                    proof[1] = chase
                    chase += 14

        return render_to_response('global_stats/world_stats.html', {'checked': checked, 'listWithRgb': listWithRgb, 'finalFinalList': finalFinalList, 'final_list': final_list, 'dup_total': dup_total, 'ciu': ciu, 'total': total, 'testing': testing, 'countries': countries, 'netinfo': netinfo }, context_instance = RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))


def geo_stats(request):
    if request.user.is_authenticated():
        netinfo = NetInfo.objects.all()
        countries = []
        cities = []
        # get country names that data has been collected on
        for net in netinfo:
            country_city = []
            country_city.append(net.country)
            country_city.append(net.city)
            cities.append(country_city)
            if net.country not in countries:
                countries.append(net.country)

        countries.pop(0)
        total = []
        # get total number of users from each country
        for country in countries:
            la_count = 0
            tmp_country_city = []
            for net in netinfo:
                if net.country == country:
                   la_count += 1
            tmp_country_city.append(country)
            tmp_country_city.append(la_count)
            total.append(tmp_country_city)

        country_names = []
        # use pycountry to get country name from abbreviation
        for cnty in countries:
            c_name = pycountry.countries.get(alpha_2=cnty)
            cnty = c_name.name
            country_names.append(c_name.name)

        # use pycountry to get country name from abbreviation
        for tot in total:
            c_name = pycountry.countries.get(alpha_2=tot[0])
            c_the_name = str(c_name.name)
            tot[0] = str(c_the_name)

        total = sorted(total, key=operator.itemgetter(1), reverse=True)
        country_names = json.dumps(country_names)
        totalJSON = json.dumps(total)

        return render_to_response('global_stats/geo_stats.html', { 'country_names': country_names, 'countries': countries, 'totalJSON' : totalJSON, 'total': total }, context_instance = RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))


def calendar_data(request):
    # getting rid of this?
    session = Session.objects.all()
    user = User.objects.all()
    start_sesh = []
    end_sesh = []
    total_sesh = []
    duration = []
    stuff_care = []
    la_strings = []
    sup_strings = []
    for sesh in session:
        nested_sesh = []
        start_sesh.append(sesh.startDate)
        end_sesh.append(sesh.lastDate)
        nested_sesh.append(sesh.startDate)
        nested_sesh.append(sesh.lastDate)
        total_sesh.append(nested_sesh)
        duration.append(nested_sesh)
        duration.append(sesh.lastDate - sesh.startDate)
        duration.append(sesh.netInfo)
        stuff_care.append(nested_sesh)
        start_s = sesh.startDate
        end_s = sesh.lastDate
        the_strings = []
        the_strings.append(start_s.strftime('%b, %-d, %Y, %I:%M %p'))
        the_strings.append(end_s.strftime('%b, %-d, %Y, %I:%M %p'))
        sup_strings.append(the_strings);
        la_strings.append("SUP")
        la_strings.append(start_s.strftime('%Y, %-m, %-d'))
        la_strings.append(end_s.strftime('%Y, %-m, %-d'))

    cool_strings = json.dumps(sup_strings)

    return render_to_response('session_stats/calendar_data.html', { 'cool_strings': cool_strings, 'la_strings': la_strings, 'stuff_care': stuff_care, 'duration': duration, 'total_sesh': total_sesh, 'start_sesh': start_sesh, 'end_sesh': end_sesh, 'session': session, 'data': "Hello" }, context_instance = RequestContext(request))


def bar_sesh(request):
    if request.user.is_authenticated():
        session = Session.objects.all()
        the_diff = []
        for sesh in session:
            nested_sesh = []
            start_s = sesh.startDate
            end_s = sesh.lastDate
            the_strings = []
            the_strings.append(start_s.strftime('%b, %-d, %Y, %I:%M %p'))
            the_strings.append(end_s.strftime('%b, %-d, %Y, %I:%M %p'))
            time_diff = end_s-start_s
            if time_diff != datetime.timedelta(seconds=0):
                time_vars = []
                the_diff.append(str(time_diff))
                time_vars.append(start_s.strftime('%Y'))
                time_vars.append(start_s.strftime('%B'))
                time_vars.append(start_s.strftime('%-m'))
                time_vars.append(start_s.strftime('%-I %p'))
                time_str = str(time_diff)

            one_min_sesh = one_hour_sesh = half_day_sesh = one_day_sesh = one_week_sesh = few_weeks_sesh = one_month_sesh = two_month_sesh = three_plus_sesh = []

            one_min = one_hour = half_day = one_day = one_week = few_weeks = one_month = two_month = three_plus = 0

            for sesh in session:
                start_s = sesh.startDate
                end_s = sesh.lastDate
                time_diff = end_s-start_s
                if time_diff >= datetime.timedelta(weeks=12):
                    three_plus_sesh.append(str(time_diff))
                    three_plus += 1
                if time_diff < datetime.timedelta(weeks=12) and time_diff >= datetime.timedelta(weeks=8):
                    two_month_sesh.append(str(time_diff))
                    two_month += 1
                if time_diff < datetime.timedelta(weeks=8) and time_diff >= datetime.timedelta(weeks=4):
                    one_month_sesh.append(str(time_diff))
                    one_month += 1
                if time_diff <= datetime.timedelta(weeks=4) and time_diff > datetime.timedelta(weeks=1):
                    few_weeks_sesh.append(str(time_diff))
                    few_weeks += 1
                if time_diff <= datetime.timedelta(weeks=1) and time_diff > datetime.timedelta(days=1):
                    one_week_sesh.append(str(time_diff))
                    one_week += 1
                if time_diff <= datetime.timedelta(days=1) and time_diff > datetime.timedelta(hours=12):
                    one_day_sesh.append(str(time_diff))
                    one_day += 1
                if time_diff <= datetime.timedelta(hours=12) and time_diff > datetime.timedelta(hours=1):
                    half_day_sesh.append(str(time_diff))
                    half_day += 1
                if time_diff <= datetime.timedelta(hours=1) and time_diff > datetime.timedelta(minutes=1):
                    one_hour_sesh.append(str(time_diff))
                    one_hour += 1
                if time_diff <= datetime.timedelta(minutes=1) and time_diff > datetime.timedelta(seconds=0):
                    one_min_sesh.append(str(time_diff))
                    one_min += 1

        all_the_seshs = {}
        all_the_seshs['one_min_sesh'] = one_min_sesh
        all_the_seshs['one_hour_sesh'] = one_hour_sesh
        all_the_seshs['half_day_sesh'] = half_day_sesh
        all_the_seshs['one_day_sesh'] = one_day_sesh
        all_the_seshs['one_week_sesh'] = one_week_sesh
        all_the_seshs['few_weeks_sesh'] = few_weeks_sesh
        all_the_seshs['one_month_sesh'] = one_month_sesh
        all_the_seshs['two_month_sesh'] = two_month_sesh
        all_the_seshs['three_plus_sesh'] = three_plus_sesh

        # all_seshs = {}
        all_seshs = collections.OrderedDict()
        all_seshs['time'] = 'value'
        all_seshs['one_min'] = one_min
        all_seshs['one_hour'] = one_hour
        all_seshs['half_day'] = half_day
        all_seshs['one_day'] = one_day
        all_seshs['one_week'] = one_week
        all_seshs['few_weeks'] = few_weeks
        all_seshs['one_month'] = one_month
        all_seshs['two_month'] = two_month
        all_seshs['three_plus'] = three_plus
        print all_seshs

        with open('statsPage/static/csv/bar_session.csv', 'wb') as csv_file:
            writer = csv.writer(csv_file)
            for key, value in all_seshs.items():
                writer.writerow([key, value])

        return render_to_response('session_stats/bar_sesh.html', { 'all_seshs': all_seshs, 'all_the_seshs': all_the_seshs, 'the_diff': the_diff, 'session': session }, context_instance = RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))


def show_log(request):
    '''
    Renders the logs.
    '''
    current_path = request.get_full_path()
    machine = Machine.objects
    return render_to_response('showlog.html', {'current_path': current_path, 'machine': machine
    }, context_instance=RequestContext(request))


def help(request):
    '''
    Renders the help page.
    '''
    return render_to_response('help.html', {}, context_instance=RequestContext(request))


def show_error_log(request):
    '''
    Renders the logs.
    '''
    return render_to_response('showerrorlog.html', {
    }, context_instance=RequestContext(request))



def show_error_details(request, error_id):
    '''
    Renders the template which shows detailed error info.
    '''
    error_obj = get_object_or_404(Error, pk=error_id)
    # countryLog = LogEvent.objects.filter(date__range = (date_from, timezone.now())).values('netInfo__country').annotate(count=Count('netInfo__country'))
    actions = LogEvent.objects.values('date', 'action__name').filter(date__lte=error_obj.date, user=error_obj.logEvent.user, machine=error_obj.logEvent.machine).order_by('-date')[:10]
    for action in actions:
        action['name'] = action['action__name']
        del(action['action__name'])

    return render_to_response('errordetails.html', {
        "id": error_id,
        "description": error_obj.description,
        "stack_trace": error_obj.stackTrace,
        "severity": error_obj.severity,
        "user_comments": error_obj.userComments,
        "execution_log": error_obj.executionLog,
        "date": error_obj.date,
        "source": error_obj.logEvent.source,
        "platform": error_obj.logEvent.machine.getPlatform(),
        "actions": actions,
    }, context_instance=RequestContext(request))



def show_debug(request):
    '''
    For debugging use only, will show a form where you can submit log events.
    '''
    if settings.DEBUG:
        return render_to_response('debug.html', {
        }, context_instance=RequestContext(request))
    else:
        raise Http404


def show_debug_error(request):
    '''
    For debugging use only, will show a form where you can submit errors to be logged.
    '''
    if settings.DEBUG:
        return render_to_response('debugerr.html', {
        }, context_instance=RequestContext(request))
    else:
        raise Http404


def pie_by_year(request):
    if request.user.is_authenticated():
        session = Session.objects.all()
        i = 0
        for sesh in session:
            if i == 0:
                stuff = dateutil.parser.parse(str(sesh.startDate))
                i = 1

        years = []
        for sesh in session:
           years.append(sesh.startDate.year)

        cool = numpy.unique(years)
        all_the_years = []
        total_years = []
        todo = []

        for year in cool:
            all_the_years.append(year)
            total_years.append(year)
            the_coolest = []
            for sesh in session:
                if year == sesh.startDate.year:
                    the_months = []
                    the_months.append(sesh.startDate.month)
                    the_coolest.append(the_months)
            all_the_years.append(the_coolest)
            todo.append(year)
            todo.append(all_the_years)


        deck = {}
        for year in cool:
            la_coolest = []
            for sesh in session:
                if year == sesh.startDate.year:
                    la_months = []
                    la_months.append(sesh.startDate.month)
                    la_coolest.append(la_months)
                    deck[year] = la_coolest

        with open('statsPage/static/json/by_year.json', 'w') as f:
            json.dump(deck, f)

        tot_size = len(total_years)
        return render_to_response('time_stats/pie_by_year.html', { 'deck': deck, 'todo': todo, 'total_size': tot_size, 'total_years': total_years, 'all_the_years': all_the_years }, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))


def testing(request):
    # was using this to get user data so can figure out geolocation to get
    # something cool on the home page for user to interact with about
    # their location. not sure if should just delete this or not
    if request.user.is_authenticated():
        session = Session.objects.all()
        send_url = 'http://freegeoip.net/json'
        r = requests.get(send_url)
        j = json.loads(r.text)
        lat = j['latitude']
        lon = j['longitude']

        latlon = []
        latlon.append(lat)
        latlon.append(lon)
        omg = rg.search(latlon)
        la_state = omg[0]['admin1']
        la_country = omg[0]['cc']
        all_the_info = pycountry.countries.get(alpha_2=la_country)
        country_name = all_the_info.name

        actions = Action.objects.all()
        action_meta = Action._meta

        act_names = []
        for act in actions:
           if ' ' in act.name:
               stuff = act.name
               new_stuff = stuff.split()
               act_names.append(new_stuff[0])
           if ' ' not in act.name:
               act_names.append(act.name)


        cool = numpy.unique(act_names)
        all_names = []
        for name in cool:
            func_names = []

            func_names.append(name)
            count = 0
            for act in act_names:
                if name == act:
                   count += 1
            func_names.append(count)
            all_names.append(func_names)

        all_names = json.dumps(all_names)

        return render_to_response('testing/testing.html', { 'all_names': all_names, 'req': request, 'lon': lon, 'lat': lat }, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def nested_chart(request):
    if request.user.is_authenticated():
        actions = Action.objects.all()
        action_meta = Action._meta

        act_names = []
        for act in actions:
           if 'Error' not in act.name:
               if ' ' in act.name:
                   stuff = act.name
                   new_stuff = stuff.split()
                   act_names.append(new_stuff[0])
               if ' ' not in act.name:
                   act_names.append(act.name)

        cool = numpy.unique(act_names)
        all_names = []
        for name in cool:
            func_names = []
            sub_list = []

            func_names.append(name)
            count = 0
            for act in act_names:
                if name == act:
                   count += 1
            func_names.append(count)
            func_names.append(sub_list)
            all_names.append(func_names)

        admire = []
        for name in cool:
            if "." not in name:
               admire.append(name)

        yeah = []
        chillin = copy.deepcopy(all_names)
        for ad in admire:
            infinity = []
            colder = []
            count = 0
            for halo in chillin:
                if ad == halo[0]:
                    count += halo[1]
                if ad in halo[0]:
                    if ad != halo[0]:
                        mask = []
                        tumblr = halo[0].split(".")
                        mask.append(tumblr[1])
                        mask.append(halo[1])
                        colder.append(mask)
            infinity.append(ad)
            infinity.append(count)
            infinity.append(colder)
            yeah.append(infinity)

        plan = []
        for fine in yeah:
            free = []
            yup = []
            if len(fine[2]) != 0:
                count = 0
                for previous, item, nxt in previous_and_next(fine[2]):
                    if item[0] in yup:
                        yup.append(item[1])
                    if item[0] not in yup:
                        yup.append(item[0])
                        yup.append(item[1])
                free.append(fine[0])
                free.append(yup)
                plan.append(free)

        growth = []
        for elegance in plan:
            learn = []
            count = 0
            for previous, item, nxt in previous_and_next(elegance[1]):
                if isinstance(item, (int, long)):
                    count += item
                    if nxt is None:
                        learn.append(count)
                if isinstance(item, string_types):
                    if count != 0:
                        learn.append(count)
                        count = 0
                    learn.append(item)
            growth.append(learn)

        huh = []
        for fine in yeah:
            if len(fine[2]) != 0:
                for grow in growth:
                    if fine[2][0][0] == grow[0]:
                        fine[2] = grow



        dup_all = copy.deepcopy(all_names)
        faith = []
        hope = []
        sub_states = []
        fake = 0
        for fade in dup_all:
            if '.' in fade[0]:
                states = fade[0].split('.')
                fade[0] = states[0]
                que_bueno = []
                nested_bueno = []
                try:
                    que_bueno.append(states[1])
                    try:
                        nested_bueno.append(states[2])
                        try:
                            super_nested = []
                            super_nested.append(states[3])
                            nested_bueno.append(super_nested)
                            # nested_bueno.append(states[3])
                        except IndexError:
                            pass
                    except IndexError:
                        pass
                except IndexError:
                    pass
                que_bueno.append(nested_bueno)
                fade[2].append(que_bueno)

        top_hier = []
        for dup in dup_all:
            if dup[0] not in top_hier:
                nested_hier = []
                nested_hier.append(dup[0])
                nested_hier.append([])
                top_hier.append(nested_hier)
            for d in dup[2]:
                for e in d:
                    pass

        sick = []
        idgt = []
        bay = []
        for dup in dup_all:
            laugh = []
            if dup[0] not in sick:
                sick.append(dup[0])
                bay.append(dup[0])
            try:
                if dup[2]:
                    if dup[2][0][0] not in idgt:
                        idgt.append(dup[2][0][0])
                        laugh.append(dup[0])
                        laugh.append(dup[2][0][0])
                        sick.append(laugh)
            except IndexError:
                print "index error, dup[2] does not exist"


        bed = []
        for not_sick in sick:
            if type(not_sick) == list:
                if not_sick[0] not in bed:
                    pass
                if not_sick[0] in bed:
                    for b in bed:
                        if b == not_sick[0]:
                            this = []
            if type(not_sick) != list:
                pass

        bay = json.dumps(bay)
        sick = json.dumps(sick)
        idgt = json.dumps(idgt)
        all_names = json.dumps(all_names)
        admire = json.dumps(admire)
        yeah = json.dumps(yeah)
        return render_to_response('action_stats/nested_chart.html', { 'growth': growth, 'plan': plan, 'yeah': yeah, 'admire': admire, 'bay': bay, 'bed': bed, 'idgt': idgt, 'sick': sick, 'dup_all': dup_all, 'sub_states': sub_states, 'faith': faith, 'hope': hope, 'cool': cool, 'all_names': all_names, 'act_names': act_names, 'action_meta': action_meta, 'actions': actions }, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))


# gathers the next and previous in a list and returns
# current, next, and previous to the call
# used in a few places, do not delete
def previous_and_next(some_iterable):
    prevs, items, nexts = tee(some_iterable, 3)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])
    return izip(prevs, items, nexts)


def most_used_pie(request):
    actions = Action.objects.all()
    action_meta = Action._meta

    act_names = []
    for act in actions:
       if 'Error' not in act.name:
           if ' ' in act.name:
               stuff = act.name
               new_stuff = stuff.split()
               act_names.append(new_stuff[0])
           if ' ' not in act.name:
               act_names.append(act.name)

    cool = numpy.unique(act_names)
    all_names = []
    for name in cool:
        func_names = []

        func_names.append(name)
        count = 0
        for act in act_names:
            if name == act:
               count += 1
        func_names.append(count)
        all_names.append(func_names)

    all_names = json.dumps(all_names)
    return render_to_response('action_stats/most_used_pie.html', { 'cool': cool, 'all_names': all_names, 'act_names': act_names, 'action_meta': action_meta, 'actions': actions }, context_instance=RequestContext(request))


def table(request):
    if request.user.is_authenticated():
        netinfo = NetInfo.objects.all()
        countries = []
        cities = []
        country_abbr = []
        for_country_names = []
        # adds country names and respective cities to lists
        # these lists will be used later to help build the necessary structures
        # duplicated lists are necessary for later comparing values to determine
        # number of users
        for net in netinfo:
            tmp_country_city = []
            tmp_country_city.append(net.country)
            tmp_country_city.append(net.city)
            cities.append(tmp_country_city)
            if net.country not in countries:
                tmp_country = []
                countries.append(net.country)
                tmp_country.append(net.country)
                country_abbr.append(tmp_country)
                dup_region = []
                d_region = "duplicate"
                dup_region.append(d_region)
                dup_region.append(tmp_country)
                for_country_names.append(dup_region)

        countries.pop(0)
        country_abbr.pop(0)
        for_country_names.pop(0)

        # this for loop gets the region name based on the country
        for country_name in for_country_names:
            region = Region.objects.get(countries__country=country_name[1][0])
            country_name[0] = region.name

        cities.pop(0)
        new_cities = []
        no_reps = []

        the_length = len(countries);
        sub_city = float(1000)/the_length
        mini_sub_city = 10

        # this for loop adds all the city names to a list such that there aren't
        # any duplicate city names. Moreover, this list gets the appropriate
        # country name associated with the respective city and adds it to the
        # new cities list -- it contains duplicates but the duplicates are
        # removed later in this function/action
        for cit in cities:
            if cit[1] != "Unknown":
                if cit[1] not in no_reps:
                    no_reps.append(cit[1])
                    c_name = pycountry.countries.get(alpha_2=cit[0])
                    cit[0] = c_name.name
                    new_c = []
                    new_c.append(cit[0])
                    new_c.append(cit[1])
                    new_c.append(mini_sub_city)
                    mini_sub_city += 14
                    new_cities.append(new_c)

        # translates country abbreviation to actual country name for list of countries
        for country in country_abbr:
            c_name = pycountry.countries.get(alpha_2=country[0])
            country[0] = c_name.name

        total = []
        dup_total = []
        dup_size = 25
        sub_num = sub_city
        # this for loop figures out how many times a user from that particular
        # country have used the software
        for country in countries:
            la_count = 0
            country_count = []
            dup_country_count = []
            for net in netinfo:
                if net.country == country:
                   la_count += 1
            country_count.append(country)
            country_count.append(la_count)

            dup_country_count.append(country)
            dup_country_count.append(la_count)
            needed_later = "placement"
            country_count.append(needed_later)
            country_count.append(sub_num)

            dup_country_count.append(needed_later)
            dup_country_count.append(sub_num)
            sub_num += sub_city
            la_future_region = "placement"
            region = Region.objects.get(countries__country=country)
            ala_region = region.name
            la_region = ala_region.encode('ascii', 'ignore')
            dup_all = []
            dup_region = []
            dup_region.append(la_region)
            dup_region.append(dup_size)
            dup_all.append(dup_region)
            dup_all.append(dup_country_count)
            dup_total.append(dup_all)
            dup_size += 25
            total.append(country_count)

        # counts how many users from a particular city have used the software
        for city in new_cities:
            city_count = 0
            for net in netinfo:
                if city[1] == net.city:
                    city_count += 1
            city.append(city_count)

        # translates country abbreviation to actual country name for list of countries
        for tot in total:
            c_name = pycountry.countries.get(alpha_2=tot[0])
            tot[0] = c_name.name

        # translates country abbreviation to actual country name for list of countries
        for dup_tot in dup_total:
            c_name = pycountry.countries.get(alpha_2=dup_tot[1][0])
            dup_tot[1][0] = c_name.name

        # this for loop iterates through the duplicated lists and decides
        # where to add the city (i.e. what nested list to add it to)
        for dup_tot in dup_total:
            ciu = []
            for city in new_cities:
                ciudad =[]
                if city[0] == dup_tot[1][0]:
                    ciudad.append(city[1])
                    ciudad.append(city[2])
                    ciudad.append(city[3])
                    ciu.append(ciudad)
            dup_tot[1][3] = ciu

        # this for loop iterates through the duplicated lists and decides
        # where to add the city (i.e. what nested list to add it to)
        for tot in total:
            ciu = []
            for city in new_cities:
                ciudad =[]
                if city[0] == tot[0]:
                    ciudad.append(city[1])
                    ciudad.append(city[2])
                    ciudad.append(city[3])
                    ciu.append(ciudad)
            tot[3] = ciu

        total = sorted(total, key=operator.itemgetter(1), reverse=True)
        dup_total = sorted(dup_total, key=operator.itemgetter(1), reverse=True)

        # necessary for figuring out where to place the region for dendogram
        dupregion_size = 67
        for duptot in dup_total:
            duptot[0][1] = dupregion_size
            dupregion_size += 67

        # necessary for figuring out where to place the region for dendogram
        dupthis_size = 67
        for duptot in dup_total:
            duptot[1][2] = dupthis_size
            dupthis_size += 67

        # necessary for figuring out where to place the region for dendogram
        this_size = 67
        for tot in total:
            tot[2] = this_size
            this_size += 67

        # necessary for figuring out where to place the city for dendogram
        dupla_mini_sub_city = 10
        for tot in dup_total:
             tot[1][3] = sorted(tot[1][3], key=operator.itemgetter(2), reverse=True)
             for each in tot[1][3]:
                 each[1] = dupla_mini_sub_city
                 dupla_mini_sub_city += 14

        # necessary for figuring out where to place the city for dendogram
        la_mini_sub_city = 10
        for tot in total:
            for each in tot[3]:
                each[1] = la_mini_sub_city
                la_mini_sub_city += 14

        temporary_list = []
        final_list = []
        # pieces together the respective regions, countries and cities
        for duptot in dup_total:
            if duptot[0][0] not in temporary_list:
                temporary_list.append(duptot[0][0])
                final_list.append(duptot)
            if duptot[0][0] in temporary_list:
                for ush in final_list:
                    if ush[0][0] == duptot[0][0]:
                        if ush[1][0] != duptot[1][0]:
                            ush.append(duptot[1])


        finalFinalList = copy.deepcopy(final_list)
        copy_dupTotal = copy.deepcopy(dup_total)
        # better = []
        listWithRgb = []
        tots = 0
        # necessary for random colors for dendogram for respective
        # regions, countries, and cities
        for cp_dT in copy_dupTotal:
           dup_rgb_num = random.randint(112, 220)
           dup_sec_rgb_num = random.randint(79, 220)
           dup_third_rgb_num = random.randint(79, 220)
           que_bueno = len(cp_dT)
           tmp_Rgb = []
           ice = []
           i = 1
           while i < que_bueno:
               ice.append(cp_dT[i])
               i = i+1
           tmp_Rgb.append(cp_dT[0][0])
           tmp_Rgb.append(cp_dT[0][1])
           tmp_Rgb.append(ice)
           tmp_Rgb.append(dup_rgb_num)
           tmp_Rgb.append(dup_sec_rgb_num)
           tmp_Rgb.append(dup_third_rgb_num)
           tmp_Rgb.append(tots)
           listWithRgb.append(tmp_Rgb)

        change_this = 107
        copy_LWR = copy.deepcopy(listWithRgb)
        checked = []
        rcc_withCount = []
        # gets the total count for each region and adds it to it's
        # respective region
        # for dont in copy_LWR:
        for LWR in copy_LWR:
            if LWR[0] not in rcc_withCount:
                LWR_copy = copy.deepcopy(LWR)
                LWR_copy.pop(0)
                LWR_copy.pop(0)
                country_cities = LWR_copy[0]
                cc_length = len(country_cities)
                total = 0
                for each in country_cities:
                    total += each[1]
                LWR[6] = total
                rcc_withCount.append(LWR[0])
                checked.append(LWR)

        for cp in finalFinalList:
            cp.pop(0)

        checked = sorted(checked, key=operator.itemgetter(6), reverse=True)

        for each in checked:
            each[1] = change_this
            change_this += 106

        switch = 67
        # for D3JS so that it knows where each country should be drawn
        for each in checked:
            for each_country in each[2]:
                each_country[2] = switch
                switch += 67

        increment = 10
        # for D3JS so that it knows where each city should be drawn
        for check in checked:
            for ch in check[2]:
               for cities in ch[3]:
                    cities[1] = increment
                    increment += 14

        return render_to_response('global_stats/table.html', {'checked': checked, 'listWithRgb': listWithRgb, 'finalFinalList': finalFinalList, 'dup_total': dup_total, 'ciu': ciu, 'total': total, 'country_abbr': country_abbr, 'countries': countries, 'netinfo': netinfo }, context_instance = RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

# https://stackoverflow.com/questions/406121/flattening-a-shallow-list-in-python
def flatten(x):
    result = []
    for el in x:
        if hasattr(el, "__iter__") and not isinstance(el, basestring):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result

# https://stackoverflow.com/questions/5389507/iterating-over-every-two-elements-in-a-list
def pairwise(iterable):
    "s -> (s0, s1), (s2, s3), (s4, s5), ..."
    a = iter(iterable)
    return izip(a, a)

def sessions_started_per_day(request):
    if request.user.is_authenticated():
        session = Session.objects.all()
        dates = []
        all_dates = []
        heatmap_dates = []
        # gathers all start dates for the session and puts it in
        # year month day format
        for sesh in session:
            nested = []
            dict_nested ={}
            just_date = sesh.startDate.date()
            str_date = sesh.startDate
            # below line is for format for google charts
            # strj_date = str_date.strftime('%Y,%-m,%d')
            # below line is for format for D3 JS
            strj_date = str_date.strftime('%Y%m%d')
            heatmap_date = str_date.strftime("%a %d %b %Y %H:%M:%S")
            if strj_date not in dates:
                count = 0
                dates.append(strj_date)
                nested.append(strj_date)
                nested.append(count)
                dict_nested["date"] = heatmap_date
                dict_nested["count"] = count
                heatmap_dates.append(dict_nested)
            if nested:
                all_dates.append(nested)
                heatmap_dates.append(dict_nested)

        for sesh in session:
            just_date = sesh.startDate.date()
            str_date = sesh.startDate
            # print str_date
            strj_date = str_date.strftime('%Y,%-m,%d')
            hm_date = str_date.strftime('%a %d %b %Y %H:%M:%S')
            for all_d in all_dates:
                if all_d[0] == strj_date:
                    all_d[1] += 1
            for hm_d in heatmap_dates:
                if hm_d['date'] == hm_date:
                    hm_d['count'] += 1

        with open('statsPage/static/csv/test.csv', 'wb') as f:
            writer = csv.writer(f)
            # for val in izip(stuff):
            for x, y in pairwise(all_dates):
                # writer.writerow(val)
                writer.writerow(x)
        # with open("target.csv", "w") as f:
        #     w = csv.writer(f)
        #     w.writerows(stuff)

        for all_d in all_dates:
            all_d[0] = json.dumps(all_d[0])

        return render_to_response('session_stats/sessions_started_per_day.html', {'heatmap_dates': heatmap_dates, 'all_dates': all_dates}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def unique_user_sesh(request):
    if request.user.is_authenticated():
        session = Session.objects.all()
        dates = []
        all_dates = []
        heatmap_dates = []
        # gathers all start dates for the session and puts it in
        # year month day format but also makes sure that for each day
        # the start dates are unique for each user
        for sesh in session:
            nested = []
            dict_nested ={}
            just_date = sesh.startDate.date()
            str_date = sesh.startDate
            strj_date = str_date.strftime('%Y,%-m,%d')
            heatmap_date = str_date.strftime("%a %d %b %Y %H:%M:%S")
            if strj_date not in dates:
                count = 0
                user_list = []
                dates.append(strj_date)
                nested.append(strj_date)
                nested.append(count)
                nested.append(user_list)
                dict_nested["date"] = heatmap_date
                dict_nested["count"] = count
                dict_nested["user_list"] = user_list
            if nested:
                all_dates.append(nested)
                heatmap_dates.append(dict_nested)

        for all_d in all_dates:
            for sesh in session:
                just_date = sesh.startDate.date()
                str_date = sesh.startDate
                strj_date = str_date.strftime('%Y,%-m,%d')
                if strj_date == all_d[0]:
                   if sesh.user not in all_d[2]:
                        all_d[2].append(sesh.user)
                        all_d[1] += 1

        for hm_d in heatmap_dates:
            # print hm_d
            for sesh in session:
                str_date = sesh.startDate
                hm_date = str_date.strftime('%a %d %b %Y %H:%M:%S')
                if hm_d['date'] == hm_date:
                    if sesh.user in hm_d['user_list']:
                        hm_d['count'] = len(hm_d['user_list'])


        for all_d in all_dates:
            all_d[0] = json.dumps(all_d[0])
            all_d[2] = []

        for hm_d in heatmap_dates:
            for key, value in hm_d.iteritems():
                if key == "user_list":
                    hm_d[key] = []

        return render_to_response('session_stats/unique_user_sesh.html', {'heatmap_dates': heatmap_dates, 'all_dates': all_dates}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def nested_d3(request):
    error_c = 0
    if request.user.is_authenticated():
        actions = Action.objects.all()
        act_names = []
        # this for loop gathers all main action names and
        # parses the action names that have a . in it to
        # get the main action name (first part of string prior
        # to the period)
        for act in actions:
              if 'Error' in act.name:
                error_c += 1
              if ' ' in act.name:
                  name = act.name
                  new_name = name.split()
                  act_names.append(new_name[0])
              if ' ' not in act.name:
                  act_names.append(act.name)

        partitioned_names = []
        o_list = []
        # this for loop parses all the action names that contain periods,
        # and adds them into a nested list called o_list
        for name in act_names:
            if "." in name:
                par_name = name.partition('.')
                partitioned_names.append(par_name[0])
                s = {}
                inner = par_name[2].partition('.')
                if "." in par_name[2]:
                    away = par_name[2].partition('.')
                    nested_names = {}
                    if '.' in away[2]:
                        nested_name_split = away[2].partition('.')
                        side = {}
                        side[nested_name_split[0]] = nested_name_split[2]
                        nested_names[away[0]] = side
                        s[par_name[0]] = nested_names
                    else:
                        nested_names[away[0]] = away[2]
                        s[par_name[0]] = nested_names
                else:
                    s[par_name[0]] = par_name[2]
                o_list.append(s)
            if "." not in name:
                partitioned_names.append(name)

        first_l = []
        # this for loop iterates through the main action names and adds
        # it into a nested list and initializes the counts to zero for each of the action names
        for name in act_names:
            first_d = collections.OrderedDict()
            second_l = []
            third_l = []
            if "." in name:
                part_name = name.partition('.')
                first_d["key"] = part_name[0]
                if "." in part_name[2]:
                    second_d = collections.OrderedDict()
                    nested_name = part_name[2].partition('.')
                    second_d["key"] = nested_name[0]
                    if "." in nested_name[2]:
                        third_d = collections.OrderedDict()
                        fourth_d = collections.OrderedDict()
                        fourth_l = []
                        snested_name = nested_name[2].partition('.')
                        third_d["key"] = snested_name[0]
                        fourth_d["key"] = snested_name[2]
                        fourth_d["values"] = 0
                        fourth_l.append(fourth_d)
                        third_d["values"] = fourth_l
                        third_l.append(third_d)
                        second_d["values"] = third_l
                        second_l.append(second_d)
                        first_d["values"] = second_l
                        first_l.append(first_d)
                    else:
                        second_d["values"] = nested_name[2]
                        second_l.append(second_d)
                else:
                      afirst = collections.OrderedDict()
                      af_list = []
                      afirst["key"] = part_name[2]
                      afirst["values"] = 0
                      af_list.append(afirst)
                      first_d["values"] = af_list
                      first_l.append(first_d)
            else:
                first_d["key"] = name
                first_d["value"] = 1
                first_l.append(first_d)

        eighth_l = []
        fourth_l = []
        im_empty = 'empty'
        s_empty = 'empty'
        dontchange = 0
        s_change = 0
        total = 0
        s_total = 0
        check = []
        first_check = 0
        s_check = []
        # iterates through the nested list, determines whether nested values
        # are a dictionary or not. If they are not a dictionary, check to see
        # if the name is in the temporary list. If it is, increment the count.
        # If it is not, move on to the next nested dictionary/list
        for l in first_l:
            for k, v in l.iteritems():
                if type(v) is unicode:
                    if v not in check:
                        check.append(v)
                        total = 0
                if type(v) is list:
                    for time in v:
                        for f_k, f_v in time.iteritems():
                            if type(f_v) is int:
                                if s_empty in s_check:
                                    s_total += 1
                                    f_v = s_total
                                    time.update({f_k: f_v})
                            if type(f_v) is unicode:
                                if f_v not in s_check:
                                    if s_change == 0:
                                        s_empty = f_v
                                        s_change = 1
                                    s_check.append(f_v)
                                    s_total = 0
                            if type(f_v) is list:
                                for i in f_v:
                                    for s_k, s_v in i.iteritems():
                                        if type(s_v) is list:
                                            for o in s_v:
                                                for i_k, i_v in o.iteritems():
                                                    if i_v not in eighth_l:
                                                        if type(i_v) is unicode:
                                                            eighth_l.append(i_v)
                                                    if i_v in eighth_l:
                                                        if type(i_v) is unicode:
                                                            if dontchange == 0:
                                                                im_empty = i_v
                                                                dontchange = 1
                                                    if type(i_v) is int:
                                                        if im_empty in eighth_l:
                                                            total += 0
                                                            i_v = total
                                                            o.update({i_k: i_v})

        outer_l = []
        true_false = 0
        # this for loop iterates through the nested list, if the type of the
        # nested value is an int, then depending on the level of nestedness,
        # it is determined that the function has zero nested functions and thus
        # it is then notated in the nested lists/dictionaries
        for l in first_l:
            outer = collections.OrderedDict()
            for k, v in l.iteritems():
                if type(v) is int:
                    outer["super_sub"] = "no super_sub"
                    outer["subfunction"] = "no subfunction"
                    outer["value"] = v
                    outer_l.append(outer)
                    true_false = 1
                if true_false == 1:
                    outer["main_function"] = "no function"
                    true_false = 0
                if type(v) is unicode:
                    outer["key"] = v
                if type(v) is list:
                    for time in v:
                        for f_k, f_v in time.iteritems():
                            if type(f_v) is int:
                                outer["super_sub"] = "no super_sub"
                                outer["subfunction"] = "no subfunction"
                                outer["value"] = f_v
                                outer_l.append(outer)
                            if type(f_v) is unicode:
                                outer["main_function"] = f_v
                            if type(f_v) is list:
                                for i in f_v:
                                    for s_k, s_v in i.iteritems():
                                        if type(s_v) is unicode:
                                            outer["subfunction"] = s_v
                                            outer["value"] = 1
                                            outer_l.append(outer)
                                        if type(s_v) is list:
                                            for y in s_v:
                                                for y_k, y_v in y.iteritems():
                                                    if type(y_v) is unicode:
                                                        outer["super_sub"] = y_v


        equal_count = 0
        added = 0
        new_dict = []
        # the above for loop does not remove duplicate entries. Thus, the for loop below
        # accomplishes that job and removes the duplicates by adding them to a new list
        for previous, item, nxt in previous_and_next(outer_l):
            if (previous != None) and (nxt != None):
                if (previous == item) or (nxt == item):
                    if previous == item:
                        if added == 0:
                            new_dict.append(previous)
                            added = 1
                        equal_count += 1
                    elif nxt == item:
                        if added == 0:
                            new_dict.append(nxt)
                            added = 1
                        equal_count += 1
                if previous != nxt:
                    equal_count = 0
                    added = 0

        new_list = []
        new_list = copy.deepcopy(outer_l)

        unique_docs = []
        sawn = []
        # the below for loop iterates through the list without duplicate entries and
        # adjusts the count for them by comparing the entries to the entries in the list with the duplicates
        for new in new_list:
            if(new['key'], new['main_function'], new['subfunction'], new['super_sub']) in sawn:
               for un in unique_docs:
                    if (un['key'] == new['key']) and (un['main_function'] == new['main_function']) and (un['subfunction'] == new['subfunction']) and (un['super_sub'] == new['super_sub']):
                        la_val = un['value']
                        la_val += 1
                        un.update({'value': la_val})
            elif(new['key'], new['main_function'], new['subfunction'], new['super_sub']) not in sawn:
                seen = (new['key'], new['main_function'], new['subfunction'], new['super_sub'])
                unique_docs.append(new)
                sawn.append(seen)


        no_names = []
        # this for loop creates a list determining which actions don't have nested functions.
        # If they don't have nested functions, they are added to the list called "no_names"
        # in which this is passed through to the javascript and used in the D3JS functions to
        # prevent the user from clicking a level too deep in the nested d3 diagrams
        for saw in unique_docs:
            if saw['main_function'] == 'no function':
               if (saw['key'] != 'genutil') and (saw['key'] != 'cdutil'):
                   no_names.append(saw['key'])
            elif (saw['subfunction'] == 'no subfunction') and (saw['main_function'] != 'no function'):
               no_names.append(saw['main_function'])
            elif (saw['super_sub'] == 'no super_sub') and (saw['main_function'] != 'no function') and (saw['subfunction'] != 'no subfunction'):
               no_names.append(saw['subfunction'])
            elif (saw['super_sub'] != 'no super_sub') and (saw['main_function'] != 'no function') and (saw['subfunction'] != 'no subfunction'):
               no_names.append(saw['super_sub'])

        outerJSON = collections.OrderedDict()
        outerList = []
        outerJSON.update({"key": "usage"})
        outerJSON.update({"values": outer_l})
        outerList.append(outerJSON)

        with open('statsPage/static/json/nested_d3.json', 'w') as f:
            json.dump(new_list, f)

        no_names = json.dumps(no_names)
        return render_to_response('testing/nested_d3.html', {'no_names': no_names, 'new_list': new_list, 'first_l': first_l, 'o_list': o_list}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

