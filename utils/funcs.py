'''
A Python helper file to store helper functions.
'''

from datetime import timedelta
from dateutil.parser import isoparse
import re, os

# === NOT USED FOR NOW ===
#
# Tuesday, 17th December, 2024: these helpers were originally meant for when we were trying to use Tiles - the government alternative to 
#                               a third-party alternative like sqlitecloud.  

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

# === END ===

def determine_table_name(query_arm):
    '''
    Given an arm in the form of a number, return the appropriate 
    table name.
    '''
    converted_arm = query_arm.lower()
    if converted_arm.startswith('SPRinT'):
        return(os.getenv('ARM_3_NAME'))
    if 'palliative' in converted_arm:
        return(os.getenv('ARM_2_NAME'))
    if 'usual care' in converted_arm:
        return(os.getenv('ARM_1_NAME'))
    return('<unknown>')