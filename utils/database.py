'''
A module that contains functions for dealing with the remote SQLitecloud database.
'''

import sqlitecloud, os

def get_mapping_table():
    '''
    Given a question on one of the form.gov.sg forms, fetch the appropriate information from the
    right table 
    '''
    conn = sqlitecloud.connect(os.getenv('DATABASE_CONNECTOR')) 
    cursor = conn.cursor() ; cursor.execute(f'SELECT * FROM {os.getenv("MAPPING_TABLE")}')
    mapping_dictionary = dict(cursor.fetchall()) ; conn.close()
    return(mapping_dictionary)

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