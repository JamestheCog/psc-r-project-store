'''
A blueprint to contain routes for updating, fetching, and deleting data from the Tiles database
on Plumber.
'''

from flask import Blueprint, request, jsonify
import os, json, sqlitecloud
import formsg
from formsg.exceptions import WebhookAuthenticateException

# Then, import our user helpers here:
from utils.database import get_mapping_table, determine_table_name

# Define our blueprint and routes here; also load in the production version of formsg's SDK too:
api_routes = Blueprint('api_routes', __name__)
sdk = formsg.FormSdk('PRODUCTION')

# -- ROUTES FOR FETCHING AND UPLOADING DATA --
@api_routes.route('/fetch_data', methods = ['POST'])
def fetch_data():
    '''
    Given a POST request to this route, fetch data from the sqlitecloud database.
    '''
    try:
        data = request.get_json()
        if data['authorization'] is None:
            return(jsonify({'message' : 'Missing authorization information', 'status' : 400}), 400)
        if data['authorization']['password'] != os.getenv('FIRST_PASSWORD'): 
            return(jsonify({'message' : 'Incorrect password given or missing password', 'status' : 405}), 405)
        if data['query'] is None:
            return(jsonify({'message' : 'missing query information', 'status' : 405}), 405)
        if int(data['query']['arm']) not in range(1, 4):
            return(jsonify({'message' : '"arm" out of range', 'status' : 400}), 400)
        
        connection = sqlitecloud.connect(os.getenv('DATABASE_CONNECTOR'))
        cursor, table_name = connection.cursor(), determine_table_name(data.get('query').get('arm'))
        database_query = f"USE DATABASE {os.getenv('DATABASE_NAME')}" ; cursor.execute(database_query)
        fetch_query = f'SELECT * FROM {table_name}' ; cursor.execute(fetch_query) ; to_return = cursor.fetchall() ; cursor.close()
        cursor = connection.cursor()
        pragma_query = f'PRAGMA table_info({table_name})' ; cursor.execute(pragma_query) ; column_names = [i[1] for i in cursor.fetchall()] 
        connection.close()
        return(jsonify({'message' : 'Data fetching successful!', 'data' : [dict(zip(column_names, i)) for i in to_return]}), 200)
    except Exception as e:
        return(jsonify({'error_message' : str(e), 'status' : 500}), 500)

# -- Form.gov.sg uploads --
@api_routes.route('/main_form_uploads', methods = ['POST'])
def main_form_uploads():
    '''
    Try printing data using the SDK provided by formsg.  Use the test form first.
    '''
    try:
        posted_data, conn = json.loads(request.data), sqlitecloud.connect(os.getenv('DATABASE_CONNECTOR'))
        sdk.webhooks.authenticate(
            request.headers["X-FormSG-Signature"], 'https://psc-r-project-store-a3d7.onrender.com/main_form_uploads'
        )
        mapping_dictionary = get_mapping_table()
        decrypted = sdk.crypto.decrypt(os.getenv('INTERVIEW_FORMS_KEY'), posted_data['data'])
        decrypted = dict([(mapping_dictionary[i['question']], i.get('answer', '?')) for i in decrypted['responses'] if i['question'] in mapping_dictionary.keys()])
        
        # Upload the data here:
        cursor, table_name = conn.cursor(), determine_table_name(decrypted['arm'])
        cursor.execute(f"PRAGMA table_info({table_name})") ; table_columns = [i[1] for i in cursor.fetchall()]
        to_upload = '(' + ', '.join([decrypted.get(i, '?') for i in table_columns]) + ')'
        print(f"INSERT INTO {table_name} ({', '.join(table_columns)}) VALUES ({to_upload})")
        cursor.execute(f"INSERT INTO {table_name} ({', '.join(table_columns)}) VALUES ({to_upload})")
        conn.commit() ; conn.close()
        return(jsonify({'message' : 'The patient\'s data has been successfully uploaded!'}), 200)
    except WebhookAuthenticateException as e:
        return(jsonify({'message' : 'Bah!  Unauthorized request!'}, 401))
    except Exception as e:
        return(jsonify({'message' : 'Something bad happened...', 'error' : str(e)}), 500)

@api_routes.route('/update_patient', methods = ['POST'])
def update_patient():
    '''
    Given a list of patient particulars and their survey results, use them to update our patients'
    information and / or other pieces of information where necessary.
    '''
    try:
        data = request.get_json()
        if data['authorization'] is None:
            return(jsonify({'message' : 'Missing authorization information', 'status' : 400}), 400)
        if data['authorization']['password'] != os.getenv('FIRST_PASSWORD'): 
            return(jsonify({'message' : 'Incorrect password given or missing password', 'status' : 405}), 405)
        if data['patient'] is None:
            return(jsonify({'message' : 'Missing patient credentials to update information for', 'status' : 400}), 400)
        if data['to_update'] is None:
            return(jsonify({'message' : 'Missing information to update original patient information with', 
                            'status' : 400}), 400)
        
        # Do the data updating here:
        conn = sqlitecloud.connect(os.getenv('DATABASE_CONNECTOR'))
        cursor, table_name = conn.cursor(), determine_table_name(data['patient']['arm']) ; data['patient'].pop('arm')
        database_query = f"USE DATABASE {os.getenv('DATABASE_NAME')}" ; cursor.execute(database_query)
        database_update = ', '.join(list(map(lambda x : f"{x[0]} = '{x[1]}'", [(i[0], str(i[1]).replace("'", "''")) for i in data['to_update'].items()])))
        database_entry = ' AND '.join(list(map(lambda x : f"{x[0]} = '{x[1]}'", data['patient'].items())))
        update_query = f"UPDATE {table_name} SET {database_update} WHERE {database_entry}" 
        cursor.execute(update_query) ; conn.commit() ; conn.close()
        return(jsonify({'status' : 200, 'message' : 'data updated successfully!'}), 200)
    except (Exception, sqlitecloud.Error) as e:
        return(jsonify({'message' : 'something bad happened while updating the database...',
                        'error' : str(e), 'code' : 500}), 500)

## == NEW ROUTES (Tuesday, 7th January, 2024) ==

@api_routes.route('/delete_patient', methods = ['POST'])
def delete_patient():
    '''
    Given a patient's name, delete their information from the SQLitecloud database:
    '''
    try:
        data = request.get_json()
        if data['authorization'] is None:
            return(jsonify({'message' : 'Missing authorization information', 'status' : 400}), 400)
        if data['authorization']['password'] != os.getenv('FIRST_PASSWORD'): 
            return(jsonify({'message' : 'Incorrect password given or missing password', 'status' : 405}), 405)
        if data['patient'] is None:
            return(jsonify({'message' : 'Missing patient credentials to update information for', 'status' : 400}), 400)
        if data['to_update'] is None:
            return(jsonify({'message' : 'Missing information to update original patient information with', 
                            'status' : 400}), 400)
        
        # Do the deletion here:
        conn = sqlitecloud.connect(os.getenv('DATABASE_CONNECTOR'))
        cursor, table_name = conn.cursor(), determine_table_name(data['patient']['arm']) ; data['patient'].pop('arm')
        database_query = f"USE DATABASE {os.getenv('DATABASE_NAME')}" ; cursor.execute(database_query)
        delete_query = f'DELETE FROM {table_name} WHERE patient_name = "{data["patient"]["name"]}"'
        cursor.execute(delete_query) ; conn.commit() ; conn.close()
    except Exception as e:
        return(jsonify({'message' : 'something bad happened while deleting a record from the database...',
                        'error' : str(e), 'code' : 500}), 500)