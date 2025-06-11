'''
A module to contain helper functions to deal with raw data.
'''

import os, json, datetime, sqlitecloud
from cryptography.fernet import Fernet
from utils.responses import process_health_goals, process_health_goals_after, process_eq5d5l, process_cfs, process_must
from dotenv import load_dotenv
from functools import reduce

# Load in environment variables:
load_dotenv()

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
                            eq5d5l_columns = ['eq_anxiety', 'eq_mobility', 'eq_pain', 'eq_self_care', 'eq_usual'],
                            cfs_columns = ['cfs_terminally_ill', 'cfs_badls', 'cfs_iadls', 'cfs_chronic_conditions',
                                           'cfs_everything_effort', 'cfs_health_rating', 'cfs_moderate_activities'],
                            must_columns = ['must_bmi_score', 'must_weight_loss_percent_score', 'must_questions'],
                            goal_after_columns = ['met_goals', 'unmet_goals', 'unsure_goals']):
    '''
    Once the formsg responses have been processed by process_form_inputs, deal with the 
    responses themsselves.
    '''
    rest_of_data = {i : processed_forms.get(i) for i in processed_forms if i not in health_goal_columns + eq5d5l_columns + cfs_columns + must_columns}
    for question, response in rest_of_data.items():
        if ';' in response:
            rest_of_data[question] = ', '.join([i.split('-')[0].strip() for i in response.split(';')])
        elif '-' in response:
            rest_of_data[question] = response.split('-')[0].strip()       
    health_goals = {i : process_health_goals(processed_forms.get(i)) for i in health_goal_columns}
    eq5d5l_data = dict(zip(eq5d5l_columns, list(map(process_eq5d5l, [processed_forms.get(i) for i in eq5d5l_columns]))))
    cfs_data = process_cfs({i : processed_forms.get(i, '-') for i in cfs_columns}) 
    must_data = process_must({i : processed_forms.get(i, '-') for i in must_columns})
    print(health_goals)
    print('processing health goals now...')
    print({i : processed_forms.get(i, '-') for i in goal_after_columns})
    goal_data_after = process_health_goals_after({i : processed_forms.get(i, '-') for i in goal_after_columns})
    to_return = {**rest_of_data, **health_goals, **eq5d5l_data, **cfs_data, **must_data, **goal_data_after}
    to_return.update({'submission_date' : datetime.datetime.today().strftime('%Y-%m-%d')})
    return(to_return)

def return_dt_info(raw_info, fernet_key = os.getenv('FERNET_KEY')):
    '''
    Returns the de-encoded variation of a patient's distress thermometer information.
    '''
    decryptor, connection = Fernet(rf'{fernet_key}'), sqlitecloud.connect(os.getenv('DATABASE_CONNECTOR'))
    with open('./resources/mappings/dt_and_table_info.txt', 'rb') as file:
        mappings = json.loads(decryptor.decrypt(file.read()).decode('utf-8'))
    with open('./resources/mappings/database_tables.txt', 'rb') as file:
        tables = json.loads(decryptor.decrypt(file.read()).decode('utf-8'))
    cursor = connection.cursor()

    # Do the processing here:
    fetch_statement = f"SELECT {', '.join(mappings['dt']['dt_headers'])} FROM {tables['sprint, head and neck, obg (arm 3)']} WHERE"
    query, values = [], []
    for param, value in raw_info.items():
        if isinstance(value, list):
            query.append(f" {param} IN ({', '.join(['?'] * len(value))})")
            values.extend(value)
        elif isinstance(value, str):
            query.append(f" {param} = ?")
            values.append(value)
    fetch_statement = f"{fetch_statement} {' AND '.join(query)}"
    
    # Execute and fetch SQL and values here: (before returning, that is):
    cursor.execute(fetch_statement, tuple(values)) ; fetched_data = cursor.fetchall()
    fetched_data = list(map(lambda x : dict(zip(mappings['dt']['dt_headers'], x)), fetched_data))
    for result in fetched_data:
        for field in result:
            if field in mappings['dt']['dt_to_ignore'] or result[field] in ['-', None]:
                if result[field] in ['-', None]:
                    result[field] = '-'
                continue
            if result[field] in ['-', None]:
                result[field] = '-'
            else:
                result[field] = ', '.join([f"{i} - {mappings['dt']['mappings'][i.strip()]}" for i in result[field].split(',')])
    return(fetched_data)
    


