from bs4 import BeautifulSoup
import requests
import re
import json
import sys
import os.path


def load_sites_info(path='site-info.json'):
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


def get_site_assignments(class_name, site_info):
    '''
    TODO
    '''

    print('Parsing assignments for {} from {}'.format(class_name, site_info['url']))

    response = requests.get(site_info['url'], headers=site_info['headers'])
    soup = BeautifulSoup(response.text, 'html.parser')
    new_assignments = []

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
            title = "Assignment {}".format(len(new_assignments) + 1)

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
            new_assignments.append({
                'class': class_name,
                # 'assigned': (assigned_month, assigned_day),
                'due': (due_month, due_day),
                'title': title,
                'description':description})

    return new_assignments


def get_assignments(sites_info):
    '''
    TODO
    '''

    # abort operation if no assignment pages found
    if len(sites_info.items()) == 0:
        print('No assignment pages found')
        sys.exit()

    assignments = []

    for (class_name, site_info) in sites_info.items():
        assignments.extend(get_site_assignments(class_name, site_info))

    return assignments
