import scraper
import trello_utility as trello


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


def handle_new_assignments(query, board_id, list_id, new_assignments, ask_to_add=False):
    '''
    Prints out new assignments and (optionally) asks user if they should be
    added to Trello, then adds them to Trello.

    params:
    - query: a dictionary with Trello API key and token
    - board_id: the ID of board where new assignments will be added
    - list_id: the ID of the list to add new assignments to
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
            choice = input('Would you like to add them to Trello (y/n)? ') \
                .lower()

        # add new assignments iff user entered y or yes
        if choice == 'y' or choice == 'yes':
            trello.upload_assignments( \
                query, new_assignments, board_id, list_id)

    # there were no new assignments 🙌
    else:
        print('There are no new assignments')


def main():
    '''
    Loads program data from files,
    compares GFU site info to Trello assignments to find new assignments,
    upload new assignments to Trello (if user consents).

    params:
    - none

    returns:
    - none
    '''

    # load program data from files
    sites_info = scraper.load_sites_info()
    query = trello.load_credentials()
    trello_board_id, trello_lists = trello.load_board_info()

    # compare most recent assignment on Trello to
    # most recent assignment from GFU assignments pages
    new_assignments = trello.filter_new_assignments( \
        scraper.get_assignments(sites_info), \
        trello.fetch_assignments(query, trello_lists))

    # upload assignments
    handle_new_assignments(query, trello_board_id, trello_lists["To-Do"],
        new_assignments, ask_to_add=True)


main()