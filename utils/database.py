'''
A module that contains functions for dealing with the remote SQLitecloud database.
'''

import os, json
from cryptography.fernet import Fernet

def determine_table_name(query_arm, fernet_key = os.getenv('FERNET_KEY')):
    '''
    Given an arm in the form of a number, return the appropriate 
    table name.
    '''
    query_arm, decryptor = query_arm.lower(), Fernet(rf'{fernet_key}')
    with open('./resources/mappings/database_tables.txt', 'rb') as encrypted:
        arm_name = json.loads(decryptor.decrypt(encrypted.read()).decode('utf-8'))
    return(arm_name.get(query_arm, '???'))