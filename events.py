from cards import SportsCards
from config import check_if_user_in_db, send_message_to_user, blog_news_link
from config import get_cards_from_mongodb
from config import execute_sql_query, news_api_link

import json
import requests
import random

from time import time


class EventHandler:
    def __init__(self, u_id, server_url=""):
        '''
        Args:
            u_id : facebook user id of the user
            server_url: hostname of the server; this param is nedded to create
                        the url of the images that are generated in the program
        '''
        self.user_id = u_id
        self.server_url = server_url
        self.__initialise()

    def __initialise(self):
        '''
        Initialises the dictionary for 'commands' that the bot functions upon.
        Each command entry in the dict contains the respective function it
        directs to when user enters the command, and the doc string to display
        in the Help message to the user.
        '''
        self.su_commands = {'news':
                            {'doc': 'get latest news update',
                             'func': self.news_command
                             },
                            'app':
                            {'doc': 'get SportsUnity App link',
                             'func': self.app_command
                             },
                            'bye':
                            {'doc': "I'll leave you alone!",
                             'func': self.bye_command
                             },
                            'sport':
                            {'doc': 'change your sport preference',
                             'func': self.sport_command
                             },
                            'games':
                            {'doc': "see what's happening today",
                             'func': self.games_command
                             },
                            'help':
                            {'doc': 'this message'}
                            }

    def user_subscription(self):
        # check if the user is already subscribed to any Sport
        u_sport = check_if_user_in_db(self.user_id)['sport']
        u_sport = 'Cricket and Football' if u_sport == 'both' else u_sport
        if u_sport == 'None':
            # if No, then send the subscribe message back
            return self.subscribe_message()
        else:
            # if subscribed then send notification and change subscription msg
            message_text = "You are currently subscribed to "+u_sport
            send_message_to_user(self.user_id, {"text": message_text})
            return self.__change_subscription_message()

    def __create_generic_message(self, elements):
        '''
        Fills in the elements (buttons, postbacks, link etc.) that are passed
        to it and creates a generic message.
        '''
        message = {"attachment": {"type": "template", "payload": {}}}
        message['attachment']['payload'].update({"template_type": "generic"})
        message['attachment']['payload'].update({"elements": elements})
        return message

    def subscribe_message(self, custom_msg=''):
        '''
        This function creates a generic message displaying the sport type
        avaliable currently for the user to choose between. It sends the result
        in the postback message of type 'sports_selection'
        '''
        # imgUrl = "https://pbs.twimg.com/profile_images/718021447386443777/dIipQWNy.jpg"

        # setting the title for the generic card
        title = 'What Sport do you watch??'
        if custom_msg:
            title = custom_msg

        # creating the element for the generic message
        all_elements = []
        elements = {}
        elements.update({"title": title})
        # elements.update({"subtitle": "Subscribe for Live Updates, press YES to subscribe!"})
        # elements.update({"image_url": imgUrl})

        # creating buttons for generic message and appending it to elements
        buttons = []

        # postback json string for Football
        postback_string = {'type': 'sport_selection', 'result': 'football'}
        buttons.append({"type": "postback", "title": "Football", "payload": json.dumps(postback_string)})

        # postback json string for Cricket
        postback_string = {'type': 'sport_selection', 'result': 'cricket'}
        buttons.append({"type": "postback", "title": "Cricket", "payload": json.dumps(postback_string)})

        # postback json string for Both
        postback_string = {'type': 'sport_selection', 'result': 'both'}
        buttons.append({"type": "postback", "title": "Both", "payload": json.dumps(postback_string)})

        elements.update({"buttons": buttons})
        all_elements.append(elements)
        return self.__create_generic_message(all_elements)

    def __get_latest_news_element(self):
        '''
        Returns the first object element from the json returned by the url in
        blog_news_link, which contains the latest news article.
        '''
        try:
            r = requests.get(blog_news_link)
            if r.ok:
                return r.json()[0]
        except Exception as e:
            print "Err in __get_latest_blog_news :", str(e)
            return

    def __get_news_image(self, res):
        '''
        Returns the image of the latest news article exrtacted.
        '''
        try:
            return res['better_featured_image']['media_details']['sizes']['goodlife-latest-short']['source_url']
        except:
            return "https://pbs.twimg.com/profile_images/718021447386443777/dIipQWNy.jpg"

    def __get_news_title(self, res):
        '''
        Returns the title of the latest news article.
        '''
        return res['title']['rendered']

    def __get_news_link(self, res):
        '''
        Returns the blog URL of the latest blog news article.
        '''
        return res['link']

    def __blog_news_message(self):
        '''
        This method returns the generic message with link to latest blog article.
        '''
        # first get the response from the url of the blog news
        try:
            res = self.__get_latest_news_element()
            if res:
                imgUrl = self.__get_news_image(res)
                # creating the element for the generic message
                all_elements = []
                elements = {}
                elements.update({"title": self.__get_news_title(res)})
                elements.update({"image_url": imgUrl})

                # creating buttons for generic message and appending it to elements
                buttons = []

                # postback json string for YES
                buttons.append({"type": "web_url", "title": "View News", "url": self.__get_news_link(res)})
                elements.update({"buttons": buttons})
                all_elements.append(elements)
                return self.__create_generic_message(all_elements)
            else:
                return {'text': "Can't Fetch any news at the moment"}
        except Exception as e:
            print "Err in news_message :", str(e)
            return {"text": "Can't Fetch any news at the moment!"}

    def help_command(self):
        '''
        Returns the description of the commands that are executed by the bot.
        '''
        text = ''
        for comm in self.su_commands.keys():
            text += comm+'\n  > '+self.su_commands[comm]['doc']+'\n\n'
        return {"text": text}

    def avaliable_commands(self):
        '''
        Returns the list of avaliable commands that bot executes.
        '''
        return self.su_commands.keys()

    def process_command(self, command):
        '''
        Returns the response of the command user types on the messenger.
        '''
        if command == 'help':
            return self.help_command()
        return self.su_commands[command]['func']()

    def news_command(self):
        try:
            r = requests.get(news_api_link)
            res = r.json()
            if res['success']:
                item = res['result'][random.sample(xrange(10), 5)[random.randint(0, 4)]]
                imgUrl = item['image_link']
                # creating the element for the generic message
                all_elements = []
                elements = {}
                elements.update({"title": item['title']})
                elements.update({"image_url": imgUrl})

                # creating buttons for generic message and appending it to elements
                buttons = []

                # postback json string for YES
                buttons.append({"type": "web_url", "title": "View News", "url": 'http://sportsunity.co/news'})
                elements.update({"buttons": buttons})
                all_elements.append(elements)
                return self.__create_generic_message(all_elements)
            else:
                return self.__blog_news_message()
        except:
            return self.__blog_news_message()

    def app_command(self, custom_message=''):
        '''
        Returns back the generic message with app deeplink.
        '''
        # setting the message sent prior to the app link message
        msg = ''
        if custom_message:
            msg = custom_message
        else:
            msg = "Behold!!! Here comes the best thing ever happend for the sports Fans!!!\nCheck it out... Now!!"
        send_message_to_user(self.user_id, {'text': msg})

        imgUrl = "https://pbs.twimg.com/profile_images/718021447386443777/dIipQWNy.jpg"
        app_url = "http://sportsunity.co/sports"
        try:
            # creating the element for the generic message
            all_elements = []
            elements = {}
            elements.update({"title": "SportsUnity, an App for every sports fan, Download Now"})
            elements.update({"subtitle": "Live Scores, Live Commentry, New Discussions and many more..."})
            elements.update({"image_url": imgUrl})

            # creating buttons for generic message and appending it to elements
            buttons = []
            buttons.append({"type": "web_url", "title": "Open SportsUnity", "url":app_url})
            elements.update({"buttons": buttons})
            all_elements.append(elements)
            return self.__create_generic_message(all_elements)
        except Exception as e:
            print "Err in app_command :", str(e)
            return {'text': "Click here : "+app_url}

    def bye_command(self):
        '''
        This command deletes the user's sport prefernce and set the active flag
        to false in the database. Next time when user visits it starts the
        subsciption process again.
        '''
        query = "UPDATE FBUsers set sport='', active='false' WHERE user_id="+str(self.user_id)
        execute_sql_query(query)
        if check_if_user_in_db(self.user_id, "Followers"):
            query = "DELETE FROM Followers WHERE user_id="+str(self.user_id)
            execute_sql_query(query)
        text = "Hate to see you go... :(\n\nBut if you want to chat again, I am just a message away :)"
        return {"text": text}

    def sport_command(self):
        '''
        This command tells the user his current sport preference and sends him
        the generic message to select the sport type again.
        '''
        # get the current sport preference of user and create the msg to notify
        # and set the custom message accordingly
        msg = ''
        custom_msg = ''
        sport = check_if_user_in_db(self.user_id)
        if sport['sport']:
            msg = "Well currently you're following "
            msg += 'both Cricket and Football' if sport=='both' else str(sport['sport']).capitalize()
            custom_msg = "Which sport should we switch to??"
        else:
            msg = "You're not following any sport at the moment! :/"
            custom_msg = "Which sport do you prefer?"

        send_message_to_user(self.user_id, {"text": msg})
        return self.subscribe_message(custom_msg)

    def games_command(self):
        '''
        This command returns the games that are going to happen on present day,
        in generic message format. Each message (card) is going to have an image
        for the teams playing, a follow button and a button which is deeplinked
        to the match in the app.
        '''
        # check the sport type of the user and set the filter accordingly
        user = check_if_user_in_db(self.user_id)
        if user['sport']:

            # setting the filters to run in the mongo query
            filters = {}

            # first is the time filter, i.e. we need to get the matched which
            # are starting later from the present time, so the time filter will
            # be to get the matches with epoch greater than present time epoch
            time_filter = {"epoch": {"$gt": int(time())}}

            # if sport is 'both', then we present messages for both cricket and
            # football, so the only filter will be time_filter defined above
            if user['sport']!='both':
                # if sport is either cricket or football, set the filter with
                # the mongo AND ($and) operator to enforce both the params
                filters = {"$and": [{"sport": user['sport']}, time_filter]}

            # if filters is set to empty (sport type is 'both'), then set
            # the filters to only time_filter
            if not filters:
                filters = time_filter

            # running the mongo query with filters on
            matches = get_cards_from_mongodb(filters)
            if matches:
                all_elements = []
                for match in matches:
                    all_elements.append(match['element'])
                return self.__create_generic_message(all_elements[:5])
            else:
                return {"text": "No Games Found Today..."}
        else:
            return self.sport_command()
