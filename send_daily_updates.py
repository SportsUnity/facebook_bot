'''
This file runs everyday between 9:00 AM to 3:00 PM. It gathers the games list
goin to happen on the present day and send users messages to follow the games
after checking the sport type user is following to.
'''

from config import conn, get_cards_from_mongodb, send_message_to_user
from time import time


def create_generic_message(elements):
    '''
    This function creates the generic message template.
    '''
    message = {"attachment": {"type": "template", "payload": {}}}
    message['attachment']['payload'].update({"template_type": "generic"})
    message['attachment']['payload'].update({"elements": elements})
    return message


def get_user_for_sport(sport):
    '''
    Returns the users who subscribed for 'sport' sport type.
    '''
    cursor = conn.cursor()
    query = "SELECT * FROM FBUsers WHERE sport='"+sport+"'"
    cursor.execute(query)
    return cursor.fetchall()


def notify_users(users, sport):
    '''
    This functions fetches data from mongodb for the present day games, and
    sends generic message to all the users subscribed for 'sport' sport type.
    '''
    filters = {}
    time_filter = {"epoch": {"$gt": int(time())}}

    if sport != 'both':
        filters = {"$and": [{"sport": sport}, time_filter]}

    if not filters:
        filters = time_filter

    matches = get_cards_from_mongodb(filters)
    if matches:
        all_elements = []
        for match in matches:
            all_elements.append(match['element'])
            message = create_generic_message(all_elements[:5])
            for user in users:
                send_message_to_user(user[0], {"text": "Check out the Games today!\n\nWhich One are we following then?? :D"})
                send_message_to_user(user[0], message)


if __name__ == '__main__':
    # all the sport types our bot is processing
    sport_types = ['cricket', 'football', 'both']
    for sport in sport_types:
        # get users of one sport type at a time
        users = get_user_for_sport(sport)
        if users:
            # notifying abt the matches to the users
            notify_users(users, sport)
