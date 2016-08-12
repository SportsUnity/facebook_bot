import psycopg2
import requests
import pymongo

import os
import urlparse
import json

from traceback import print_exc


# -------------- postgres set up for Heroku Deploy ----------------
# urlparse.uses_netloc.append("postgres")
# url = urlparse.urlparse(os.environ["DATABASE_URL"])

# conn = psycopg2.connect(
#    database=url.path[1:],
#    user=url.username,
#    password=url.password,
#    host=url.hostname,
#    port=url.port
# )
# ------------------------------------------------------------------

# mongodb config vars
MONGO_HOST = None
MONGO_PORT = None

# making connection with mongodb
mongo_conn = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)

app_deeplink = 'http://sportsunity.co/scores'

blog_news_link = 'https://www.sportsunity.co/blog/wp-json/wp/v2/posts'

news_api_link = "http://NewsLB-388179569.ap-northeast-2.elb.amazonaws.com/mixed?skip=0&limit=10&image_size=hdpi&type_1=football&type_1=cricket"

try:
    conn = psycopg2.connect(
        "dbname='testdb' user='akash' host='localhost' password='sportsunity'"
    )
except Exception as e:
    print 'DB ERROR >', str(e)
    print "unable to connect to the database"


def execute_sql_query(query):
    '''
    This method executes the postresql operation with the query passed to it.
    '''
    try:
        cur = conn.cursor()
        cur.execute(query)
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        print ' >> Error :', str(e)
        print ' >> Exception in executing :', query


def send_message_to_user(user_id, message):
    '''
    This method replys to the user back using facebook api and user_id.
    '''
    # construct the params, headers and data to be sent in the post body
    params = {"access_token": "EAAWUYp92UTQBANPpjbUCbxlQZAjqC6nUZArf1Sh7KhKugTmSfgkZAkxNTiZCquwfnRFUIy6UcxZAQxiDpHcrZCY5vkcuksR6DXjyLKqwDe1woNHeJMFGbRxDM6XXZC2ylqXlWMdmqlA8mCvWI6Wb1YZAgQVRZAlbGLRS7Fgs1A5M1DAZDZD"}
    headers = {"Content-Type": "application/json"}
    data = json.dumps({"recipient": {"id": user_id},
                       "message": message
                       })
    # sending post request to the facebook API
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                  params=params, data=data, headers=headers
                  )
    print '\nStatus: ', r.json()


def check_if_user_in_db(user_id, table="FBUsers"):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT * FROM "+table+" WHERE user_id=%s", (str(user_id),))
    row = cursor.fetchone()
    # print 'status of ', user_id, row
    # print row
    return row



def get_name_of_facebook_user(u_id):
    '''
    Returns the Name of the user for the Facebook id passed to it.
    '''
    # constructing the params (access token)
    params = {'access_token': "EAAWUYp92UTQBANPpjbUCbxlQZAjqC6nUZArf1Sh7KhKugTmSfgkZAkxNTiZCquwfnRFUIy6UcxZAQxiDpHcrZCY5vkcuksR6DXjyLKqwDe1woNHeJMFGbRxDM6XXZC2ylqXlWMdmqlA8mCvWI6Wb1YZAgQVRZAlbGLRS7Fgs1A5M1DAZDZD"}

    # facebook graph api for getting name of user
    api_url = 'https://graph.facebook.com/v2.7/'+str(u_id)
    try:
        r = requests.get(api_url, params=params)
        return str(r.json()['first_name']).capitalize()
    except Exception as e:
        print 'Err in config.get_name_of_facebook_user :', str(e)
        print_exc()
        return


def get_cards_from_mongodb(filters={}):
    '''
    Returns the cards to show in generic message (carasoul) in the facebook
    messager. Each card will have an image for the teams, follow button and
    app deeplink for the game.
    All of the data will be extraceted from the MongoDB which is saved by the
    program update_db.py in the project.
    '''
    try:
        coll = mongo_conn.su_bot.today_matches
        return list(coll.find(filters))
    except:
        print 'Err in get_cards_from_mongodb'
        print_exc()
        return []
