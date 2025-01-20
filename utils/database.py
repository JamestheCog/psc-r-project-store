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
    if query_arm == 3 or str(query_arm).lower() in ['obg', 'sprint', 'head and neck']:
        return(os.getenv('ARM_3_NAME'))
    elif query_arm == 2 or 'usual and palliative care' in str(query_arm).lower():
        return(os.getenv('ARM_2_NAME'))
    elif query_arm == 1 or 'usual care' in str(query_arm).lower():
        return(os.getenv('ARM_1_NAME'))
    return('<unknown>')