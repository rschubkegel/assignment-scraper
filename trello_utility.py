import requests
import re
import json
import sys
import os.path
from datetime import date


def load_credentials(path='credentials.json'):
    '''
    Attempts to find credentials file in program args,
    if that fails it just searches in the local directory.
    Loads Trello API key/token from a file. Quits app if not successful.

    params:
    - path: the JSON file where Trello API key/token are stored

    returns:
    - a Python dictionary with Trello API key, token
    '''

    # try to get file path from arguments
    if len(sys.argv) > 1:
        pattern = re.compile(path)
        for arg in sys.argv[1:]:
            if pattern.search(arg):
                path = arg

    # try to load credentials from local JSON file
    if os.path.exists(path):
        try:
            f = open(path)
            data = json.load(f)
            key = data['key']
            token = data['token']
            print('Credentials loaded from {}'.format(path))
            return {'key': key, 'token': token}

        except Exception as e:
            print('Fatal error: '.format(e))
            sys.exit()

    # file did not exist
    else:
        print('Fatal error: file {} does not exist'.format(path))
        sys.exit()


def load_board_info(path='trello-info.json'):
    '''
    Attempts to find Trello info file in program args,
    if that fails it just searches in the local directory.
    Loads the board ID, lists on board, and labels on board from JSON file.
    If the file does not exist, program exits.

    params:
    - path: the JSON filename to load/store Trello information

    returns:
    - a tuple with trello board ID, trello lists
    '''

    # try to get file path from arguments
    if len(sys.argv) > 1:
        pattern = re.compile(path)
        for arg in sys.argv[1:]:
            if pattern.search(arg):
                path = arg

    # load data from file if it exists
    if os.path.exists(path):
        try:
            f = open(path)
            data = json.load(f)
            board_id = data['board-id']
            lists = data['lists']
            print('Trello info loaded from {}'.format(path))
            return (board_id, lists)

        # I/O error of some kind
        except Exception as e:
            print('Fatal error: '.format(e))
            sys.exit()

    # file did not exist
    else:
        print('Fatal error: file {} does not exist'.format(path))
        sys.exit()


def fetch_assignments(query, trello_lists):
    '''
    Returns a Python object of all the card in the specified lists.

    params:
    - query: a dictionary with Trello API key and token
    - trello_lists: a list of dictionaries (name, id) of Trello lists

    returns:
    - a Python object of all the card in a list
    '''
    
    url = 'https://api.trello.com/1/lists/{}/cards'

    cards_json = []
    for (name, id) in trello_lists.items():
        response = requests.request(
            'GET',
            url.format(id),
            params=query
        )
        cards_json.extend(json.loads(response.text))

    # convert to Python dictionaries for easy comparison
    cards_list = []
    for card in cards_json:
        card_dict = trello_card_to_dict(card)
        if card_dict:
            cards_list.append(card_dict)

    return cards_list


def trello_card_to_dict(card):
    '''
    Converts a Trello card (received from HTTPS request) to a Python dict.

    params:
    - card: the Trello card received from REST request

    returns:
    - Python dict with keys class, title, due, and description,
      or None if the Trello card didn't have all those fields
    '''

    # parse due date
    try:
        nums = re.findall(r'-\d\d', card['due'])
        new_month = int(nums[0][1:])
        new_day = int(nums[1][1:])

        # return dictionary
        return {
            'class': card['labels'][0]['name'],
            'title': card['name'],
            'due': (new_month, new_day),
            'description': card['desc']
        }

    # this Trello card didn't have a due date
    except Exception as error:
        return None


def get_trello_labels(query, board_id):
    '''
    Gets the labels on the Trello board specified in program constants.

    params:
    - query: a dictionary with Trello API key and token
    - board_id: the ID of the Trello board whose labels are being fetched

    returns:
    - a list of Trello labels (class names)
    '''

    labels_json = json.loads(requests.request(
        'GET',
        f'https://api.trello.com/1/boards/{board_id}/labels',
        params=query
    ).text)
    labels = {}
    for l in labels_json:
        labels[l['name']] = l['id']
    return labels


def filter_new_assignments(assignments, trello_cards):
    '''
    Compare assignments by *title* and add return the new ones.

    params:
    - assignments: a dict of assignments from the assignments page
    - trello_cards: a dict of assignments from Trello

    returns:
    - a dict of new assignments (name did not appear on Trello)
    '''

    new_assignments = []
    for a in assignments:
        is_new = True
        for card in trello_cards:
            if a['title'] == card['title']:
                is_new = False
                break
        if is_new:
            new_assignments.append(a)

    return new_assignments


def upload_assignments(query, assignments, board_id, list_id):
    '''
    Add dictionary of assignments to the specified Trello board.

    params:
    - query: a dictionary with Trello API key and token
    - assignments: a dictionary of new school assignments
    - board_id: the Trello board from which to get labels
    - list_id: the ID of the Trello list to add new assignments to

    returns:
    - None
    '''

    trello_labels = get_trello_labels(query, board_id)

    print('Adding {} new assignments to Trello'.format(len(assignments)))

    count = 0
    for a in assignments:

        # ignore assignment if class not listed in Trello labels
        if not a['class'] in trello_labels.keys():
            print('Error adding "{}": no Trello label "{}"'\
                .format(a['title'], a['class']))

        # go ahead and add assignment
        else:

            # format due date
            due = date(2021, a['due'][0], a['due'][1] + 1).isoformat()

            url = 'https://api.trello.com/1/cards?' \
                + 'idList={}&name={}&desc={}&due={}'\
                .format(list_id, a['title'], a['description'], due)

            # add the Trello card
            response = requests.request(
                'POST',
                url,
                params=query
            )
            print("Added {}".format(a['title']))

            # add label
            card_id = json.loads(response.text)['id']
            url = 'https://api.trello.com/1/cards/{}/idLabels?value={}'\
                .format(card_id, trello_labels[a['class']])
            requests.request(
                'POST',
                url,
                params=query
            )

            count += 1

    print('{} assignments added\n'.format(count))