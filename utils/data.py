'''
A module to contain helper functions to deal with raw data.
'''

def process_form_responses(form_responses, mapping_dictionary):
    '''
    Given a decrypted list of formsg responses and a dictionary of question-to-db column mappings,
    create a dictionary where the column ID is the key and the form response(s) itself the value.
    '''
    to_return = {}
    for i in form_responses:
        column_id = mapping_dictionary.get('question', '<unknown>')
        to_return[column_id] = '; '.join(i.get('answerArray', '-')) if 'answerArray' in i else i.get('answer', '-')
    return(to_return)