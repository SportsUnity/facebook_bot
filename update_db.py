'''
This file runs everyday at 00:00 hours. It deletes the previous games entries
and updates the database with the present day matches for cricket and football.
'''

from cards import SportsCards
from config import mongo_conn

import pymongo


# def generate_cards_from_db():
#    coll = mongo_conn.su_bot.today_matches
#    print list(coll.find())

if __name__ == '__main__':
    # first delete the previous entries by dropping the database
    # so that we can fresh start and get insert fresh matches entries
    mongo_conn.drop_database("su_bot")

    # get new matches and save it into database with get_game_cards method
    obj = SportsCards("https://f7c7279e.ngrok.io")
    obj.get_game_cards()
