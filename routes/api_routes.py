'''
A blueprint to contain routes for updating, fetching, and deleting data from the Tiles database
on Plumber.
'''

from flask import Blueprint, request, jsonify
import os, requests, json

# Then, import our user helpers here:
from utils.funcs import offset_datetime

# Define our blueprint and routes here:
api_routes = Blueprint('api_routes', __name__)

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
        if data.get('authorization') is None:
            return(jsonify({'message' : 'Missing authorization information', 'status' : 400}), 400)
        if data.get('authorization').get('password') != os.getenv('PASSWORD'): 
            return(jsonify({'message' : 'Incorrect password given or missing password', 'status' : 405}), 405)
        if data.get('query') is None:
            return(jsonify({'message' : 'missing query information', 'status' : 405}), 405)
        if int(data.get('query').get('arm')) not in range(1, 4):
            return(jsonify({'message' : '"arm" out of range', 'status' : 400}), 400)
        
        db_info, beginning_timestamp = [], '2024-12-05T13:30:00.000+08:00'
        while True:
            response = requests.post(os.getenv('GET_ROUTES'), headers = {'Content-Type' : 'application/json'},
                                    data = json.dumps({'authorization' : {'password' : os.getenv('PASSWORD')},
                                                        'query' : {'arm' : data.get('query').get('arm'),
                                                                'timestamp' : beginning_timestamp}}))
            if response.status_code != 200:
                return(jsonify({'message' : 'something happened on the server...', 'status' : 500}), 500)
            response = response.json()
            if response.get('rowFound') is not None and not response.get('rowFound'): 
                break
            db_info.append(response) ; beginning_timestamp = offset_datetime(response['timestamp'])
        return(jsonify({'result' : response, 'status' : 200}), 200)
    except Exception as e:
        return(jsonify({'result' : str(e), 'status' : 500}), 500)

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
    