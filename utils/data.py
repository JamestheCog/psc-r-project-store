'''
A module to contain helper functions to deal with raw data.
'''

import os, json, datetime
from cryptography.fernet import Fernet
from utils.responses import process_health_goals, process_eq5d5l

def process_form_inputs(form_responses, fernet_key = os.getenv('FERNET_KEY')):
    '''
    Given a decrypted list of formsg responses and a dictionary of question-to-db column mappings,
    create a dictionary where the column ID is the key and the form response(s) itself the value.
    '''
    to_return, decryptor = {}, Fernet(fernet_key)
    with open('./resources/mappings/question_mappings.txt', 'rb') as file:
        mapping = json.loads(decryptor.decrypt(file.read()).decode('utf-8'))
    for i in form_responses:
        column_id = mapping.get(i['question'].lower(), '<unknown>')
        to_return[column_id] = '; '.join(i.get('answerArray', '-')) if 'answerArray' in i else i.get('answer', '-')
    return(to_return)

def process_respondent_data(processed_forms, 
                            health_goal_columns = ['health_goals'],
                            eq5d5l_columns = ['eq_anxiety', 'eq_mobility', 'eq_pain', 'eq_self_care', 'eq_usual']):
    '''
    Once the formsg responses have been processed by process_form_inputs, deal with the 
    responses themsselves.
    '''
    rest_of_data = {i : processed_forms.get(i) for i in processed_forms if i not in health_goal_columns + eq5d5l_columns}
    for question, response in rest_of_data.items():
        if ';' in response:
            rest_of_data[question] = ', '.join([i.split('-')[0].strip() for i in response.split(';')])
        elif '-' in response:
            rest_of_data[question] = response.split('-')[0].strip()       
    health_goals = {i : process_health_goals(processed_forms.get(i)) for i in health_goal_columns}
    eq5d5l_data = dict(zip(eq5d5l_columns, list(map(process_eq5d5l, eq5d5l_columns))))
    to_return = {**rest_of_data, **health_goals, **eq5d5l_data}
    to_return.update({'submission_date' : datetime.today().strftime('%Y-%m-%d')})
    return(to_return)