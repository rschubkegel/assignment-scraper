from bs4 import BeautifulSoup
import requests
import re
import json
import sys
import os.path
import markdownify


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

    # grab HTML and make it into beautiful soup 🍲
    response = requests.get(site_info['url'], headers=site_info['headers'])
    soup = BeautifulSoup(response.text, 'html.parser')

    # store assignments found in HTML into list
    assignments = []
    for row in soup('tr'):

        # assignments always have three columns
        # and assignements always have m/d date format
        cols = row('td')
        if len(cols) == 3 and re.search(r'/', cols[0].string):

            # assignment due dates are always column 2/3
            due_text = re.sub(r"'", "", repr(cols[1].contents[0]))
            due = tuple(re.split(r'/', due_text))
            try:
                due_month = int(due[0])
                due_day = int(due[1])

            # if date parsing failed, this assignment has no due date listed
            # and should not be added to Trello
            # e.g. variable due date of final presentations from CSIS 420
            except Exception as _:
                continue

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

            # remove <td> tags from description,
            # then convert to Markdown so formatting is preserved in Trello
            description = markdownify.markdownify(re.sub(r'<td>', '', repr(cols[2])))

            # append assignment dictionary
            assignments.append({
                'class': class_name,
                # 'assigned': (assigned_month, assigned_day),
                'due': (due_month, due_day),
                'title': title,
                'description':description})

    return assignments


def get_assignments(sites_info):
    '''
    TODO
    '''

    # abort operation if no assignment pages found
    if len(sites_info.items()) == 0:
        print('No assignment pages found')
        sys.exit()

    # get assignments from every page
    assignments = []
    for (class_name, site_info) in sites_info.items():
        assignments.extend(get_site_assignments(class_name, site_info))

    return assignments
