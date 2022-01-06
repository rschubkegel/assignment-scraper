from datetime import date, datetime
import gfu_utility as cs_scraper
import trello_utility as trello
import canvas_utility as canvas


def print_assignments(assignments):
    '''
    Prints each assignment's class title, assignment title, and due date.

    params:
    - assignments:

    returns:
    - none
    '''

    print()
    for a in assignments:
        due = datetime.fromisoformat(a['due'])
        print('Class:\t\t{}'.format(a['class']))
        print('Title:\t\t{}'.format(a['title']))
        print('Due date:\t{}/{}'.format(due.month, due.day))
        print()


def filter_new_assignments(old_assignments, new_assignments):
    '''
    Compare assignments by title and date and return the new ones.

    params:
    - old_assignments: a dict of assignments
    - new_assignments: a dict of assignments

    returns:
    - a dict of new assignments (new assignment name not in old assignments
      and due date is in the future)
    '''

    result = []
    for a_new in new_assignments:

        # only add upcoming assignments
        upcoming = a_new['due'] > date.today().isoformat()
        if upcoming:

            # only add assignments that aren't in old_assignments
            exclusive = True
            for a_old in old_assignments:
                if a_new['title'] == a_old['title']:
                    exclusive = False
                    break
            if exclusive:
                result.append(a_new)

    return result


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
    - True if new assignments were added, otherwise False
    '''

    assignments_added = False

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
            assignments_added = True

    # there were no new assignments 🙌
    else:
        print('There are no new assignments')

    return assignments_added


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
    query = trello.load_credentials()
    trello_board_id, trello_lists = trello.load_board_info()

    # get assignments
    trello_assignments = trello.get_assignments(query, trello_lists)
    cs_assignments = cs_scraper.get_assignments()
    canvas_assignments = canvas.get_assignments( \
        included_accounts=['Undergrad Programs'])

    # handle new Trello assignments
    added = handle_new_assignments(query, trello_board_id, trello_lists["To-Do"],
        filter_new_assignments(trello_assignments, cs_assignments),
        ask_to_add=True)

    # account for assignments that appear on CS sites *and* Canvas
    if added:
        trello_assignments.extend(cs_assignments)

    # handle new Canvas assignments
    handle_new_assignments(query, trello_board_id, trello_lists["To-Do"],
        filter_new_assignments(trello_assignments, canvas_assignments),
        ask_to_add=True)


if __name__ == '__main__':
    main()