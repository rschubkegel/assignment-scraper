from bs4 import BeautifulSoup
import requests
import re
import json
import sys
import os.path
from datetime import date


def main():
    '''
    Loads Trello API key/token, assignment page info,
    and Trello school board info from file.
    Pulls homework assignments from class pages and converts to Python dict.
    Grabs assignments from Trello and puts them in Python dict.
    Compares dictionaries to find new homework assignments
    and uploads them to Trello.

    params:
    - none

    returns:
    - none
    '''

    # load program data from files
    query = load_credentials()
    site_info = load_site_info()
    trello_board_id, trello_lists = load_trello_info()
    print()

    # only continue if there are assignment pages to check!
    if len(site_info.items()) == 0:
        print('No assignment pages found')
        sys.exit()

    # parse assignments from pages
    assignments = []
    for (k, v) in site_info.items():
        print('Parsing assignments for {} from {}'.format(k, v['url']))
        assignments.extend(parse_assignments(k, v))
    print()

    # fetch all cards from Trello
    print('Fetching cards from Trello board {}'.format(trello_board_id))
    cards = get_trello_cards(query, trello_lists)
    print()

    # compare most recent assignment on Trello to
    # most recent assignment from assignments pages
    new_assignments = get_new_assignments(assignments, cards)

    # upload assignments
    handle_new_assignments(
        query, trello_board_id, new_assignments, ask_to_add=True)


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


def load_site_info(path='site-info.json'):
    '''
    Attempts to find site info file in program args,
    if that fails it just searches in the local directory.
    Loads assignments page info from a file
    or quits the program if it fails.

    params:
    - path: the JSON file from which to load the assignments page info

    returns:
    - a python dict of site information
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
            print('Assignment page info loaded from {}'.format(path))
            return json.load(f)

        # I/O error of some kind
        except Exception as e:
            print('Fatal error: '.format(e))
            sys.exit()

    # file did not exist
    else:
        print('Fatal error: file {} does not exist'.format(path))
        sys.exit()


def load_trello_info(path='trello-info.json'):
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


def parse_assignments(class_name, site_info):
    '''
    Creates an HTTP request and parses the response into assignment attributes
    using beautifulsoup. Returns this as a list of dictionaries of attributes.

    params:
    - class_name: the name of the class these assignments are for
    - site_info: a dict of assignment page information

    returns:
    - a list of dictionaries of assignment attributes
    '''

    response = requests.get(site_info['url'], headers=site_info['headers'])
    soup = BeautifulSoup(response.text, 'html.parser')
    assignments = []

    for row in soup('tr'):

        cols = row('td')

        # assignments always have three columns
        # and assignements always have m/d date format
        if len(cols) == 3 and re.search(r'/', cols[0].string):

            # assignment due dates are always column 2/3
            due_text = re.sub(r"'", "", repr(cols[1].contents[0]))
            due = tuple(re.split(r'/', due_text))
            due_month = int(due[0])
            due_day = int(due[1])

            # <em> typically used for assignment titles,
            # but Hansen breaks this rule 😠 so assignment names
            # are the assignment number by default
            title = "Assignment {}".format(len(assignments) + 1)

            # if an em tag exists in col 3, then
            # its concent will be used as the title of the assignment
            em_tags = cols[2].find('em').find_all(text=True)
            if len(em_tags) > 0 and re.search(r'\A<td><em>', repr(cols[2])):
                title = em_tags[0].strip()
                title = re.sub(r'&', 'and', title)
                title = re.sub(r'\s+', ' ', title)

            # description tends to have extra spaces,
            # so I take those out
            description = ''
            for t in cols[2].find_all(text=True):

                # don't put the assignment tile in the description
                if t == em_tags[0]:
                    continue

                line = re.sub(r'\s+', ' ', t)
                if not title and re.search(r':', t):
                    title = line.strip()
                else:
                    description += line
            description = description.strip()

            # append assignment dictionary
            assignments.append({
                'class': class_name,
                # 'assigned': (assigned_month, assigned_day),
                'due': (due_month, due_day),
                'title': title,
                'description':description})

    return assignments


def get_trello_cards(query, trello_lists):
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
    for list in trello_lists:
        response = requests.request(
            'GET',
            url.format(list['id']),
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


def get_new_assignments(assignments, trello_cards):
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


def add_assignments_to_trello(query, assignments, board_id):
    '''
    Add dictionary of assignments to the specified Trello board.

    params:
    - query: a dictionary with Trello API key and token
    - assignments: a dictionary of new school assignments
    - board_id: the ID of the Trello board to add new assignments to

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
                .format(board_id, a['title'], a['description'], due)

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


def handle_new_assignments(query, board_id, new_assignments, ask_to_add=False):
    '''
    Prints out new assignments and (optionally) asks user if they should be
    added to Trello, then adds them to Trello.

    params:
    - query: a dictionary with Trello API key and token
    - board_id: the ID of the board to add new assignments to
    - new_assignments: assignments to be added to Trello
    - ask_to_add: automatically adds assignments to Trello if not set to True

    returns:
    - none
    '''

    if len(new_assignments) != 0:

        # print new assignments
        print('{} new assignments found:'.format(len(new_assignments)))
        print_assignments(new_assignments)

        # automatically add new assignments if param not set to true
        choice = 'y'
        if ask_to_add:
            # only add new assignments if user wants to
            choice = input('Would you like to add them to Trello (y/n)? ').lower()

        # add new assignments iff user entered y or yes
        if choice == 'y' or choice == 'yes':
            add_assignments_to_trello( \
                query, new_assignments, board_id)

    # there were no new assignments 🙌
    else:
        print('There are no new assignments')


def print_assignments(assignments):
    '''
    Prints each assignment's class title, assignment title, and due date.

    params:
    - assignments:

    returns:
    - none
    '''

    for a in assignments:
        print('Class:\t\t{}'.format(a['class']))
        print('Title:\t\t{}'.format(a['title']))
        print('Due date:\t{}/{}'.format(a['due'][0], a['due'][1]))
        print()


main()