# === Functions for checking daily responses (both private and public) ===

def _get_response_for_table(sql_command, values, arm_param, connector = os.getenv('DATABASE_CONNECTOR')):
    '''
    A private function meant to be used within check_daily_responses() - so that the latter function
    doesn't become bloated.  This function fetches all data for a date given a submission date and 
    returns dictionaries.
    '''
    connector = sqlitecloud.connect(connector) ; cursor = connector.cursor()
    cursor.execute(f"PRAGMA table_info({values[arm_param]})") ; values.pop(arm_param)
    column_names = [i[1] for i in cursor.fetchall()] ; cursor.close()
    cursor = connector.cursor() ; cursor.execute(sql_command, tuple(*values.values()))
    to_return = list(map(lambda x : dict(zip(column_names, x)), cursor.fetchall()))
    return(to_return)

def _check_missing_responses(arm_name, raw_data, fernet_key):
    '''
    A private function meant to be used within check_daily_responses() - so that the latter function
    doesn't become bloated.  This function - given a list of columns to check for - returns a list of 
    columns 
    '''
    decryptor, checked_responses = Fernet(rf'{fernet_key}'), []
    with open('./resources/mappings/dt_and_table_info.txt', 'rb') as file:
        mappings = json.loads(decryptor.decrypt(file.read()).decode('utf-8'))
    for patient in raw_data:
        if arm_name.endswith("1"):
            arm_to_match = 'arm_1_checks'
        elif arm_name.endswith("2"):
            arm_to_match = 'arm_2_checks'
        elif arm_name.endswith("3"):
            arm_to_match = 'arm_3_checks'
        missing_cols = list(map(lambda x : mappings['headers_to_check']['header_names'][x], mappings['headers_to_check']['cols_to_check'][arm_to_match]))
        missing_cols = reduce(lambda x, y : x + y, missing_cols)
        missing_cols = list(filter(lambda x : patient[x] in [None, '', '-'], missing_cols))
        if len(missing_cols):
            checked_responses.append({patient[mappings['headers_to_check']['name_param']] : [f'- {i}' for i in missing_cols]})
    return(checked_responses)


def check_daily_responses(raw_results, fernet_key = os.getenv('FERNET_KEY')):
    '''
    Checks for missing variables within a date's responses.
    '''
    decryptor, info_of_interest = Fernet(rf'{fernet_key}'), []
    with open('./resources/mappings/dt_and_table_info.txt', 'rb') as file:
        mappings = json.loads(decryptor.decrypt(file.read()).decode('utf-8'))
    for table_name in mappings['headers_to_check']['arm_names']:
        select_statement = F'SELECT * FROM {table_name} WHERE'
        params, values = [], {mappings['headers_to_check']['table_param'] : table_name}
        for param in raw_results:
            if len(raw_results[param]) > 1:
                params.append(f"{param} IN ({', '.join(['?'] * len(raw_results[param]))})")
                values[param] = raw_results[param]
            else:
                params.append(f'{param} = ?')
                values[param] = raw_results[param]
        select_statement = f"{select_statement} {' AND '.join(params)}"
        info_of_interest.extend(_get_response_for_table(select_statement, values, mappings['headers_to_check']['table_param']))
    to_return = {
        'arm_1' : [i for i in info_of_interest if '1' in i['patient_arm']],
        'arm_2' : [i for i in info_of_interest if '2' in i['patient_arm']],
        'arm_3' : [i for i in info_of_interest if '3' in i['patient_arm']]
    }
    print(info_of_interest)
    if sum(list(map(lambda x : len(to_return[x]), list(to_return.keys())))) > 0:
        to_return = {arm : _check_missing_responses(arm, data, fernet_key) for arm, data in to_return.items()}
    print(to_return)
    return(to_return)
    