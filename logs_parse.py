#!/usr/bin/env python
import re, datetime
import time
import sys

WARN_TYPES = {'INFO':0,'WARN':1,'WARNING':1,'ERROR':2}
TYPE_TEXT = {0:'INFO',1:'WARNING',2:'ERROR'}

LOGS_PATERN  = \
    r'\s*(?P<datetime>(?P<day>\d\d)\.(?P<month>\d\d)\.(?P<year>\d{2,4})\s+' \
    r'(?P<hour>\d\d):(?P<min>\d\d):(?P<sec>\d\d)\.(?P<mic>\d{3,3}))' \
    r'\s+\[(?P<type>\w+)\]\s*\t\s*(?P<message>.+?)\s*\t\s*' \
    r'(?:(?P<path>.*)\s+)?' \
    r'(?P<num_line>\d+)\s+'

LOGS_REGEXP = re.compile(LOGS_PATERN, re.I| re.U)

CHUNK = 4096*6

class Log(object):
    __slots__ = ('datetime','type_mes','message','path','num_line', \
                'datetime_str', 'type_text')
    def __init__(self, datetime=None, type_mes=None,
                 message=None,path=None, num_line = None):
        self.datetime, self.type_mes = datetime, type_mes  
        self.message, self.path, self.num_line = message, path, num_line
    
    @property
    def datetime_str(self):
        return str(self.datetime)
    
    @property
    def type_text(self):
        return TYPE_TEXT.get(self.type_mes,'INFO')
        

def toint(x,y=None):
    try:
        return int(x)
    except ValueError:
        return y
        

def get_from_dict_or(mydict, key, default):
    return toint(mydict.get(key,default),default)

def dict_to_logs_object(mydict):
    mydate = datetime.datetime(year = get_from_dict_or(mydict,'year',0),
                               month = get_from_dict_or(mydict,'month',0),
                               day = get_from_dict_or(mydict,'day',0),
                               hour = get_from_dict_or(mydict,'hour',0),
                               minute = get_from_dict_or(mydict,'min',0),
                               second = get_from_dict_or(mydict,'sec',0))
    
    mytype = WARN_TYPES.get(mydict.get('type','INFO'),0)
    return Log(datetime = mydate, type_mes = mytype, 
               message = mydict.get('message',''),
               path = mydict.get('path',''),
               num_line = get_from_dict_or(mydict,'num_line',0))
    
#Closures for filter
def closure_filter_by_date(startdate, enddate):
    filter_by_date = lambda x: x.datetime<=startdate and \
        x.datetime>=enddate and True
    return filter_by_date

def closure_filter_by_type(types):
    filter_by_type = lambda x: x.type_mes in types and True
    return filter_by_type

def closure_filter_by_message(message):
    filter_by_message = lambda x: x.message.find(message)!=-1 and True
    return filter_by_message

def closure_filter(startdate=None, enddate=None, types=None, message=None):
    filter_funs = []
    if enddate:
        filter_funs.append(closure_filter_by_date( \
            startdate or datetime.datetime.now(), enddate))
    if types:
        filter_funs.append(closure_filter_by_type(types))
    if message:
        filter_funs.append(closure_filter_by_message(message))
    
    if not filter_funs:
        return None
    
    def filter_logs(obj):
        if False in [ i(obj) for i in filter_funs]:
            return False
        else:
            return True
    
    return filter_logs

def read_log(log_name):
    mfile = open(log_name,'rb',0)
    text = mfile.read(CHUNK).decode('cp1251')
    text_start = 0
    text_start_old = 0
    old_part_text = ''
    while text:
        res = LOGS_REGEXP.match(text, text_start)
        if res:
            text_start = res.end()
            yield dict_to_logs_object(res.groupdict())
            del res
        else:
            text_start_old = text_start
            text_start = text.find('\n',text_start + 1) + 1
            if text_start == 0:
                old_part_text = text[text_start_old:]
                text =  mfile.read(CHUNK).decode('cp1251')
                if text:
                    text = old_part_text + text
                text_start = 0
    mfile.close()
    del text
    del mfile
    

def logs_obj_filter(log_obj, *args, **kwargs):
    myfilter = closure_filter(*args, **kwargs)
    for i in logs_obj:
        if myfilter(i):
            yield i
    del myfilter
    
def read_logs_filter(log_name, *args, **kwargs):
    return logs_obj_filter(read_log(log_name), *args, **kwargs)
            
