'''
This program recives the POST request parameters sent to the /notify handler by
the SportsUnity backend. It matches the parmeters (match_id, sport, series_id),
and send the 'comment' parameter to all the users following the game represented
by the params.
'''

from config import conn, send_message_to_user


def get_followers_of_game(sport, match_id, series_id):
    '''
    Returns the list of users following game matching with sport, match_id,
    series_id.
    '''
    cursor = conn.cursor()
    query = "SELECT * FROM Followers WHERE sport='"+sport+"' OR sport='both' AND match_id='"+match_id+"' AND series_id='"+series_id+"'"
    cursor.execute(query)
    return cursor.fetchall()


def send_notifications(sport, match_id, series_id, comment):
    '''
    Send the comment to the users following the game matching with spoirt,
    match_id and series_id.
    '''
    # getting the followers list from the database
    users = get_followers_of_game(sport, match_id, series_id)
    for user in users:
        # sending comment (highlight) to each user one by one
        send_message_to_user(user[0], {"text": comment})
