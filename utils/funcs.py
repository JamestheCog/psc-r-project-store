'''
A Python helper file to store helper functions.
'''

from datetime import timedelta
from dateutil.parser import isoparse
import re

def offset_datetime(timeset_object, second_offset = 30):
    '''
    Generates a datetime object in the form of form.gov.sg's 
    datetime object.  This will be used to fetch the data
    we want, and this is the time format this function will return: 
    2024-12-05T13:30:00.000+08:00

    Update (Tuesday, 17th December, 2024):  We're not using this function for now, but I'll just leave this in for now 
                                            lest there's a need for this later on.
    '''
    new_timeset = isoparse(timeset_object) + timedelta(seconds = second_offset)
    new_timeset = new_timeset.isoformat() ; plus_index = new_timeset.index('+')
    return(new_timeset[:(plus_index - 3)] + new_timeset[plus_index:])


def convert_date(formsg_time):
    '''
    Given a time in the format of "2024-12-01T03:16:50.810+08:00", turn it into a number.
    I propose just removing all non-convertible characters for now.
    '''
    return(int(re.sub('(-|T|:|\\+|\\.)', '', formsg_time)))