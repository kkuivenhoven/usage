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
import time
from django.utils import timezone
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.csrf import csrf_exempt

from stats.models import *
from django.db import models

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

import geograpy
from django.http import JsonResponse


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



def show_log(request):
    '''
    Renders the logs.
    '''
    return render_to_response('showlog.html', {
    }, context_instance=RequestContext(request))



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



def help(request):
    '''
    Renders the help page.
    '''
    return render_to_response('help.html', {}, context_instance=RequestContext(request))


def table(request):
    if request.user.is_authenticated():
        netinfo = NetInfo.objects.all()
        regions = WorldRegionsRegion.objects.all()
        countries = WorldRegionsRegioncountry.objects.all()
        country_names = []
        for each in countries:
            abbr = each.country
            if abbr.encode("utf-8") == 'AN':
                pass
            else:
                c_name = pycountry.countries.get(alpha_2=abbr.encode("utf-8"))
                country_names.append(c_name.name)
        return render_to_response('global_stats/table.html', {'country_names': country_names, 'countries': countries, 'regions': regions, 'netinfo': netinfo}, context_instance = RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))


def geo_stats(request):
    if request.user.is_authenticated():
        netinfo = NetInfo.objects.all()
        regions = WorldRegionsRegion.objects.all()
        countries = WorldRegionsRegioncountry.objects.all()
        country_names = []
        country_abbr = []
        all_it = []
        for each in countries:
            abbr = each.country
            if abbr.encode("utf-8") == 'AN':
                pass
            else:
                c_name = pycountry.countries.get(alpha_2=abbr.encode("utf-8"))
                country_names.append(c_name.name)
                country_abbr.append(abbr.encode("utf-8"))
                nested = []
                nested.append(abbr.encode("utf-8"))
                nested.append(c_name.name)
                all_it.append(nested)


        with_R = []
        for one in all_it:
            n_R = []
            region = Region.objects.get(countries__country=one[0])
            n_R.append(region.name)
            n_R.append(one[1])
            with_R.append(n_R)

        regions_bro = []
        el_paiz = []
        outer_dict = {}
        outer_child = []
        for each in with_R:
            if each[0] in regions_bro:
                for out in outer_child:
                    if each[0] == out['name']:
                        nested_d = {}
                        nested_d["name"] = each[1]
                        nested_d["size"] = 0
                        out['children'].append(nested_d)
            else:
                regions_bro.append(each[0])
                nested_dict = {}
                nested_dict["name"] = each[0]
                nested_dict["children"] = []
                country_dict = {}
                country_dict["name"] = each[1]
                country_dict["size"] = 0
                nested_dict["children"].append(country_dict)
                outer_child.append(nested_dict)

        outer_dict["name"] = "usage"
        outer_dict["children"] = outer_child

        with open('statsPage/static/json/geo_stats.json', 'w') as outfile:
            json.dump(outer_dict, outfile)

        return render_to_response('global_stats/geo_stats.html', {}, context_instance = RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))


def all_years_pie(request):
    if request.user.is_authenticated():
        session = Session.objects.all()
        dates = []
        for sesh in session:
            dates.append(sesh.startDate.month)


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


        all_months = []

        jan_dict = {}
        feb_dict = {}
        mar_dict = {}
        apr_dict = {}
        may_dict = {}
        june_dict = {}
        july_dict = {}
        aug_dict = {}
        sept_dict = {}
        oct_dict = {}
        nov_dict = {}
        dec_dict = {}

        jan_dict['label'] = "January"
        jan_dict['count'] = january
        all_months.append(jan_dict)

        feb_dict['label'] = "February"
        feb_dict['count'] = february
        all_months.append(feb_dict)

        mar_dict['label'] = "March"
        mar_dict['count'] = march
        all_months.append(mar_dict)

        apr_dict['label'] = "April"
        apr_dict['count'] = april
        all_months.append(apr_dict)

        may_dict['label'] = "May"
        may_dict['count'] = may
        all_months.append(may_dict)

        june_dict['label'] = "June"
        june_dict['count'] = june
        all_months.append(june_dict)

        july_dict['label'] = "July"
        july_dict['count'] = july
        all_months.append(july_dict)

        aug_dict['label'] = "August"
        aug_dict['count'] = august
        all_months.append(aug_dict)

        sept_dict['label'] = "September"
        sept_dict['count'] = september
        all_months.append(sept_dict)

        oct_dict['label'] = "October"
        oct_dict['count'] = october
        all_months.append(oct_dict)

        nov_dict['label'] = "November"
        nov_dict['count'] = november
        all_months.append(nov_dict)

        dec_dict['label'] = "December"
        dec_dict['count'] = december
        all_months.append(dec_dict)

        with open('statsPage/static/csv/all_years_pie.csv', 'wb') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["month", "count"])
            writer.writerow([0, january])
            writer.writerow([1, february])
            writer.writerow([2, march])
            writer.writerow([3, april])
            writer.writerow([4, may])
            writer.writerow([5, june])
            writer.writerow([6, july])
            writer.writerow([7, august])
            writer.writerow([8, september])
            writer.writerow([9, october])
            writer.writerow([10, november])
            writer.writerow([11, december])

        all_months = json.dumps(all_months)
        return render_to_response('time_stats/all_years_pie.html', {'all_months': all_months, 'dates': dates, 'session': session}, context_instance = RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))


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


def bar_session(request):
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

        with open('statsPage/static/csv/bar_session.csv', 'wb') as csv_file:
            writer = csv.writer(csv_file)
            for key, value in all_seshs.items():
                writer.writerow([key, value])

        return render_to_response('session_stats/bar_session.html', { 'all_seshs': all_seshs, 'all_the_seshs': all_the_seshs, 'the_diff': the_diff, 'session': session }, context_instance = RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

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
            for x, y in pairwise(all_dates):
                writer.writerow(x)

        for all_d in all_dates:
            all_d[0] = json.dumps(all_d[0])

        return render_to_response('session_stats/sessions_started_per_day.html', {'heatmap_dates': heatmap_dates, 'all_dates': all_dates}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))


