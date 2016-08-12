from config import conn, execute_sql_query, send_message_to_user
from config import check_if_user_in_db, get_name_of_facebook_user
from events import EventHandler
from postbacks import Postbacks
from notifications import send_notifications

import tornado.httpserver
import tornado.ioloop
import tornado.web
import psycopg2
import psycopg2.extras

import os
import json

from traceback import print_exc


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello World")

    def post(self):
        self.write("Post method")


class FBHandler(tornado.web.RequestHandler):
    def get(self):
        # when the endpoint is registered as webhook in facebook
        # app settings, 'hub_challenge' value is returned in
        # the query parameters
        print 'verifying... '
        if self.get_argument("hub.mode") == "subscribe" and \
                self.get_argument("hub.challenge"):
            if self.get_argument("hub.verify_token") == 'whattheheckmanactualy':
                print 'Verified!!'
                self.write(self.get_argument("hub.challenge"))
            else:
                self.set_status(403)
                self.finish("Verify Token Mismatch")

    def post(self):
        try:
            # getting the url of the server
            self.server_url = ("%s://%s" %
                               (self.request.protocol,self.request.host,)
                                )
            # load the request data in json
            data = json.loads(self.request.body)
            # extracting user_id, app_id, and message text
            if data["object"] == "page":
                for entry in data["entry"]:
                    for messaging_event in entry["messaging"]:
                        # getting the id of the user
                        self.user_id = messaging_event["sender"]["id"]
                        try:
                            # if user has sent the message, excecute this
                            if messaging_event.get("message"):
                                message_text = messaging_event["message"]["text"]
                                self.process_message(message_text.lower())

                            # if user clicks on an option and a postback is returned
                            if messaging_event.get("postback"):
                                self.process_postback(messaging_event['postback']['payload'])
                        except Exception as e:
                            print " >> FB Handler Message Err :", str(e)
                            print_exc()
                            send_message_to_user(self.user_id, {"text": "Bot Error!!"})

            self.set_status(200)
            self.finish("ok")
        except Exception as e:
            print ' >>  Error in FBHandler post :', str(e)
            self.set_status(200)
            self.finish("error")

    def process_postback(self, payload):
        payload = json.loads(payload)
        obj = Postbacks(self.user_id)
        print payload
        send_message_to_user(self.user_id, obj.execute_postback(payload['type'], payload['result']))

    def process_message(self, message):
        # flag to indicate if user has messaged first time
        fresh_user = False

        # creating the table if its not already created
        query = '''CREATE TABLE IF NOT EXISTS
                   FBUsers (
                     user_id bigint PRIMARY KEY,
                     name varchar(40),
                     sport varchar(20),
                     active boolean
                    )'''
        execute_sql_query(query)

        # checking if record with user_id exists
        if not check_if_user_in_db(self.user_id):
            fresh_user = True
            # creating a new row in the database
            query = "INSERT INTO FBUsers (user_id, name, sport, active)"
            query += " VALUES ("+str(self.user_id)+", '', '', 'false')"
            execute_sql_query(query)

        # get the object of Event handler
        obj = EventHandler(self.user_id, self.server_url)

        if fresh_user:
            # if the user is engaging very first time, send an opening message
            send_message_to_user(self.user_id, opening_message(self.user_id))
        else:
            # get the user item from the database
            fbuser = check_if_user_in_db(self.user_id)

            # check if the name already exists in the database
            if not fbuser['name']:
                user_name = get_name_of_facebook_user(self.user_id)
                if message in ['yes', 'ya', 'yeah', 'yea', 'ok', 'alright', 'sure', 'yep']:
                    # this block runs when the user messages with positive
                    # response, i.e. any of the above mentioned replies

                    # update database
                    query = "UPDATE FBUsers SET name='"+user_name+"', active='true' WHERE user_id="+str(self.user_id)
                    execute_sql_query(query)
                    # send subscribe message to the user highlighting the sports
                    send_message_to_user(self.user_id, {"text": "Great :D"})
                    send_message_to_user(self.user_id, obj.subscribe_message())
                elif message in ['no', 'nope', 'na', 'nah']:
                    # this block runs in case user response is negetive
                    send_message_to_user(self.user_id, {"text": "Ummm okay! But, if you want to chat again, I am just a message away :)"})
                    query = "UPDATE FBUsers SET name='"+user_name+"' WHERE user_id="+str(self.user_id)
                    execute_sql_query(query)
                else:
                    swear_words = ['fuck', 'fuk', 'shit', 'gaand', 'gaandu']
                    # if user replies any of the above words

                    # check if any of the above word appears in the reply
                    for word in swear_words:
                        if word in message:
                            send_message_to_user(self.user_id, {"text": "Wowh!! Calm down bro"})
                            break
                    send_message_to_user(self.user_id, {'text':'Please be a good lad and reply as "Yes" or "No" ^_^'})
            else:
                # check if the user is active user of the bot
                if fbuser['active']:
                    # check if the message is command for bot to process
                    if message in obj.avaliable_commands():
                        send_message_to_user(self.user_id, obj.process_command(message))
                    else:
                        send_message_to_user(self.user_id, sorry_message())
                        send_message_to_user(self.user_id, obj.help_command())
                else:
                    # if the user has returned after unsubscribing
                    send_message_to_user(self.user_id, returned_user(self.user_id))


class NotificationHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("We're Good..")

    def post(self):
        '''
        This function is used by the Backend of sportsunity, that sends the
        highlights of the match with match_id, series_id and the sport type.
        '''
        try:
            data = self.request.arguments
            # creating the comment string from the post params
            comment = data['tt'][0]+'!\n'+ data['bt'][0]
            # getting match_id and series_id
            match_id = data['m'][0]
            series_id = data['l'][0]
            # getting sport type, 1: cricket 2: football
            sport = 'cricket' if data['s'][0]=='1' else 'football'
            send_notifications(sport, match_id, series_id, comment)
            # send_notifications('cricket', '30', '5212', comment) # for testing
            self.finish("ok")
        except Exception as e:
            print "Err in POST:NotificationHandler ;", str(e)
            self.finish("Error")


def opening_message(u_id):
    '''
    This message is sent only once, when the user messages very first time.
    '''
    # getting the name of the user
    name = get_name_of_facebook_user(u_id)
    text_part = "Hey "
    text_part += name if name else "there"
    text_part += "! I am here from SportsUnity, here to tell you about football"
    text_part += " and cricket. You interested..??"
    return {"text": text_part}


def sorry_message():
    text = "Sorry, dint understand you mate.Here's what I can help you with\n"
    return {'text': text}


def returned_user(u_id):
    '''
    This function is triggered when the user recently left (executed 'bye'cmd),
    and after that event messages again (at any point of time after leaving).
    '''
    text = "Hey you're back again :D \nSo lets talk sports, ready??? ;)"
    query = "UPDATE FBUsers SET name='' WHERE user_id="+str(u_id)
    execute_sql_query(query)
    return {'text': text}


def welcome_message():
    return {'text': 'Welcome to SportsUnity Page'}


def main():
    application = tornado.web.Application([
      (r"/", MainHandler),
      (r"/webhook", FBHandler),
      (r"/notify", NotificationHandler),
      (r"/images/(.*)", tornado.web.StaticFileHandler, {"path": "./images"})
    ], debug=True)
    http_server = tornado.httpserver.HTTPServer(application)
    port = 5000
    http_server.listen(port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
