'''
This module handles the postback retuned as a result of generic messages sent
to the users.
'''

from config import execute_sql_query, check_if_user_in_db, send_message_to_user
from events import EventHandler

import json
from datetime import datetime
from time import time

from traceback import print_exc


class Postbacks:
    def __init__(self, u_id):
        self.user_id = u_id
        self.__initialise()

    def __initialise(self):
        '''
        Initialises the functions triggered on the postbacks recieved.
        '''
        self.su_postbacks = {
                            "sport_selection": self.__sport_selected,
                            "follow": self.__follow_game
                            }

    def execute_postback(self, field, result):
        return self.su_postbacks[field](result)

    def __create_generic_message(self, elements):
        message = {"attachment": {"type": "template", "payload": {}}}
        message['attachment']['payload'].update({"template_type": "generic"})
        message['attachment']['payload'].update({"elements": elements})
        return message

    def __sport_selected(self, result):
        '''
        This method recieves the postback returned at the time user selectes a
        sport preference. It updates the sport type in the database and returns
        back the app link message.
        '''
        obj = EventHandler(self.user_id)
        # updating the sport type in the database
        query = "UPDATE FBUsers SET sport='"+result+"' WHERE user_id="+str(self.user_id)
        execute_sql_query(query)

        # sending message to acknowledge back
        msg_both = "Now thats what I am talking about!"
        msg = msg_both if result=='both' else "A "+str(result).capitalize()+" Fan, Hmmmm!"
        send_message_to_user(self.user_id, {'text': msg})

        # sending the message back to notify the user
        msg = "I will make sure you are the FIRST to know all about whatever happens in "
        msg += 'sport' if result=='both' else result
        send_message_to_user(self.user_id, {'text': msg+' world! :)'})
        custom_msg = "Meanwhile check out this amazing thig...\n"
        return obj.app_command(custom_msg)

    def __update_followers_db(self, res):
        # creating the table if its not already created
        query = '''CREATE TABLE IF NOT EXISTS
                   Followers (
                     user_id bigint,
                     match_id varchar(40),
                     series_id varchar(40),
                     sport varchar(20),
                     matchdate varchar(20)
                    )'''
        execute_sql_query(query)

        # check if user is already in Followers table
        user = check_if_user_in_db(self.user_id, "Followers")
        game_date = str(datetime.fromtimestamp(res['epoch']).strftime("%Y-%m-%d"))
        if user:
            # check the date of the game user is following, if the date is
            # present date only, then notify the user for subscribing to the app
            # by sending the download app message
            present_date = user['matchdate']
            if game_date == present_date:
                send_message_to_user(self.user_id, {"text": "I am sorry mate but you can only follow 1 game in a day"})
                return False
            else:
                # updating the data for user
                query = "UPDATE FBUsers SET sport='"+res['sport']+"', match_id='"+res['match_id']+"', series_id='"+res['series_id']+"', matchdate='"+game_date+"' WHERE user_id="+str(self.user_id)
        else:
            # creating new entry for the user
            query = "INSERT INTO Followers (user_id, sport, match_id, series_id, matchdate)"
            query += " VALUES ("+str(self.user_id)+", '"+res['sport']+"', '"+res['match_id']+"', '"+res['series_id']+"', '"+str(game_date)+"')"

        execute_sql_query(query)
        return True

    def __follow_game(self, result):
        try:
            if self.__update_followers_db(result):
                text_msg = "game will begin at "
                text_msg += str(datetime.fromtimestamp(result['epoch']).strftime("%H:%M"))
                return {"text": text_msg+"\nStay Tuned ;)"}
            else:
                obj = EventHandler(self.user_id)
                return obj.app_command("To get all the matches and more, get surprised and check out this bad boy!")
        except Exception as e:
            print "Err in __follow_game :", str(e)
            print_exc()
            return {"text": "Stay Tuned.. ;)"}