def unique_user_session(request):
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

        return render_to_response('session_stats/unique_user_session.html', {'heatmap_dates': heatmap_dates, 'all_dates': all_dates}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))


def world_stats(request):
    if request.user.is_authenticated():
        netinfo = NetInfo.objects.all()
        regions = WorldRegionsRegion.objects.all()
        countries = WorldRegionsRegioncountry.objects.all()
        country_names = []
        for each in countries:
            abbr = each.country
            if abbr.encode("utf-8") == 'AN':
                pass
            else:
                c_name = pycountry.countries.get(alpha_2=abbr.encode("utf-8"))
                country_names.append(c_name.name)
        with open('statsPage/static/csv/testing.csv', 'wb') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Rank", "Country (or dependent territory)", "Population", "Date"])
            i = 1
            for each in regions:
                writer.writerow([i, each.name, 0, time.strftime("%d/%m/%Y")])
                i+=1

        return render_to_response('global_stats/world_stats.html', {'country_names': country_names, 'countries': countries, 'regions': regions, 'netinfo': netinfo}, context_instance = RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))


# gathers the next and previous in a list and returns
# current, next, and previous to the call

# gathers the next and previous in a list and returns
# current, next, and previous to the call
# used in a few places, do not delete
def previous_and_next(some_iterable):
    prevs, items, nexts = tee(some_iterable, 3)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])
    return izip(prevs, items, nexts)



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
        return render_to_response('action_stats/nested_d3.html', {'no_names': no_names, 'new_list': new_list, 'first_l': first_l, 'o_list': o_list}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))


def survey(request):
    if request.method == 'POST':
        if request.is_ajax():
            stuff = request.POST.get('surveyData')
            stuff = json.loads(stuff)
            with open('statsPage/static/json/surveyJson.json', 'a') as outfile:
                if os.stat("statsPage/static/json/surveyJson.json").st_size != 0:
                    outfile.seek(-1, os.SEEK_END)
                    outfile.truncate()
                    outfile.write(',')
                    outfile.write('\n')
                    json.dump(stuff, outfile)
                    outfile.write(']')
                else:
                    outfile.write('[')
                    json.dump(stuff, outfile)
                    outfile.write(']')
    if request.method != 'POST':
        with open("statsPage/static/json/survey_new.json") as json_data:
            surveyMaterial = json.load(json_data)
            json_data.close()
    surveyMaterial = json.dumps(surveyMaterial)
    return render_to_response('survey_results/survey.html', {'surveyMaterial': surveyMaterial}, context_instance=RequestContext(request))

