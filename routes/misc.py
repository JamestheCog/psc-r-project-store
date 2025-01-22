'''
A helper Python file for containing miscellaneous routes for this proxy application
'''

from flask import Blueprint
misc = Blueprint('miscellaneous_routes', __name__)

@misc.route('/ping', methods = ['GET'])
def ping():
    '''
    Return the string "warm me up!" - meant to be used by a Chron job for keeping the application
    warm!
    '''
    return('warm me up!', 200)