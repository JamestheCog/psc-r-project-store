'''
A blueprint to contain routes for updating, fetching, and deleting data from the Tiles database
on Plumber.
'''

from flask import Blueprint, request, jsonify
import os, json, sqlitecloud
import formsg
from formsg.exceptions import WebhookAuthenticateException

# Then, import our user helpers here:
from utils.database import determine_table_name
from utils.data import process_form_inputs, process_respondent_data

# Define our blueprint and routes here; also load in the production version of formsg's SDK too:
api_routes = Blueprint('api_routes', __name__)
sdk = formsg.FormSdk('PRODUCTION')

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
        decrypted = sdk.crypto.decrypt(os.getenv('INTERVIEW_FORMS_KEY'), posted_data['data']) ; print(decrypted)
        decrypted = process_form_inputs(decrypted['responses']) ; print(decrypted)
        decrypted = process_respondent_data(decrypted) ; print(decrypted)
        
        # Upload the data here:
        cursor, table_name = conn.cursor(), determine_table_name(decrypted['patient_arm'])
        cursor.execute(f"PRAGMA table_info({table_name})") ; table_columns = [i[1] for i in cursor.fetchall()]
        to_upload = [j if len(str(j).strip()) else '-' for j in [decrypted.get(i, '') for i in table_columns]]
        cursor.execute(f"INSERT INTO {table_name} ({', '.join(table_columns)}) VALUES ({', '.join(['?'] * len(to_upload))})", to_upload)
        conn.commit() ; conn.close()
        return(jsonify({'message' : 'The patient\'s data has been successfully uploaded!'}), 200)
    except WebhookAuthenticateException as e:
        print(e)
        return(jsonify({'message' : 'Bah!  Unauthorized request!'}, 401))
    except Exception as e:
        print(e)
        return(jsonify({'message' : 'Something bad happened...', 'error' : str(e)}), 500)