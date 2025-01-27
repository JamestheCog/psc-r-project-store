'''
Routes for the Excel workbook to access the Proxy application.  
'''

from flask import Blueprint, request, jsonify
import os, sqlitecloud

# Then, import our user helpers here:
from utils.database import determine_table_name

# Define the blueprint here:
excel_routes = Blueprint('excel_routes', __name__)

@excel_routes.route('/fetch_data', methods = ['POST'])
def fetch_data():
    '''
    Given a POST request to this route, fetch data from the sqlitecloud database.
    '''
    try:
        data = request.get_json()
        if data['authorization'] is None:
            return(jsonify({'message' : 'Missing authorization information', 'status' : 400}), 400)
        if data['authorization']['password'] != os.getenv('PASSWORD'): 
            return(jsonify({'message' : 'Incorrect password given or missing password', 'status' : 405}), 405)
        if data['query'] is None:
            return(jsonify({'message' : 'missing query information', 'status' : 405}), 405)
        if data['query']['arm'] not in range(1, 4):
            return(jsonify({'message' : '"arm" out of range', 'status' : 400}), 400)
        
        connection = sqlitecloud.connect(os.getenv('DATABASE_CONNECTOR'))
        cursor, table_name = connection.cursor(), determine_table_name(data.get('query').get('arm'))
        fetch_query = f'SELECT * FROM {table_name}' 
        fetch_query = fetch_query if data.get('query').get('arm') < 3 else f"{fetch_query} WHERE nccs_department = \"{data.get('query').get('department')}\""
        cursor.execute(fetch_query) ; to_return = cursor.fetchall() ; cursor.close() ; cursor = connection.cursor()
        pragma_query = f'PRAGMA table_info({table_name})' ; cursor.execute(pragma_query) ; column_names = [i[1] for i in cursor.fetchall()] 
        connection.close()
        return(jsonify({'message' : 'Data fetching successful!', 'data' : [dict(zip(column_names, i)) for i in to_return]}), 200)
    except Exception as e:
        return(jsonify({'error_message' : str(e), 'status' : 500}), 500)

@excel_routes.route('/fetch_caregiver_data', methods = ['POST'])
def fetch_caregiver_data():
    '''
    Given a patient's name, find caregiver-related information (if there's any) for the patient in question given their 
    name.
    '''
    try:
        data, conn = request.get_json(), sqlitecloud.connect(os.getenv('DATABASE_CONNECTOR'))
        if data['authorization'] is None:
            return(jsonify({'message' : 'Missing authorization information', 'status' : 400}), 400)
        if data['authorization']['password'] != os.getenv('PASSWORD'): 
            return(jsonify({'message' : 'Incorrect password given or missing password', 'status' : 405}), 405)
        if data['query'] is None:
            return(jsonify({'message' : 'missing query information', 'status' : 405}), 405)
        cursor, query = conn.cursor(), '%s = "%s"' % list(data['query'].items())[0]
        cursor.execute(f"PRAGMA table_info({os.getenv('CAREGIVER_TABLE')})") ; columns = [i[1] for i in cursor.fetchall()]
        cursor.close() ; cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {os.getenv('CAREGIVER_TABLE')} WHERE {query}") ; to_return = cursor.fetchall()
        to_return = ['-'] * len(columns) if len(to_return) == 0 else to_return[0]
        to_return = dict(zip(columns, to_return)) ; conn.close()
        return(jsonify({'message' : 'Data successfully fetched!', 'code' : 200, 'data' : to_return}), 200)
    except (sqlitecloud.Error, Exception) as e:
        return(jsonify({'Something bad happened...' : str(e), 'status' : 500}), 500)

# === Routes for updating and deleting data ===
@excel_routes.route('/update_patient', methods = ['POST'])
def update_patient():
    '''
    Given a list of patient particulars and their survey results, use them to update our patients'
    information and / or other pieces of information where necessary.
    '''
    try:
        data = request.get_json()
        if data['authorization'] is None:
            return(jsonify({'message' : 'Missing authorization information', 'status' : 400}), 400)
        if data['authorization']['password'] != os.getenv('PASSWORD'): 
            return(jsonify({'message' : 'Incorrect password given or missing password', 'status' : 405}), 405)
        if data['patient'] is None:
            return(jsonify({'message' : 'Missing patient credentials to update information for', 'status' : 400}), 400)
        if data['to_update'] is None:
            return(jsonify({'message' : 'Missing information to update original patient information with', 
                            'status' : 400}), 400)
        # Do the data updating here:
        conn = sqlitecloud.connect(os.getenv('DATABASE_CONNECTOR'))
        cursor, table_name = conn.cursor(), determine_table_name(data['patient']['arm'])
        if table_name != os.getenv('ARM_3_NAME'): 
            data['patient'].pop('arm')
        else:
            data['patient']['nccs_department'] = data['patient'].pop('arm')
        if len(data['to_update']):
            database_update = ', '.join(list(map(lambda x : f"{x[0]} = '{x[1]}'", [(i[0], str(i[1]).replace("'", "''")) for i in data['to_update'].items()])))
            database_entry = ' AND '.join(list(map(lambda x : f"{x[0]} = '{x[1]}'", list(data['patient'].items())[:2])))
            update_query = f"UPDATE {table_name} SET {database_update} WHERE {database_entry}" ; print(update_query)
            cursor.execute(update_query) ; conn.commit() ; conn.close()
        return(jsonify({'status' : 200, 'message' : 'data updated successfully!'}), 200)
    except (Exception, sqlitecloud.Error) as e:
        return(jsonify({'message' : 'something bad happened while updating the database...',
                        'error' : str(e), 'code' : 500}), 500)

@excel_routes.route('/delete_patient', methods = ['POST'])
def delete_patient():
    '''
    Given a patient's name, delete their information from the SQLitecloud database:
    '''
    try:
        data = request.get_json()
        if data['authorization'] is None:
            return(jsonify({'message' : 'Missing authorization information', 'status' : 400}), 400)
        if data['authorization']['password'] != os.getenv('PASSWORD'): 
            return(jsonify({'message' : 'Incorrect password given or missing password', 'status' : 405}), 405)
        if data['patient'] is None:
            return(jsonify({'message' : 'Missing patient credentials to update information for', 'status' : 400}), 400)
        
        # Do the deletion here:
        conn = sqlitecloud.connect(os.getenv('DATABASE_CONNECTOR')) ; cursor = conn.cursor()
        patient_info = {k : str(v).strip() for k, v in data['patient'].items()} ; table_name = determine_table_name(data['patient']['arm'])
        delete_query = f"DELETE FROM {table_name} WHERE (patient_name = \"{patient_info.get('patient_name', 'unknown')}\" OR patient_id = \"{patient_info.get('patient_id', 'unknown')}\")"
        delete_query = delete_query if table_name == os.getenv("ARM_3_PATIENTS") else delete_query + f" AND nccs_department = \"{data['patient']['arm']}\""
        cursor.execute(delete_query) ; conn.commit() ; conn.close()
        return(jsonify({'message' : f'patient "{patient_info["patient_name"]}" successfully deleted!', 'code' : 200}), 200)
    except Exception as e:
        return(jsonify({'message' : 'something bad happened while deleting a record from the database...',
                        'error' : str(e), 'code' : 500}), 500)