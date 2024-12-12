'''
A Python helper file to store helper functions.
'''

from datetime import timedelta
from dateutil.parser import isoparse

def offset_datetime(timeset_object, second_offset = 1):
    '''
    Generates a datetime object in the form of form.gov.sg's 
    datetime object.  This will be used to fetch the data
    we want, and this is the time format this function will return: 
    2024-12-05T13:30:00.000+08:00
    '''
    new_timeset = isoparse(timeset_object) + timedelta(seconds = second_offset)
    new_timeset = new_timeset.isoformat() ; plus_index = new_timeset.index('+')
    return(new_timeset)
