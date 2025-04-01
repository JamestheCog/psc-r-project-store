'''
A module that contains helper functions to process raw questionnaire responses.  The functions here are generally
for encoding responses so far - no calculations or anything of that sort... yet!
'''

import json, os
from cryptography.fernet import Fernet

def process_eq5d5l(raw, fernet_key = os.environ.get('FERNET_KEY')):
    '''
    Maps a person's EQ5D5L response to a numeric grade as defined by the mapping dictionary. 
    '''
    decryptor, raw = Fernet(rf'{fernet_key}'), raw.lower()
    with open('./resources/mappings/eq5d5l_mappings.txt', 'rb') as file:
        mapping_dictionary = json.loads(decryptor.decrypt(file.read()).decode('utf-8'))
    for i in mapping_dictionary:
        is_inside = list(map(lambda x : raw.startswith(x), mapping_dictionary[i]))
        if sum(is_inside) > 0:
            return(i)
    return('-')

def process_health_goals(raw_goals, fernet_key = os.getenv('FERNET_KEY')):
    '''
    Given a patient's health goals, encode it.
    '''
    raw_goals, decryptor = list(map(lambda x : x.lower(), raw_goals)), Fernet(rf'{fernet_key}')
    with open('./resources/mappings/health_goals.txt', 'rb') as encrypted:
        health_goals = json.loads(decryptor.decrypt(encrypted.read()).decode('utf-8'))
    conversions = [health_goals.get(i, '') for i in raw_goals]
    return(', '.join(list(filter(lambda x : len(x.strip()) > 0, conversions))))

def process_cfs(cfs_responses, fernet_key = os.getenv('FERNET_KEY')):
    '''
    Process a patient's responses to the clinical frailty scale:
    '''
    input, decryptor = {k : v.lower().strip() for k, v in cfs_responses.items()}, Fernet(rf'{fernet_key}')
    with open('./resources/mappings/cfs_mappings.txt', 'rb') as encrypted:
        cfs_mappings = json.loads(decryptor.decrypt(encrypted.read()).decode('utf-8'))
    input = {k : cfs_mappings[k].get(v.split('-->')[0].strip(), '-') for k, v in input.items()}
    return(input)

def process_must(must_responses):
    '''
    Process some of the patient's responses to the MUST survey:
    '''
    input = {k : (v if len(v.strip()) else '-') for k, v in must_responses.items()}
    input = {k : v.lower().split('-->')[-1].strip()[-1] for k, v in input.items()}
    return(input)
