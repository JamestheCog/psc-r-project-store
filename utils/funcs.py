'''
A Python helper file to store helper functions.
'''

from datetime import timedelta
from dateutil.parser import isoparse

def offset_datetime(timeset_object, second_offset = 1):
    '''
    Generates a datetime object in the form of form.gov.sg's 
    datetime object.  This will be used to fetch the data
    we want:
    '''
    new_timeset = isoparse(timeset_object) + timedelta(seconds = second_offset)
    return(new_timeset.isoformat())
