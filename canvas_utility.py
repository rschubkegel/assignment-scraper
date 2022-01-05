import requests, json, sys, re, os


# NOTE: should use HTTP authorization header instead
ENDPOINT = 'https://georgefox.instructure.com/api/graphql?access_token={}'


def load_credentials(path='credentials.json'):
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
            print('Fatal error: '.format(e))
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
        ENDPOINT.format(load_credentials()['token']),
        json={'query': query}
    )

    # result was good!
    if response.status_code == 200:
        result = json.loads(response.text)

    return result


def fetch_courses():
    '''
    Returns JSON data in the following format:

    course [
        name: str
        id: str
        account [
            name: str
        ]
    ]

    params:
    - none

    returns:
    - none
    '''

    return _send_query(
        '''
            query GetCourses {
                allCourses {
                    name
                    id
                    account {
                        name
                    }
                }
            }
        '''
    )


if __name__ == '__main__':
    data = fetch_courses()
    if data:
        print(f'Data received from Canvas:\n{json.dumps(data, indent=2)}')
    else:
        print('Something went wrong ¯\_(ツ)_/¯')