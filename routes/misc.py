'''
A helper Python file for containing miscellaneous routes for this proxy application
'''

from flask import Blueprint
miscellaneous_routes = Blueprint('miscellaneous_routes', __name__)

@miscellaneous_routes.route('/ping', methods = ['GET'])
def ping():
    '''
    Return the string "pong" - meant to be used by a Chron job for keeping the application
    warm!
    '''
    return('pong', 200)
