'''
A blueprint to contain routes for updating, fetching, and deleting data from the Tiles database
on Plumber.
'''

from flask import Blueprint, request, jsonify
import os, requests, json, sqlitecloud

# Then, import our user helpers here:
from utils.funcs import determine_table_name

# Define our blueprint and routes here:
api_routes = Blueprint('api_routes', __name__)

# Define a global variable data row here - so that one can fetch the data:
shared_data = None

# -- ROUTES FOR FETCHING AND UPLOADING DATA --
@api_routes.route('/fetch_data', methods = ['POST'])
def fetch_data():
    '''
    Given a POST request to this route, fetch data from 
    the Tiles database, but only after validation:

    Note (Friday, 6th November, 2024):  apparently, there's no way to add an auto-incrementing counter 
                                        to Tiles or get form.gov.sg to do something like this.  I have 
                                        another idea - we'll use dates instead.  We'll set a pretty 
                                        early date - say the end of this year - before using it to 
                                        fetch the next item.  We'll increment the time by one second 
                                        until such time we end up with no more data (hence the infinite
                                        loop - it'll break out of the loop when there's no more data).

                                        I've gone ahead and chosen the timestamp 2024-12-05T13:30:00.000+08:00
                                        for now - basically the Thursday when I wrote this!
    '''
    global shared_data
    try:
        data = request.get_json()
        if data.get('authorization') is None:
            return(jsonify({'message' : 'Missing authorization information', 'status' : 400}), 400)
        if data.get('authorization').get('password') != os.getenv('PASSWORD'): 
            return(jsonify({'message' : 'Incorrect password given or missing password', 'status' : 405}), 405)
        if data.get('query') is None:
            return(jsonify({'message' : 'missing query information', 'status' : 405}), 405)
        if int(data.get('query').get('arm')) not in range(1, 4):
            return(jsonify({'message' : '"arm" out of range', 'status' : 400}), 400)
        
        connection = sqlitecloud.connect('%s/%s?apikey=%s' % (os.getenv('DATABASE_CONNECTOR'), os.getenv('DATABASE_NAME'), 
                                                              os.getenv('SQLITECLOUD_ADMIN_KEY')))
        cursor, table_name = connection.cursor(), determine_table_name(data.get('query').get('arm'))
        cursor.execute('USE DATABASE %s' % os.getenv('DATABASE_NAME'))
        cursor.execute('PRAGMA table_info(%s)' % table_name) ; table_columns = [i[1] for i in cursor.fetchall()]
        cursor.execute('SELECT * FROM %s' % table_name) ; patient_responses = cursor.fetchall()
        to_return = [dict(zip(table_columns, i)) for i in patient_responses]
        connection.close()
        return(jsonify({'message' : 'Data fetching successful!', 'data' : to_return}), 200)
    except Exception as e:
        return(jsonify({'error_message' : str(e), 'status' : 500}), 500)

@api_routes.route('/upload', methods = ['POST'])
def upload():
    '''
    Given a request from one of the publication arms, process its datetime before uploading
    it to the proper Tiles database
    '''
    try:
        data = request.get_json()
        print(data)
        if data.get('authorization') is None:
            return(jsonify({'message' : 'Missing authorization information', 'status' : 400}), 400)
        if data.get('authorization').get('password') != os.getenv('PASSWORD'): 
            return(jsonify({'message' : 'Incorrect password given or missing password', 'status' : 405}), 405)
        if data.get('query') is None:
            return(jsonify({'message' : 'missing query information', 'status' : 405}), 405)
        if data.get('to_upload') is None:
            return(jsonify({'message' : 'missing information to upload', 'status' : 405}), 405)
        if int(data.get('query').get('arm')) not in range(1, 4):
            return(jsonify({'message' : '"arm" out of range', 'status' : 400}), 400)
        
        # Upload the data here:
        connection = sqlitecloud.connect('%s/%s?apikey=%s' % (os.getenv('DATABASE_CONNECTOR'), os.getenv('DATABASE_NAME'), 
                                                              os.getenv('SQLITECLOUD_ADMIN_KEY')))
        table_name = determine_table_name(data.get('query').get('arm'))
        connection.execute('USE DATABASE %s' % os.getenv('DATABASE_NAME')) ; cursor = connection.cursor()
        cursor.execute('PRAGMA table_info(%s)' % table_name) ; column_names = [i[1] for i in cursor.fetchall()]
        cursor.execute('INSERT INTO %s %s VALUES %s' % (table_name, f"({', '.join(column_names)})", f"({', '.join(data['to_upload'])})"))
        connection.close()
        return(jsonify({'message' : 'data successfully uploaded onto the database!', 'code' : 200}), 200)
    except Exception as e:
        return(jsonify({'error_message' : str(e), 'status' : 500}), 500)

@api_routes.route('/update_patient', methods = ['POST'])
def update_patient():
    '''
    Given a list of patient particulars and their survey results, use them to update our patients'
    information and / or other pieces of information where necessary.  THIS FUNCTION IS NOT FINISHED YET!
    '''
    data = request.get_json()
    if data.get('authorization') is None:
        return(jsonify({'message' : 'Missing authorization information', 'status' : 400}), 400)
    if data.get('authorization').get('password') != os.getenv('PASSWORD'): 
        return(jsonify({'message' : 'Incorrect password given or missing password', 'status' : 405}), 405)
    if data.get('arm') not in range(1, 4):
        return(jsonify({'message' : '"arm" out of range', 'status' : 400}), 400)
    if data.get('patient') is None:
        return(jsonify({'message' : 'Missing patient credentials to update information for', 'status' : 400}), 400)
    if data.get('to_update') is None:
        return(jsonify({'message' : 'Missing information to update original patient information with', 
                        'status' : 400}), 400)
    return(jsonify({'status' : 200, 'message' : 'data updated successfully!'}), 200)
    