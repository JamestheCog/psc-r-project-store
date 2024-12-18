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
    try:
        data = request.get_json()
        if data['authorization'] is None:
            return(jsonify({'message' : 'Missing authorization information', 'status' : 400}), 400)
        if data['authorization']['password'] != os.getenv('PASSWORD'): 
            return(jsonify({'message' : 'Incorrect password given or missing password', 'status' : 405}), 405)
        if data['query'] is None:
            return(jsonify({'message' : 'missing query information', 'status' : 405}), 405)
        if int(data['query']['arm']) not in range(1, 4):
            return(jsonify({'message' : '"arm" out of range', 'status' : 400}), 400)
        
        connection = sqlitecloud.connect('%s/%s?apikey=%s' % (os.getenv('DATABASE_CONNECTOR'), os.getenv('DATABASE_NAME'), 
                                                              os.getenv('SQLITECLOUD_ADMIN_KEY')))
        cursor, table_name = connection.cursor(), determine_table_name(data.get('query').get('arm'))
        database_query = f"USE DATABASE {os.getenv('DATABASE_NAME')}" ; cursor.execute(database_query)
        fetch_query = f'SELECT * FROM {table_name}' ; cursor.execute(fetch_query) ; to_return = cursor.fetchall()
        pragma_query = f'PRAGMA table_info({table_name})' ; cursor.execute(pragma_query) ; column_names = [i[1] for i in cursor.fetchall()] 
        connection.close()
        return(jsonify({'message' : 'Data fetching successful!', 'data' : [dict(zip(column_names, i)) for i in to_return]}), 200)
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
        if data['authorization'] is None:
            return(jsonify({'message' : 'Missing authorization information', 'status' : 400}), 400)
        if data['authorization']['password'] != os.getenv('PASSWORD'): 
            return(jsonify({'message' : 'Incorrect password given or missing password', 'status' : 405}), 405)
        if data['query'] is None:
            return(jsonify({'message' : 'missing query information', 'status' : 405}), 405)
        if data['to_upload'] is None:
            return(jsonify({'message' : 'missing information to upload', 'status' : 405}), 405)
        if int(data['query']['arm']) not in range(1, 4):
            return(jsonify({'message' : '"arm" out of range', 'status' : 400}), 400)
        
        # Upload the data here:
        connection = sqlitecloud.connect('%s/%s?apikey=%s' % (os.getenv('DATABASE_CONNECTOR'), os.getenv('DATABASE_NAME'), 
                                                              os.getenv('SQLITECLOUD_ADMIN_KEY')))
        cursor, table_name = connection.cursor(), determine_table_name(data['query']['arm'])
        database_query = f"USE DATABASE {os.getenv('DATABASE_NAME')}" ; cursor.execute(database_query)
        pragma_query = f'PRAGMA table_info({table_name})' ; cursor.execute(pragma_query) ; column_names = [i[1] for i in cursor.fetchall()]
        insertion_query = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({', '.join(['?'] * len(column_names))})"
        cursor.execute(insertion_query, tuple([str(data['to_upload'][i]) for i in column_names]))
        print(tuple([data['to_upload'][i] for i in column_names])) ; connection.commit() ; connection.close()
        return(jsonify({'message' : 'data successfully uploaded onto the database!', 'code' : 200}), 200)
    except (Exception, sqlitecloud.Error) as e:
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
    
    # Do the data updating here:
    connection = sqlitecloud.connect('%s/%s?apikey=%s' % (os.getenv('DATABASE_CONNECTOR'), os.getenv('DATABASE_NAME'), 
                                                              os.getenv('SQLITECLOUD_ADMIN_KEY')))
    cursor = connection.cursor()
    return(jsonify({'status' : 200, 'message' : 'data updated successfully!'}), 200)
    