from bs4 import BeautifulSoup
import requests
import re
import json
import getpass
import sys
from datetime import date


SCHOOL_BOARD_ID = '7ARNAyc5'
TO_DO_LIST_ID = '5f60cc5ab8b90f19b7739b14'


def main():
    '''
    Loads a Trello key/token from file, arguments, or CL input.
    Pulls homework assignments from class pages and converts to Python dict.
    Grabs assignments from Trello via REST API and puts them in Python dict.
    Compares dictionaries to find new homework assignments
    and uploads them to Trello.

    params:
    - none

    returns:
    - none
    '''

    # if possible, load data from files provided in command-line arguments
    if len(sys.argv) > 1:
        if len(sys.argv) != 3:
            print('Fatal error: expected two arguments but got {}. Quitting...'\
                .format(len(sys.argv) - 1))
            sys.exit()
        else:
            key, token = get_credentials(sys.argv[1])
            site_info = get_site_info(sys.argv[2])

    # if no command-line arguments given, try to load default local files
    else:
        key, token = get_credentials()
        site_info = get_site_info()

    # only continue if there are assignment pages to check!
    if len(site_info.items()) == 0:
        print('No assignment pages found, quitting...')
        sys.exit()

    # parse assignments from pages
    print('Parsing all assignment pages:')
    assignments = []
    for (k, v) in site_info.items():
        print('Parsing assignments for {} from {}'.format(k, v['url']))
        assignments.extend(parse_assignments(k, v))

    print('Assignments parsed\n')

    # fetch all cards from Trello
    query = {
        'key': key,
        'token': token
    }
    list_ids = get_list_ids(query)
    cards = get_cards_in_lists(query, list_ids)

    # compare most recent assignment on Trello to
    # most recent assignment from assignments pages
    new_assignments = get_new_assignments(assignments, cards)

    # upload assignments
    handle_new_assignments(query, new_assignments, ask_to_add=True)


def get_credentials(path='credentials.json'):
    '''
    Tries to load Trello API key/token in a two ways:
    1) Load from a JSON file or
    2) Ask for key/token via command-line input.
    If both of these fail, the program will terminate.

    params:
    - path: the JSON file where Trello API key/token are stored

    returns:
    - a tuple with Trello API key, token
    '''

    key = None
    token = None

    # try to load credentials from local JSON file
    kt_entered = False
    try:
        f = open(path)
        data = json.load(f)
        key = data['key']
        token = data['token']
        kt_entered = True
        print('Credentials loaded from "credentials.json"\n')
    except Exception as error:
        print('No "credentials.json" file found. Enter Trello key/token:')

    # ask user for Trello key/token
    while not kt_entered:
        try:
            key = getpass.getpass(prompt='Key: ')
            token = getpass.getpass(prompt='Token: ')
        except Exception as error:
            print('ERROR', error)
            sys.exit()
        else:
            print()
            kt_entered = True

    return (key, token)


def get_site_info(path='site-info.json'):
    '''
    Tries to load assignments page info from a file
    or quits the program if it fails.

    params:
    - path: the JSON file from which to load the assignments page info

    returns:
    - a python dict of site information
    '''

    try:
        print('Loading assignment page info from "site-info.json"\n')
        f = open(path)
        return json.load(f)
    except Exception as error:
        print('Fatal error: no such file "site-info.json"')
        print('Quitting...')
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
            # print(repr(cols[2]))
            # sys.exit()
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


def get_list_ids(query):
    '''
    Returns a list of all Trello list ids in the School board.
    https://developer.atlassian.com/cloud/trello/rest/api-group-boards/#api-boards-id-lists-get

    params:
    - query: a dictionary with Trello API key and token

    returns:
    - a list of all Trello list ids in the School board
    '''

    url = 'https://api.trello.com/1/boards/{}/lists'.format(SCHOOL_BOARD_ID)

    response = requests.request(
        'GET',
        url,
        params=query
    )
    lists = json.loads(response.text)

    # print('Compiling Trello list ids:')
    ids = []
    for l in lists:
        ids.append(l['id'])
        # print(f'Added list id {ids[-1]}')
    # print('All Trello list ids compiled\n')

    return ids


def get_cards_in_lists(query, list_ids):
    '''
    Returns a Python object of all the card in a list.
    https://developer.atlassian.com/cloud/trello/rest/api-group-lists/#api-lists-id-cards-get

    params:
    - query: a dictionary with Trello API key and token
    - list_ids: a list of the ids of all the lists to retrieve cards from

    returns:
    - a Python object of all the card in a list
    '''
    
    url = 'https://api.trello.com/1/lists/{}/cards'

    print('Fetching all Trello cards:')
    cards_json = []
    for id in list_ids:
        response = requests.request(
            'GET',
            url.format(id),
            params=query
        )
        cards_json.extend(json.loads(response.text))
    print('All Trello cards fetched')

    print('Converting from JSON to Python list\n')
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


def get_to_do_id(query, list_ids):
    '''
    Gets the list ID of the 'To-Do' list on board or quits if it doesn't exist.

    params:
    - query: a dictionary with Trello API key and token
    - list_ids: a list of all Trello list IDs in 'School' board

    returns:
    - ID of the 'To-Do' list
    '''

    for id in list_ids:
        url = 'https://api.trello.com/1/lists/{}'.format(id)
        response = requests.request(
            'GET',
            url,
            params=query
        )
        if json.loads(response.text)['name'] == 'To-Do':
            return id
    print('Fatal error: "To-Do" list not found. Quitting...')
    sys.exit()


def get_trello_labels(query):
    '''
    Gets the labels on the Trello board specified in program constants.

    params:
    - query: a dictionary with Trello API key and token

    returns:
    - a list of Trello labels (class names)
    '''

    labels_json = json.loads(requests.request(
        'GET',
        f'https://api.trello.com/1/boards/{SCHOOL_BOARD_ID}/labels',
        params=query
    ).text)
    labels = {}
    for l in labels_json:
        labels[l['name']] = l['id']
    return labels


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

    trello_labels = get_trello_labels(query)

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


def handle_new_assignments(query, new_assignments, ask_to_add=False):
    '''
    Prints out new assignments and (optionally) asks user if they should be
    added to Trello, then adds them to Trello.

    params:
    - query: a dictionary with Trello API key and token
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
                query, new_assignments, TO_DO_LIST_ID)

    # there were no new assignments 🙌
    else:
        print('There are no new assignments')


main()