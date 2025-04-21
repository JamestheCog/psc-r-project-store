'''
Routes for the Excel workbook to access the Proxy application.  
'''

from flask import Blueprint, request, jsonify
from cryptography.fernet import Fernet
import os, sqlitecloud, json
from utils.data import return_dt_info, check_daily_responses

# Define the blueprint here:
excel_routes = Blueprint('excel_routes', __name__)

@excel_routes.route('/fetch_data', methods = ['POST'])
def fetch_data():
    '''
    Given a POST request to this route, fetch data from the sqlitecloud database.
    '''
    try:
        data = request.get_json()
        if data.get('authorization') is None:
            return(jsonify({'message' : 'Missing authorization information', 'status' : 400}), 400)
        if data['authorization'].get('password') != os.getenv('PASSWORD'): 
            return(jsonify({'message' : 'Incorrect password given or missing password', 'status' : 405}), 405)
        if data['query'] is None:
            return(jsonify({'message' : 'missing query information', 'status' : 405}), 405)

        # Fetching data from SQLitecloud database via the proxy application:
        connection = sqlitecloud.connect(os.getenv('DATABASE_CONNECTOR')); cursor = connection.cursor()
        with open('./resources/mappings/fetch_params.txt', 'rb') as encrypted:
            decryptor = Fernet(rf"{os.getenv('FERNET_KEY')}")
            statement_helpers = json.loads(decryptor.decrypt(encrypted.read()).decode('utf-8'))
        table_name = data.get('query').get('arm') ; fetch_query = f'SELECT * FROM {table_name}'
        if '3' in data.get('query').get('arm'):
            fetch_query = f"{fetch_query} WHERE {statement_helpers['department_param']} = \"{statement_helpers['department_mappings'].get(data.get('query').get('department'))}\""
        cursor.execute(fetch_query) ; to_return = cursor.fetchall() ; cursor.close() ; cursor = connection.cursor()
        cursor.execute(f'PRAGMA table_info({table_name})') ; column_names = [i[1] for i in cursor.fetchall()] 
        connection.close()
        return(jsonify({'message' : 'Data fetching successful!', 'data' : [dict(zip(column_names, i)) for i in to_return]}), 200)
    except Exception as e:
        print(e)
        return(jsonify({'error_message' : str(e), 'status' : 500}), 500)

@excel_routes.route("/update_patients", methods = ['POST'])
def update_patients():
    '''
    Update the patients' information given their updated values in the JSON object - ensures a two-way sync between
    the Excel workbook and the database.
    '''
    try:
        data = request.get_json()
        if data.get('authorization') is None:
            return(jsonify({'message' : 'Missing authorization information', 'status' : 400}), 400)
        if data['authorization'].get('password') != os.getenv('PASSWORD'): 
            return(jsonify({'message' : 'Incorrect password given or missing password', 'status' : 405}), 405)
        if data.get('patients') is None:
            return(jsonify({'message' : 'Missing patient credentials to update information for', 'status' : 400}), 400)
        if data.get('study_settings') is None:
            return(jsonify({'message' : 'Missing study settings parameter', 'status' : 400}), 400)
        if data['study_settings'].get('arm') is None:
            return(jsonify({'message' : 'Missing study arm to update patients\' data for', 'status' : 400}), 400)
        
        # Do the updating here:
        conn = sqlitecloud.connect(os.getenv('DATABASE_CONNECTOR')) ; cursor = conn.cursor()
        with open('./resources/mappings/update_params.txt', 'rb') as encrypted:
            decryptor = Fernet(rf"{os.getenv('FERNET_KEY')}")
            constructor_helpers = json.loads(decryptor.decrypt(encrypted.read()).decode('utf-8'))
        for patient in data['patients']:
            data_of_interest = data['patients'][patient]
            for month_data in data_of_interest:
                if not len(data_of_interest[month_data]): 
                    continue
                set_statement = ', '.join([f'{i} = ?' for i in data_of_interest[month_data].keys()])
                where_statement = ' AND '.join([f'{i} = ?' for i in constructor_helpers['where_parameters'].values()])
                update_statement = f"UPDATE {data['study_settings']['arm']} SET {set_statement} WHERE {where_statement}"
                update_data = tuple(data_of_interest[month_data].values()) + (patient, month_data)
                cursor.execute(update_statement, update_data)
        return(jsonify({'message' : 'Successfully updated patients\' data!', 'status' : 200}))
    except Exception as e:
        print(e)
        return(jsonify({'error_message' : str(e), 'status' : 500}), 500)
    
@excel_routes.route('/delete_patient', methods = ['POST'])
def delete_patient():
    '''
    Given a patient's name, delete their information from the SQLitecloud database:
    '''
    try:
        data = request.get_json()
        if data.get('authorization') is None:
            return(jsonify({'message' : 'Missing authorization information', 'status' : 400}), 400)
        if data['authorization'].get('password') != os.getenv('PASSWORD'): 
            return(jsonify({'message' : 'Incorrect password given or missing password', 'status' : 405}), 405)
        if data.get('study_settings') is None or data['study_settings'].get('arm') is None:
            return(jsonify({'message' : 'Missing study settings arm and / or info.', 'status' : 405}), 405)
        if data.get('delete_parameters') is None:
            return(jsonify({'message' : 'Missing patient credentials to update information for', 'status' : 400}), 400)
        
        # Do the deletion here:
        conn = sqlitecloud.connect(os.getenv('DATABASE_CONNECTOR')) ; cursor = conn.cursor()
        delete_statement = f"DELETE FROM {data['study_settings'].get('arm')} WHERE " + ' AND '.join([f'{k} = "{v}"' for k, v in data['delete_parameters'].items()])
        cursor.execute(delete_statement)
        return(jsonify({'message' : 'A successful deletion!', 'code' : 200}), 200)
    except Exception as e:
        print(e)
        return(jsonify({'message' : 'something bad happened while deleting a record from the database...',
                        'error' : str(e), 'code' : 500}), 500)

@excel_routes.route('/fetch_with_sql', methods = ['post'])
def fetch_dt_information():
    '''
    Given a SQL statement to be executed, execute it, return the result, and process it accordingly:
    '''
    data = request.get_json()
    if data.get('authorization') is None:
        return(jsonify({'message' : 'Missing authorization information.', 'status' : 400}), 400)
    if data['authorization'].get('password') != os.getenv('PASSWORD'):
        return(jsonify({'message' : 'Incorrect or missing password.', 'status' : 400}), 400)
    if data.get('request') is None:
        return(jsonify({'message' : 'Missing query information.', 'status' : 400}), 400)
    if data['request'].get('sql_command_or_params') is None:
        return(jsonify({'message' : 'Missing SQL statement to be executed.', 'status' : 400}), 400)
    if data['request'].get('action') is None:
        return(jsonify({'message' : 'Missing action to do with fetched data.', 'status' : 400}), 400)
    
    if data['request']['action'] == 'get_dt_information':
        results = return_dt_info(data['request']['sql_command_or_params'])
    elif data['request']['action'] == 'get_daily_responses':
        results = check_daily_responses(data['request']['sql_command_or_params'])
    return(jsonify({'data' : results, 'message' : 'SQL command and action executed successfully!'}), 200)
    