def survey_results(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        installProc = []
        cdatPack = []
        packageUsage = []
        mostUsed = []
        fileFormat = []
        favoriteOS = []
        cdatUsage = []
        improv = []
        python3comp = []
        viz = []
        useOnWindows = []

        for sur in surRes:
            installProc.append(sur['installationProcess'])
            cdatPack.append(sur['cdatPackages'])
            packageUsage.append(sur['packageUsage'])
            mostUsed.append(sur['mostUsed'])
            fileFormat.append(sur['fileFormat'])
            favoriteOS.append(sur['favoriteOs'])
            improv.append(sur['Improvements'])
            python3comp.append(sur['python3compatible'])
            viz.append(sur['otherVizGraphics'])
            useOnWindows.append(sur['useOnWindows'])

        return render_to_response('survey_results/survey_results.html', {'mostUsed': mostUsed, 'fileFormat': fileFormat, 'favoriteOS': favoriteOS, 'cdatUsage': cdatUsage, 'improv': improv, 'python3comp': python3comp, 'viz': viz, 'useOnWindows': useOnWindows, 'packageUsage': packageUsage, 'cdatPack': cdatPack, 'installProc': installProc, 'surRes': surRes}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def results_installProc(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        installProc = []
        veryEasy = 0
        easy = 0
        moderate = 0
        difficult = 0
        veryDifficult = 0
        user_resp = []
        for sur in surRes:
            installProc.append(sur['installationProcess'])
            if sur['installationProcess'] == 'veryEasy':
                veryEasy += 1
            if sur['installationProcess'] == 'easy':
                easy += 1
            if sur['installationProcess'] == 'difficult':
                difficult += 1
            if sur['installationProcess'] == 'moderate':
                moderate += 1
            if sur['installationProcess'] == 'veryDifficult':
                veryDifficult += 1
            if "question2" in sur:
                user_resp.append(sur['question2']) 

        all_responses = []

        d_easy = {}
        d_veasy = {}
        d_mod = {}
        d_diff = {}
        d_vdiff = {}

        d_veasy['label'] = "Very Easy"
        d_veasy['count'] = veryEasy
        d_easy['label'] = "Easy"
        d_easy['count'] = easy
        d_mod['label'] = "Moderate"
        d_mod['count'] = moderate
        d_diff['label'] = "Difficult"
        d_diff['count'] = difficult
        d_vdiff['label'] = "Very Difficult"
        d_vdiff['count'] = veryDifficult
        
        all_responses.append(d_veasy)
        all_responses.append(d_easy)
        all_responses.append(d_mod)
        all_responses.append(d_diff)
        all_responses.append(d_vdiff)

        all_responses = json.dumps(all_responses)
        return render_to_response('survey_results/r_installProc.html', { 'user_resp': user_resp, 'all_responses': all_responses, 'installProc': installProc, 'veryEasy': veryEasy, 'easy': easy, 'difficult': difficult, 'moderate': moderate, 'veryDifficult': veryDifficult }, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))
   
def guiUsefulness(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        veryEasy = 0
        easy = 0
        moderate = 0
        difficult = 0
        veryDifficult = 0
        for sur in surRes:
            if sur['guiUsefulness'] == 'veryEasy':
                veryEasy += 1
            if sur['guiUsefulness'] == 'easy':
                easy += 1
            if sur['guiUsefulness'] == 'difficult':
                difficult += 1
            if sur['guiUsefulness'] == 'moderate':
                moderate += 1
            if sur['guiUsefulness'] == 'veryDifficult':
                veryDifficult += 1

        all_responses = []

        d_easy = {}
        d_veasy = {}
        d_mod = {}
        d_diff = {}
        d_vdiff = {}

        d_veasy['label'] = "Very Easy"
        d_veasy['count'] = veryEasy
        d_easy['label'] = "Easy"
        d_easy['count'] = easy
        d_mod['label'] = "Moderate"
        d_mod['count'] = moderate
        d_diff['label'] = "Difficult"
        d_diff['count'] = difficult
        d_vdiff['label'] = "Very Difficult"
        d_vdiff['count'] = veryDifficult
        
        all_responses.append(d_veasy)
        all_responses.append(d_easy)
        all_responses.append(d_mod)
        all_responses.append(d_diff)
        all_responses.append(d_vdiff)

        all_responses = json.dumps(all_responses)
        return render_to_response('survey_results/guiUsefulness.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))
   
def results_cdat_pack(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        cdms2 = vcs = vcsaddons = cdutil = other = 0
        for sur in surRes:
            for each in sur['cdatPackages']:
                if each == 'cdms2':
                    cdms2 += 1
                if each == 'vcs':
                    vcs += 1
                if each == 'cdutil':
                    cdutil += 1
                if each == 'vcsAddOns':
                    vcsaddons += 1
                if each == 'otherPackages':
                    other += 1

        all_responses = []

        d_cdms2 = {}
        d_vcs = {}
        d_cdutil = {}
        d_vcsaddons = {}
        d_other = {}

        d_cdms2['label'] = "cdms2"
        d_cdms2['count'] = cdms2
        d_vcs['label'] = "vcs"
        d_vcs['count'] = vcs
        d_cdutil['label'] = "cdutil"
        d_cdutil['count'] = cdutil
        d_vcsaddons['label'] = "vcsaddons"
        d_vcsaddons['count'] = vcsaddons
        d_other['label'] = "other"
        d_other['count'] = other

        all_responses.append(d_cdms2)
        all_responses.append(d_vcs)
        all_responses.append(d_cdutil)
        all_responses.append(d_vcsaddons)
        all_responses.append(d_other)
        
        all_responses = json.dumps(all_responses)
        return render_to_response('survey_results/cdat_pack.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))


def results_packageUsage(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        yes = 0
        no = 0
        all_responses = []
        for sur in surRes:
            if sur['packageUsage'] == 'yes':
                yes += 1
            if sur['packageUsage'] == 'no':
                no += 1

        d_no = {}
        d_yes = {}

        d_no['label'] = "No"
        d_no['count'] = no
        d_yes['label'] = "Yes"
        d_yes['count'] = yes

        all_responses.append(d_no)
        all_responses.append(d_yes)
        all_responses = json.dumps(all_responses)
        return render_to_response('survey_results/packageUsage.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def python3comp(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        yes = 0
        no = 0
        all_responses = []
        for sur in surRes:
            if sur['python3compatible'] == 'yes':
                yes += 1
            if sur['python3compatible'] == 'no':
                no += 1

        d_no = {}
        d_yes = {}

        d_no['label'] = "No"
        d_no['count'] = no
        d_yes['label'] = "Yes"
        d_yes['count'] = yes

        all_responses.append(d_no)
        all_responses.append(d_yes)
        all_responses = json.dumps(all_responses)
        return render_to_response('survey_results/python3comp.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def results_mostUsed(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        all_responses = []
        dataio = graphics = analysis = 0
        for sur in surRes:
            if sur['mostUsed'] == 'dataio':
                dataio += 1
            if sur['mostUsed'] == 'graphics':
                graphics += 1
            if sur['mostUsed'] == 'analysis':
                analysis += 1

        d_dataio = {}
        d_graphics = {}
        d_analysis = {}

        d_dataio['label'] = "Data I/O"
        d_dataio['count'] = dataio
        d_graphics['label'] = "Graphics"
        d_graphics['count'] = graphics
        d_analysis['label'] = "Analysis"
        d_analysis['count'] = analysis

        all_responses.append(d_dataio)
        all_responses.append(d_graphics)
        all_responses.append(d_analysis)

        all_responses = json.dumps(all_responses)
        return render_to_response('survey_results/mostUsed.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))


def response_time(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        all_responses = []
        lessThanHour = 0
        day = 0
        week = 0
        more = 0
        for sur in surRes:
            if sur['responseTime'] == 'lessThanHour':
                lessThanHour += 1
            if sur['responseTime'] == 'day':
                day += 1
            if sur['responseTime'] == 'week':
                week += 1
            if sur['responseTime'] == 'more':
                more += 1

        d_lessThanHour = {}
        d_day = {}
        d_week = {}
        d_more = {}

        d_lessThanHour['label'] = "< 1 hour"
        d_lessThanHour['count'] = lessThanHour
        d_day['label'] = "1 day"
        d_day['count'] = day
        d_week['label'] = "Week"
        d_week['count'] = week
        d_more['label'] = "More"
        d_more['count'] = more

        all_responses.append(d_lessThanHour)
        all_responses.append(d_day)
        all_responses.append(d_week)
        all_responses.append(d_more)

        all_responses = json.dumps(all_responses)
        return render_to_response('survey_results/responseTime.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))


def cdat_used_for(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        climate = weather = biology = astronomy = other = 0 
        all_responses = []
        free_resp = []
        for sur in surRes:
            if "cdatUSEDfreeRESPONSE" in sur:
                free_resp.append(sur['cdatUSEDfreeRESPONSE']) 
            for each in sur['cdatUsedFor']:
                if each == 'climate':
                    climate += 1
                if each == 'weather':
                    weather += 1
                if each == 'biology':
                    biology += 1
                if each == 'astronomy':
                    astronomy += 1
                if each == 'otherUses':
                    other += 1

        d_climate = {}
        d_weather = {}
        d_biology = {}
        d_astronomy = {}
        d_other = {}

        d_climate['label'] = "Climate"
        d_climate['count'] = climate
        d_weather['label'] = "Weather"
        d_weather['count'] = weather
        d_biology['label'] = "Biology"
        d_biology['count'] = biology
        d_astronomy['label'] = "Astronomy"
        d_astronomy['count'] = astronomy
        d_other['label'] = "Other"
        d_other['count'] = other

        all_responses.append(d_climate)
        all_responses.append(d_weather)
        all_responses.append(d_biology)
        all_responses.append(d_astronomy)
        all_responses.append(d_other)

        all_responses = json.dumps(all_responses)
        return render_to_response('survey_results/cdatUsedFor.html', {'free_resp': free_resp, 'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))


def commandLine_UI(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        all_responses = []
        veryEasy = easy = moderate = difficult = veryDifficult = 0 
        for sur in surRes:
            if sur['comndLineInterface'] == 'veryEasy':
                veryEasy += 1
            if sur['comndLineInterface'] == 'easy':
                easy += 1
            if sur['comndLineInterface'] == 'moderate':
                moderate += 1
            if sur['comndLineInterface'] == 'difficult':
                difficult += 1
            if sur['comndLineInterface'] == 'veryDifficult':
                veryDifficult += 1

        d_veryE = {}
        d_easy = {}
        d_mod = {}
        d_dif = {}
        d_veryD = {}

        d_veryE['label'] = "Very Easy"
        d_veryE['count'] = veryEasy
        d_easy['label'] = "Easy"
        d_easy['count'] = easy
        d_mod['label'] = "Moderate"
        d_mod['count'] = moderate
        d_dif['label'] = "Difficult"
        d_dif['count'] = difficult
        d_veryD['label'] = "Very Difficult"
        d_veryD['count'] = veryDifficult

        all_responses.append(d_veryE)
        all_responses.append(d_easy)
        all_responses.append(d_mod)
        all_responses.append(d_dif)
        all_responses.append(d_veryD)

        all_responses = json.dumps(all_responses)
        return render_to_response('survey_results/commandLine_UI.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def userSupportUsefulness(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        all_responses = []
        veryUseful = useful = moderate = notAtAllUseful = 0
        for sur in surRes:
            if sur['userSupportUsefulness'] == 'veryUseful':
                veryUseful += 1
            if sur['userSupportUsefulness'] == 'useful':
                useful += 1
            if sur['userSupportUsefulness'] == 'moderatelyUseful':
                moderate += 1
            if sur['userSupportUsefulness'] == 'notAtAllUseful':
                notAtAllUseful += 1

        d_veryE = {}
        d_easy = {}
        d_mod = {}
        d_dif = {}

        d_veryE['label'] = "Very Useful"
        d_veryE['count'] = veryUseful
        d_easy['label'] = "Useful"
        d_easy['count'] = useful
        d_mod['label'] = "Moderately Useful"
        d_mod['count'] = moderate
        d_dif['label'] = "Not at all Useful"
        d_dif['count'] = notAtAllUseful

        all_responses.append(d_veryE)
        all_responses.append(d_easy)
        all_responses.append(d_mod)
        all_responses.append(d_dif)

        all_responses = json.dumps(all_responses)
        return render_to_response('survey_results/userSupportUsefulness.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def graphicsMostUsed(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        OneD = isofill = plotEnhancements = vector = ThreedScalar = isoline = primitives = Threedvector = meshfill = projections = boxfill = templates = overlay = other = 0
        all_responses = []
        for sur in surRes:
            if 'graphicsMostUsed' in sur:
                for each in sur['graphicsMostUsed']:
                    if each == '1d':
                        OneD += 1
                    if each == 'Isofill':
                        isofill += 1
                    if each == 'plotEnhancements':
                        plotEnhancements += 1
                    if each == 'Vector':
                        vector += 1
                    if each == '3dScalar':
                        ThreedScalar += 1
                    if each == 'Isoline':
                        isoline += 1
                    if each == 'Primitives':
                        primitives += 1
                    if each == '3dvector':
                        Threedvector += 1
                    if each == 'Meshfill':
                        meshfill += 1
                    if each == 'Projections':
                        projections += 1
                    if each == 'Boxfill':
                        boxfill += 1
                    if each == 'templates':
                        templates += 1
                    if each == 'Overlay':
                        overlay += 1
                    if each == 'otherGraphics':
                        other += 1

        d_1d = {}
        d_isofill = {}
        d_pE = {}
        d_vector = {}
        d_3dScalar = {}
        d_isoline = {}
        d_primitives = {}
        d_3dvector = {}
        d_mesh = {}
        d_proj = {}
        d_boxfill = {}
        d_templates = {}
        d_overlay = {}
        d_other = {}

        d_1d['label'] = "1D"
        d_1d['count'] = OneD
        d_isofill['label'] = "Isofill"
        d_isofill['count'] = isofill
        d_pE['label'] = "Plot Enhancements"
        d_pE['count'] = plotEnhancements
        d_vector['label'] = "Vector"
        d_vector['count'] = vector
        d_3dScalar['label'] = "3D Scalar"
        d_3dScalar['count'] = ThreedScalar
        d_isoline['label'] = "Isoline"
        d_isoline['count'] = isoline
        d_primitives['label'] = "Primitives"
        d_primitives['count'] = primitives
        d_3dvector['label'] = "3D Vector"
        d_3dvector['count'] = Threedvector
        d_mesh['label'] = "Meshfill"
        d_mesh['count'] = meshfill
        d_proj['label'] = "Projections"
        d_proj['count'] = projections
        d_boxfill['label'] = "Boxfill"
        d_boxfill['count'] = boxfill
        d_templates['label'] = "Templates"
        d_templates['count'] = templates
        d_overlay['label'] = "Overlay"
        d_overlay['count'] = overlay
        d_other['label'] = "Other"
        d_other['count'] = other

        all_responses.append(d_1d)
        all_responses.append(d_isofill)
        all_responses.append(d_pE)
        all_responses.append(d_vector)
        all_responses.append(d_3dScalar)
        all_responses.append(d_isoline)
        all_responses.append(d_primitives)
        all_responses.append(d_3dvector)
        all_responses.append(d_mesh)
        all_responses.append(d_proj)
        all_responses.append(d_boxfill)
        all_responses.append(d_templates)
        all_responses.append(d_overlay)
        all_responses.append(d_other)

        all_responses = json.dumps(all_responses)
        return render_to_response('survey_results/graphicsMostUsed.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def averageTimeToPlot(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        minute = fiveMinutes = tenMinutes = thirtyMinutes = oneHour = moreOnehour = oneDay = moreOneDay = 0
        all_responses = []
        for sur in surRes:
            if sur['averageTimeToPlot'] == 'minute':
                minute += 1
            if sur['averageTimeToPlot'] == '5minutes':
                fiveMinutes += 1
            if sur['averageTimeToPlot'] == '10minutes':
                tenMinutes += 1
            if sur['averageTimeToPlot'] == '30minutes':
                thirtyMinutes += 1
            if sur['averageTimeToPlot'] == '1hour':
                oneHour += 1
            if sur['averageTimeToPlot'] == 'more1hour':
                moreOnehour += 1
            if sur['averageTimeToPlot'] == '1day':
                oneDay += 1
            if sur['averageTimeToPlot'] == 'more1day':
                moreOneDay += 1

        d_min = {}
        d_5min = {}
        d_10min = {}
        d_30min = {}
        d_1hour = {}
        d_more1hour = {}
        d_1day = {}
        d_moreOneDay = {}

        d_min['label'] = "Minute"
        d_min['count'] = minute
        d_5min['label'] = "5 Minutes"
        d_5min['count'] = fiveMinutes
        d_10min['label'] = "10 Minutes"
        d_10min['count'] = tenMinutes
        d_30min['label'] = "30 Minutes"
        d_30min['count'] = thirtyMinutes
        d_1hour['label'] = "1 hour"
        d_1hour['count'] = oneHour
        d_more1hour['label'] = "> 1 hour"
        d_more1hour['count'] = moreOnehour
        d_1day['label'] = "1 day"
        d_1day['count'] = oneDay
        d_moreOneDay['label'] = "> 1 day"
        d_moreOneDay['count'] = moreOneDay

        all_responses.append(d_min)
        all_responses.append(d_5min)
        all_responses.append(d_10min)
        all_responses.append(d_30min)
        all_responses.append(d_1hour)
        all_responses.append(d_more1hour)
        all_responses.append(d_1day)
        all_responses.append(d_moreOneDay)

        all_responses = json.dumps(all_responses)
        return render_to_response('survey_results/averageTimeToPlot.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def howOftenUsed(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        everyday = fewTimesWeek = coupleWeeks = onceMonth = coupleMonths = 0
        all_responses = []
        for sur in surRes:
            if sur['Cdat_Usage'] == '1':
                everyday += 1
            if sur['Cdat_Usage'] == '2':
                fewTimesWeek += 1
            if sur['Cdat_Usage'] == '3':
                coupleWeeks += 1
            if sur['Cdat_Usage'] == '4':
                onceMonth += 1
            if sur['Cdat_Usage'] == '5':
                coupleMonths += 1

        d_everyday = {}
        d_fewWeeks = {}
        d_coupleWeeks = {}
        d_onceMonth = {}
        d_coupleMonths = {}

        d_everyday['label'] = "Everyday"
        d_everyday['count'] = everyday
        d_fewWeeks['label'] = "A few times a week"
        d_fewWeeks['count'] = fewTimesWeek
        d_coupleWeeks['label'] = "Every couple weeks"
        d_coupleWeeks['count'] = coupleWeeks
        d_onceMonth['label'] = "Once a month"
        d_onceMonth['count'] = onceMonth
        d_coupleMonths['label'] = "Every couple months"
        d_coupleMonths['count'] = coupleMonths

        all_responses.append(d_everyday)
        all_responses.append(d_fewWeeks)
        all_responses.append(d_coupleWeeks)
        all_responses.append(d_onceMonth)
        all_responses.append(d_coupleMonths)

        all_responses = json.dumps(all_responses)
        return render_to_response('survey_results/howOftenUsed.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def dataFormatConvention(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        coords = climateAndForecast = other = 0
        all_responses = []
        for sur in surRes:
            if sur['dataFormatConvention'] == 'coords':
                coords += 1
            if sur['dataFormatConvention'] == 'climateAndForecast':
                climateAndForecast += 1
            if sur['dataFormatConvention'] == 'otherConv':
                other += 1

        d_coords = {}
        d_climate = {}
        d_other = {}

        d_coords['label'] = "Coords"
        d_coords['count'] = coords
        d_climate['label'] = "Climate and Forecast"
        d_climate['count'] = climateAndForecast
        d_other['label'] = "Other"
        d_other['count'] = other

        all_responses.append(d_coords)
        all_responses.append(d_climate)
        all_responses.append(d_other)

        all_responses = json.dumps(all_responses)
        return render_to_response('survey_results/dataFormatConvention.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def youTubeHelp(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        extremelyUseful = useful = modUseful = notUseful = 0
        all_responses = []
        youT_resp = []
        for sur in surRes:
            if sur['youTubeVideos'] == 'extremelyUseful':
                extremelyUseful += 1
            if sur['youTubeVideos'] == 'useful':
                useful += 1
            if sur['youTubeVideos'] == 'modUseful':
                modUseful += 1
            if sur['youTubeVideos'] == 'notUseful':
                notUseful += 1
            if "YouTubeIndication" in sur:
                youT_resp.append(sur['YouTubeIndication'])

        d_extU = {}
        d_use = {}
        d_modU = {}
        d_notU = {}

        d_extU['label'] = "Extremely Useful"
        d_extU['count'] = extremelyUseful
        d_use['label'] = "Useful"
        d_use['count'] = useful
        d_modU['label'] = "Moderately Useful"
        d_modU['count'] = modUseful
        d_notU['label'] = "Not Useful at all"
        d_notU['count'] = notUseful

        all_responses.append(d_extU)
        all_responses.append(d_use)
        all_responses.append(d_modU)
        all_responses.append(d_notU)

        all_responses = json.dumps(all_responses)
        return render_to_response('survey_results/youTubeHelp.html', {'youT_resp': youT_resp, 'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def docUsefulness(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        extremelyUseful = useful = modUseful = notUseful = 0
        doc_resp = []
        all_responses = []
        for sur in surRes:
            if sur['docUsefulness'] == 'extremelyUseful':
                extremelyUseful += 1
            if sur['docUsefulness'] == 'useful':
                useful += 1
            if sur['docUsefulness'] == 'modUseful':
                modUseful += 1
            if sur['docUsefulness'] == 'notUseful':
                notUseful += 1
            if "docsNotUseful" in sur:
                doc_resp.append(sur['docsNotUseful'])


        d_extU = {}
        d_use = {}
        d_modU = {}
        d_notU = {}

        d_extU['label'] = "Extremely Useful"
        d_extU['count'] = extremelyUseful
        d_use['label'] = "Useful"
        d_use['count'] = useful
        d_modU['label'] = "Moderately Useful"
        d_modU['count'] = modUseful
        d_notU['label'] = "Not Useful at all"
        d_notU['count'] = notUseful

        all_responses.append(d_extU)
        all_responses.append(d_use)
        all_responses.append(d_modU)
        all_responses.append(d_notU)

        all_responses = json.dumps(all_responses)
        return render_to_response('survey_results/docUsefulness.html', {'doc_resp': doc_resp, 'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def galleryUsefulness(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        extremelyUseful = useful = modUseful = notUseful = 0
        gal_resp = []
        all_responses = []
        for sur in surRes:
            if sur['galleryUsefulness'] == 'extremelyUseful':
                extremelyUseful += 1
            if sur['galleryUsefulness'] == 'useful':
                useful += 1
            if sur['galleryUsefulness'] == 'modUseful':
                modUseful += 1
            if sur['galleryUsefulness'] == 'notUseful':
                notUseful += 1
            if "galleryIndication" in sur:
                gal_resp.append(sur['galleryIndication'])


        d_extU = {}
        d_use = {}
        d_modU = {}
        d_notU = {}

        d_extU['label'] = "Extremely Useful"
        d_extU['count'] = extremelyUseful
        d_use['label'] = "Useful"
        d_use['count'] = useful
        d_modU['label'] = "Moderately Useful"
        d_modU['count'] = modUseful
        d_notU['label'] = "Not Useful at all"
        d_notU['count'] = notUseful

        all_responses.append(d_extU)
        all_responses.append(d_use)
        all_responses.append(d_modU)
        all_responses.append(d_notU)

        all_responses = json.dumps(all_responses)
        return render_to_response('survey_results/galleryUsefulness.html', {'gal_resp': gal_resp, 'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def averageTimeToPlot(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        minute = fiveMinutes = tenMinutes = thirtyMinutes = oneHour = moreOnehour = oneDay = moreOneDay = 0
        all_responses = []
        for sur in surRes:
            if sur['averageTimeToPlot'] == 'minute':
                minute += 1
            if sur['averageTimeToPlot'] == '5minutes':
                fiveMinutes += 1
            if sur['averageTimeToPlot'] == '10minutes':
                tenMinutes += 1
            if sur['averageTimeToPlot'] == '30minutes':
                thirtyMinutes += 1
            if sur['averageTimeToPlot'] == '1hour':
                oneHour += 1
            if sur['averageTimeToPlot'] == 'more1hour':
                moreOnehour += 1
            if sur['averageTimeToPlot'] == '1day':
                oneDay += 1
            if sur['averageTimeToPlot'] == 'more1day':
                moreOneDay += 1

        d_min = {}
        d_5min = {}
        d_10min = {}
        d_30min = {}
        d_1hour = {}
        d_more1hour = {}
        d_1day = {}
        d_moreOneDay = {}

        d_min['label'] = "Minute"
        d_min['count'] = minute
        d_5min['label'] = "5 Minutes"
        d_5min['count'] = fiveMinutes
        d_10min['label'] = "10 Minutes"
        d_10min['count'] = tenMinutes
        d_30min['label'] = "30 Minutes"
        d_30min['count'] = thirtyMinutes
        d_1hour['label'] = "1 hour"
        d_1hour['count'] = oneHour
        d_more1hour['label'] = "> 1 hour"
        d_more1hour['count'] = moreOnehour
        d_1day['label'] = "1 day"
        d_1day['count'] = oneDay
        d_moreOneDay['label'] = "> 1 day"
        d_moreOneDay['count'] = moreOneDay

        all_responses.append(d_min)
        all_responses.append(d_5min)
        all_responses.append(d_10min)
        all_responses.append(d_30min)
        all_responses.append(d_1hour)
        all_responses.append(d_more1hour)
        all_responses.append(d_1day)
        all_responses.append(d_moreOneDay)

        all_responses = json.dumps(all_responses)
        return render_to_response('survey_results/averageTimeToPlot.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))


def fav_OS(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        all_responses = []
        linux = darwin = windows = 0
        for sur in surRes:
            for each in sur['favoriteOs']:
                if each == 'linux':
                    linux += 1
                if each == 'darwin':
                    darwin += 1
                if each == 'windows':
                    windows += 1

        d_lin = {}
        d_dar = {}
        d_win = {}

        d_lin['label'] = "Linux"
        d_lin['count'] = linux
        d_dar['label'] = "Darwin"
        d_dar['count'] = darwin
        d_win['label'] = "Windows"
        d_win['count'] = windows

        all_responses.append(d_lin)
        all_responses.append(d_dar)
        all_responses.append(d_win)

        all_responses = json.dumps(all_responses)

        return render_to_response('survey_results/favOS.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def gui_dis_like(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        all_responses = []
        for sur in surRes:
           all_responses.append(sur['GUIdislikeLike'])
        return render_to_response('survey_results/guiDisLike.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def fileFormat(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        all_responses = []
        for sur in surRes:
           all_responses.append(sur['fileFormat'])
        return render_to_response('survey_results/fileFormat.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def analysisAvgLength(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        all_responses = []
        for sur in surRes:
           all_responses.append(sur['analysisAverageLength'])
        return render_to_response('survey_results/analysisAverageLength.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def additionalConcerns(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        all_responses = []
        for sur in surRes:
           all_responses.append(sur['additionalConcerns'])
        return render_to_response('survey_results/additionalConcerns.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def cmndline(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        all_responses = []
        for sur in surRes:
           all_responses.append(sur['cmndlineDislikeLike'])
        return render_to_response('survey_results/cmndline.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def otherVizGraphics(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        all_responses = []
        for sur in surRes:
           all_responses.append(sur['otherVizGraphics'])
        return render_to_response('survey_results/otherVizGraphics.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def improvements(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        all_responses = []
        for sur in surRes:
           all_responses.append(sur['Improvements'])
        return render_to_response('survey_results/improvements.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def whichFeature(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        all_responses = []
        for sur in surRes:
           all_responses.append(sur['whichFeature'])
        return render_to_response('survey_results/whichFeature.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def useOnWindows(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        no = yes = 0
        all_responses = []
        for sur in surRes:
            if sur['useOnWindows'] == 'yes':
                yes += 1
            if sur['useOnWindows'] == 'no':
                no += 1
        
        d_no = {}
        d_yes = {}

        d_no['label'] = "No"
        d_no['count'] = no
        d_yes['label'] = "Yes"
        d_yes['count'] = yes

        all_responses.append(d_no)
        all_responses.append(d_yes)

        all_responses = json.dumps(all_responses)
        return render_to_response('survey_results/useOnWindows.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def userAwareness(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        no = yes = 0
        all_responses = []
        for sur in surRes:
            if sur['awareVcs'] == 'yes':
                yes += 1
            if sur['awareVcs'] == 'no':
                no += 1
        
        d_no = {}
        d_yes = {}

        d_no['label'] = "No"
        d_no['count'] = no
        d_yes['label'] = "Yes"
        d_yes['count'] = yes

        all_responses.append(d_no)
        all_responses.append(d_yes)

        all_responses = json.dumps(all_responses)
        return render_to_response('survey_results/userAwareness.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def subPackageUsage(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        cdutil = genutil = vcs = cdp = cdms2 = 0
        all_responses = []
        for sur in surRes:
            if "subPackageUsage" in sur:
                for each in sur['subPackageUsage']:
                    if each == 'cdutil':
                        cdutil += 1
                    if each == 'genutil':
                        genutil += 1
                    if each == 'vcs':
                        vcs += 1
                    if each == 'cdp':
                        cdp += 1
                    if each == 'cdms2':
                        cdms2 += 1
        
        d_cdutil = {}
        d_genutil = {}
        d_vcs = {}
        d_cdp = {}
        d_cdms2 = {}

        d_cdutil['label'] = "cdutil"
        d_cdutil['count'] = cdutil
        d_genutil['label'] = "genutil"
        d_genutil['count'] = genutil
        d_vcs['label'] = "vcs"
        d_vcs['count'] = vcs
        d_cdp['label'] = "cdp"
        d_cdp['count'] = cdp
        d_cdms2['label'] = "cdms2"
        d_cdms2['count'] = cdms2

        all_responses.append(d_cdutil)
        all_responses.append(d_genutil)
        all_responses.append(d_vcs)
        all_responses.append(d_cdp)
        all_responses.append(d_cdms2)

        all_responses = json.dumps(all_responses)
        return render_to_response('survey_results/subPackageUsage.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def NoUserAwareness(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        no = yes = 0
        all_responses = []
        for sur in surRes:
            if "NoAwareVcs" in sur:
                if sur['NoAwareVcs'] == 'yes':
                    yes += 1
                if sur['NoAwareVcs'] == 'no':
                    no += 1
        
        d_no = {}
        d_yes = {}

        d_no['label'] = "No"
        d_no['count'] = no
        d_yes['label'] = "Yes"
        d_yes['count'] = yes

        all_responses.append(d_no)
        all_responses.append(d_yes)

        all_responses = json.dumps(all_responses)
        return render_to_response('survey_results/NoUserAwareness.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def YesUserAwareness(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        always = inProd = sometimes = never = 0
        all_responses = []
        for sur in surRes:
            if "YesAwareVcs" in sur:
                if sur['YesAwareVcs'] == 'always':
                    always += 1
                if sur['YesAwareVcs'] == 'inProd':
                    inProd += 1
                if sur['YesAwareVcs'] == 'sometimes':
                    sometimes += 1
                if sur['YesAwareVcs'] == 'never':
                    never += 1
        
        d_always = {}
        d_inProd = {}
        d_sometimes = {}
        d_never = {}

        d_always['label'] = "Always"
        d_always['count'] = always
        d_inProd['label'] = "In production"
        d_inProd['count'] = inProd
        d_sometimes['label'] = "Sometimes"
        d_sometimes['count'] = sometimes
        d_never['label'] = "Never"
        d_never['count'] = never

        all_responses.append(d_always)
        all_responses.append(d_inProd)
        all_responses.append(d_sometimes)
        all_responses.append(d_never)

        all_responses = json.dumps(all_responses)
        return render_to_response('survey_results/YesUserAwareness.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def sizeOfDataFiles(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        kilo = mega = giga = tera = peta = 0
        all_responses = []
        for sur in surRes:
            if sur['sizeOfDataFiles'] == 'kilobytes':
                kilo += 1
            if sur['sizeOfDataFiles'] == 'megabytes':
                mega += 1
            if sur['sizeOfDataFiles'] == 'terabytes':
                tera += 1
            if sur['sizeOfDataFiles'] == 'gigabytes':
                giga += 1
            if sur['sizeOfDataFiles'] == 'petabytes':
                peta += 1
        
        d_kilo = {}
        d_mega = {}
        d_tera = {}
        d_peta = {}
        d_giga = {}

        d_kilo['label'] = "Kilobytes"
        d_kilo['count'] = kilo
        d_mega['label'] = "Megabytes"
        d_mega['count'] = mega
        d_tera['label'] = "Terabytes"
        d_tera['count'] = tera
        d_peta['label'] = "Petabytes"
        d_peta['count'] = peta
        d_giga['label'] = "Gigabytes"
        d_giga['count'] = giga

        all_responses.append(d_kilo)
        all_responses.append(d_mega)
        all_responses.append(d_tera)
        all_responses.append(d_peta)
        all_responses.append(d_giga)

        all_responses = json.dumps(all_responses)
        return render_to_response('survey_results/sizeOfDataFiles.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def dataFileFormat(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        asciii = binary = netcdf = hdf4 = hdf5 = hdfEos = grib2 = pp = grads = grib = other = 0
        all_responses = []
        free_resp = []
        for sur in surRes:
            if "theOtherFormat" in sur:
                free_resp.append(sur['theOtherFormat'])
            for each in sur['dataFileFormat']:
                if each == 'ascii':
                    asciii += 1
                if each == 'binary':
                    binary += 1
                if each == 'netcdf':
                    netcdf += 1
                if each == 'hdf4':
                    hdf4 += 1
                if each == 'hdf5':
                    hdf5 += 1
                if each == 'hdfEos':
                    hdfEos += 1
                if each == 'pp':
                    pp += 1
                if each == 'grads':
                    grads += 1
                if each == 'grib2':
                    grib2 += 1
                if each == 'grib':
                    grib += 1
                if each == 'otherFormat':
                    other += 1
        
        d_ascii = {}
        d_bin = {}
        d_net = {}
        d_hdf4 = {}
        d_hdf5 = {}
        d_hdfEos = {}
        d_pp = {}
        d_grads = {}
        d_grib = {}
        d_grib2 = {}
        d_other = {}

        d_ascii['label'] = "Ascii"
        d_ascii['count'] = asciii
        d_bin['label'] = "Binary"
        d_bin['count'] = binary
        d_net['label'] = "NetCDF"
        d_net['count'] = netcdf
        d_hdf4['label'] = "HDF 4"
        d_hdf4['count'] = hdf4
        d_hdf5['label'] = "HDF 5"
        d_hdf5['count'] = hdf5
        d_hdfEos['label'] = "HDF EOS"
        d_hdfEos['count'] = hdfEos
        d_pp['label'] = "PP"
        d_pp['count'] = pp
        d_grads['label'] = "GrADS"
        d_grads['count'] = grads
        d_grib['label'] = "GRIB"
        d_grib['count'] = grib
        d_grib2['label'] = "GRIB2"
        d_grib2['count'] = grib2
        d_other['label'] = "Other"
        d_other['count'] = other

        all_responses.append(d_ascii)
        all_responses.append(d_bin)
        all_responses.append(d_net)
        all_responses.append(d_hdf4)
        all_responses.append(d_hdf5)
        all_responses.append(d_hdfEos)
        all_responses.append(d_pp)
        all_responses.append(d_grads)
        all_responses.append(d_grib)
        all_responses.append(d_grib2)
        all_responses.append(d_other)

        all_responses = json.dumps(all_responses)
        return render_to_response('survey_results/dataFileFormat.html', {'free_resp': free_resp, 'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))

def otherTools(request):
    if request.user.is_authenticated():
        with open('statsPage/static/json/surveyJson.json') as json_data:
            surRes = json.load(json_data)
        ncl = matplotlib = ferret = grads = idl = visit = r = other = 0
        all_responses = []
        for sur in surRes:
            for each in sur['otherTools']:
                if each == 'ncl':
                    ncl += 1
                if each == 'matplotlib':
                    matplotlib += 1
                if each == 'ferret':
                    ferret += 1
                if each == 'grads':
                    grads += 1
                if each == 'idl':
                    idl += 1
                if each == 'visit':
                    visit += 1
                if each == 'r':
                    r += 1
                if each == 'otherTools':
                    other += 1

        d_ncl = {}
        d_matlib = {}
        d_fer = {}
        d_grads = {}
        d_idl = {}
        d_visit = {}
        d_r = {}
        d_other = {}

        d_ncl['label'] = "NCL"
        d_ncl['count'] = ncl
        d_matlib['label'] = "MatPlotLib"
        d_matlib['count'] = matplotlib
        d_fer['label'] = "Ferret"
        d_fer['count'] = ferret
        d_idl['label'] = "IDL"
        d_idl['count'] = idl
        d_grads['label'] = "GrADS"
        d_grads['count'] = grads
        d_visit['label'] = "VisIT"
        d_visit['count'] = visit
        d_r['label'] = "R"
        d_r['count'] = r
        d_other['label'] = "Other"
        d_other['count'] = other

        all_responses.append(d_ncl)
        all_responses.append(d_matlib)
        all_responses.append(d_fer)
        all_responses.append(d_idl)
        all_responses.append(d_grads)
        all_responses.append(d_visit)
        all_responses.append(d_r)
        all_responses.append(d_other)

        all_responses = json.dumps(all_responses)
        return render_to_response('survey_results/otherTools.html', {'all_responses': all_responses}, context_instance=RequestContext(request))
    else:
        return render_to_response('showlog.html', {}, context_instance = RequestContext(request))


def testing(request):
     return render_to_response('testing.html', {}, context_instance=RequestContext(request))

