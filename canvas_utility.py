# https://canvas.beta.instructure.com/doc/api/file.graphql.html
import requests, json, sys, re, os, markdownify
from datetime import datetime as dt


# NOTE: should use HTTP authorization header instead
ENDPOINT = 'https://georgefox.instructure.com/api/graphql?access_token={}'


def _load_credentials(path='credentials.json'):
    '''
    Attempts to find credentials file in program args,
    if that fails it just searches in the local directory.
    Loads Canvas API token from a file. Quits app if not successful.

    NOTE: function copied/pasted from trello_utility.py...
          should probably be abstracted into generic utility function

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
            token = data['canvas']['token']
            return {'token': token}

        except Exception as e:
            print('Fatal error loading Canvas credentials: '.format(e))
            sys.exit(1)

    # file did not exist
    else:
        print('Fatal error: file {} does not exist'.format(path))
        sys.exit(1)


def _send_query(query):
    '''
    Send requested query and returns JSON data
    or None if an error occurred.

    params:
    - query: the query to send to GraphQL API via POST request

    returns:
    - JSON response or None
    '''

    # expect bad response
    result = None

    # send query
    response = requests.post(
        ENDPOINT.format(_load_credentials()['token']),
        json={'query': query}
    )

    # result was good!
    if response.status_code == 200:
        result = json.loads(response.text)['data']

    return result


def get_assignments(included_accounts=None):
    '''
    Returns all school assignments for included accounts.
    If query returns error, prints error message and returns empty list.

    params:
    - included_accounts: list of course accounts;
      if None, all assignments are returned;
      otherwise, only returns assignments whose course account name
      is in include_accounts

    returns:
    - a chonky list of assignments or empty list if error occured
    '''

    print('Fetching assignments from Canvas')

    # declare return variable
    assignments = []

    # GraphQL query
    data = _send_query(
        '''
            query GetAssignment {
                allCourses {
                    name
                    courseCode
                    term {
                        endAt
                    }
                    account {
                        name
                    }
                    assignmentsConnection {
                        nodes {
                            dueAt
                            description
                            name
                            unlockAt
                        }
                    }
                }
            }
        '''
    )

    # errors cause no assignments to be returned
    if 'errors' in data.keys():
        for e in data['errors']:
            print(e['message'])
        return assignments

    # loop through all courses...
    today_iso = dt.now().isoformat()
    for course in data['allCourses']:

        # add class label for Trello usage;
        # if class has no course code, skip it
        code = re.search(r'\w{4} \d{3}', course['courseCode'])
        if code:
            code = code[0]
        else:
            # print('Error: no course code found for class {}'.format(course['name']))
            continue

        # only add courses whose term has not ended
        outdated = course['term']['endAt'] \
            and course['term']['endAt'] < today_iso

        # filter out courses whose account name are not specified
        excluded = included_accounts \
            and course['account']['name'] not in included_accounts

        if not outdated and not excluded:

            for a in course['assignmentsConnection']['nodes']:

                # parse date, skipping assignments w/o due dates
                # and skipping assignments that are still locked
                due = a['dueAt']
                if not due or \
                (a['unlockAt'] and a['unlockAt'] > today_iso):
                    continue

                # convert description from HTML to markdown
                if a['description']:
                    description = markdownify.markdownify(a['description']).strip()
                else:
                    description = ''

                assignments.append({
                    'class': code,
                    'due': due,
                    'title': a['name'],
                    'description': description}
                )

    return assignments


if __name__ == '__main__':
    data = get_assignments(included_accounts=['Undergrad Programs'])
    if data:
        print(f'Data received from Canvas:\n{json.dumps(data, indent=2)}')
    else:
        print('No data found ¯\_(ツ)_/¯')