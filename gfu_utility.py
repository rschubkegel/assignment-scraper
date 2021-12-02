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
            sys.exit(1)

    # file did not exist
    else:
        print('Fatal error: file {} does not exist'.format(path))
        sys.exit(1)


def _find_title(td):
    '''
    If the <td> tag contains <em> as its first child, then this function
    returns a string representation of the assignment title.
    Otherwise, it returns None.

    params:
    - td: a <td> tag corresponding to the assignment description
      for which a title is desired

    returns:
    - a string representation of the assignment title if <em> is first child,
      otherwise None
    '''

    result = None

    # if first tag within <td> is <em>
    if len(td.contents) > 0 and td.contents[0].name == 'em':
        result = list(td.em.stripped_strings)[0]
        result = re.sub(r'&', 'and', result)
        result = re.sub(r'\s+', ' ', result)

    return result


def _get_site_assignments(class_name, site_info):
    '''
    Parses the specified webpage for school assignments.
    The page must be formatted such that assignments are
    described in rows of an HTML table. Each table row must have
    the following attributes:

    - 3 columns: assigned date, due date, assignment description
    - dates in the format month/day

    If any table row does not have these attributes, it is assumed to be
    a legend or other description, not a school assignment.

    If the table row contents begins with an <em> tag,
    it is assumed to be the title of the assignment.
    Otherwise, the title is "Assignment #" where # is the current count
    of all assignments found on this page.

    params:
    - class_name: the name of this class
    - site_info: the information about this assignment page (see README)

    returns:
    - a list of dictionaries that hold the following keys:
      - class
      - due
      - title
      - description
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

            # if an <em> tag exists at beginning of table data contents,
            # use it for the assignment title, otherwise use "Assignment #"
            title = _find_title(cols[2])
            if not title:
                title = "Assignment {}".format(len(assignments) + 1)

            # remove <td> tags from description,
            # then convert to Markdown so formatting is preserved in Trello
            description = markdownify.markdownify(re.sub(r'<td>', '', repr(cols[2])))

            # append assignment dictionary
            assignments.append({
                'class': class_name,
                'due': (due_month, due_day),
                'title': title,
                'description':description})

    return assignments


def get_assignments(sites_info):
    '''
    Gets all assignments from all sites in site_info.

    params:
    - sites_info: a dictionary holding the class name as a key
      and other site info as a value (see README for specific contents)

    returns:
    - a list of dictionaries where each dictionary holds the info
      for a single school assignment
    '''

    # abort operation if no assignment pages found
    if len(sites_info.items()) == 0:
        print('No assignment pages found')
        sys.exit()

    # get assignments from every page
    assignments = []
    for (class_name, site_info) in sites_info.items():
        try:
            assignments.extend(_get_site_assignments(class_name, site_info))
        except Exception as e:
            print(f'Error parsing {class_name}')

    return assignments
