import requests, json


# NOTE: should use HTTP authorization header instead
ENDPOINT = 'https://georgefox.instructure.com/api/graphql?access_token={}'


def fetch_courses():

    result = None

    query = '''
        query GetCourses {
            allCourses {
                account {
                    name
                }
                name
                id
            }
        }
    '''

    print(f'Sending the following query to {ENDPOINT}:\n{query}')

    token = 'xxx'

    response = requests.post(
        ENDPOINT.format(token),
        json={'query': query}
    )

    if response.status_code != 200:
        print(f'Error {response.status_code}')
    else:
        result = json.loads(response.text)
        print(f'Received the following data:\n{json.dumps(result, indent=2)}')

    return result


fetch_courses()