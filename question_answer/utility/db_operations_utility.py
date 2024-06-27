import datetime

import psycopg2
from decouple import config
import json

from langchain_core.messages import HumanMessage, AIMessage


HOST = config('DB_HOST')
NAME = config('DB_NAME')
USER = config('DB_USER')
PASS = config('DB_PASS')


def get_chat_from_db(class_id, member_id, ca_query=False):
    try:
        conn = psycopg2.connect(host=HOST, user=USER, password=PASS, dbname=NAME, connect_timeout=5)
        if not ca_query:
            q = f"Select chat_text from live_query_conversation where member_id = {member_id} and video_id = {class_id} ORDER BY created_time desc LIMIT 1"
        else:
            q = f"Select chat_text from ca_live_query_conversation where member_id = {member_id} and article_id = {class_id} ORDER BY created_time desc LIMIT 1"
        curr = conn.cursor()
        curr.execute(q)
        rows = curr.fetchall()
        if len(rows) > 0:
            return rows[0][0]
        return None
    except psycopg2.Error as e:
        print("Error connecting to PostgresSQL:", e)


def get_latest_chat_history(class_id, member_id, ca_query=False):
    chat_str = get_chat_from_db(class_id=class_id, member_id=member_id, ca_query=ca_query)

    if chat_str:
        chat_dict = json.loads(chat_str)
        chat_time_list = chat_dict.keys()
        sorted_chat_time = sorted(chat_time_list)[-5:]
        latest_chat_list = [chat_dict[chat_time] for chat_time in sorted_chat_time]
        return latest_chat_list
    return []


def get_chat_history_for_ask_expert(class_id, member_id):
    chat_history_list = get_latest_chat_history(class_id=class_id, member_id=member_id)
    chat_list = []
    for chat_history in chat_history_list:
        chat_list.append(chat_history['question'])
    return chat_list


def get_processed_chat_history(class_id, member_id, ca_query=False):
    chat_history_list = get_latest_chat_history(class_id=class_id, member_id=member_id, ca_query=ca_query)
    chat_list = []
    for chat_history in chat_history_list:
        chat_list.append(HumanMessage(content=chat_history['question']))
        chat_list.append(AIMessage(content=chat_history['response']))

    return chat_list


def update_create_chat_history(query, old_conversation, class_id, member_id, package_id, res):
    if old_conversation == 'false':
        time_stamp = datetime.datetime.now()
        chat = json.dumps({
            str(time_stamp): {
                "question": query,
                "response": res,
                "time": str(time_stamp),
                "like": None
            }
        })
        q = """
        INSERT INTO live_query_conversation (member_id, chat_text, package_id, video_id, created_time)
    VALUES (%s, %s, %s, %s, %s);
        """
        try:
            conn = psycopg2.connect(host=HOST, user=USER, password=PASS, dbname=NAME, connect_timeout=5)
            curr = conn.cursor()
            curr.execute(q, (member_id, chat, package_id, class_id, time_stamp))
            conn.commit()
            get_query = f"""
            Select id from live_query_conversation where member_id={member_id} and video_id={class_id} ORDER BY 
            created_time desc LIMIT 1 """

            curr.execute(get_query)
            row = curr.fetchall()
            conn.close()
            id = row[0][0]
            return id, time_stamp
        except psycopg2.Error as e:
            print("Error connecting to PostgresSQL:", e)

    else:
        already_exist_q = f"""
        SELECT id, chat_text FROM live_query_conversation 
                        WHERE member_id = {member_id} and video_id = {class_id} ORDER BY created_time desc limit 1
        """

        try:
            conn = psycopg2.connect(host=HOST, user=USER, password=PASS, dbname=NAME, connect_timeout=5)
            curr = conn.cursor()
            curr.execute(already_exist_q)
            rows = curr.fetchall()
            id = rows[0][0]
            chat_text = rows[0][1]
            time_stamp = datetime.datetime.now()
            if len(rows) > 0:
                chat_dict = json.loads(chat_text)
                chat_dict[str(time_stamp)] = {
                        "question": query,
                        "response": res,
                        "time": str(time_stamp),
                        "like": None
                }
                chat = json.dumps(chat_dict)
                update_q = f"""
                UPDATE live_query_conversation set chat_text=%s,modified_time=%s where 
                id = %s
                """

                curr.execute(update_q, (chat, time_stamp, id))
                conn.commit()
                conn.close()
                return id, time_stamp
        except psycopg2.Error as e:
            print("Error connecting to PostgresSQL:", e)



def update_create_ca_chat_history(query, old_conversation, article_id, member_id, res):

    if old_conversation == 'false':
        time_stamp = datetime.datetime.now()
        chat = json.dumps({
            str(time_stamp): {
                "question": query,
                "response": res,
                "time": str(time_stamp),
                "like": None
            }
        })
        q = """
        INSERT INTO ca_live_query_conversation (member_id, chat_text, article_id, created_time)
        VALUES (%s, %s, %s, %s);
        """
        try:
            print(("value check",member_id, chat, article_id, time_stamp))
            conn = psycopg2.connect(host=HOST, user=USER, password=PASS, dbname=NAME, connect_timeout=5)
            curr = conn.cursor()
            curr.execute(q, (member_id, chat, article_id, time_stamp))
            conn.commit()
            get_query = f"""
            Select id from ca_live_query_conversation where member_id={member_id} and article_id={article_id} ORDER BY 
            created_time desc LIMIT 1 """

            curr.execute(get_query)
            row = curr.fetchall()
            conn.close()
            id = row[0][0]
            print("query id:", row)
            return id, time_stamp
        except psycopg2.Error as e:
            print("Error connecting to PostgresSQL:", e)

    else:
        already_exist_q = f"""
                        SELECT id, chat_text FROM ca_live_query_conversation 
                        WHERE member_id = {member_id} and article_id = {article_id} ORDER BY created_time desc limit 1
        """

        try:
            conn = psycopg2.connect(host=HOST, user=USER, password=PASS, dbname=NAME, connect_timeout=5)
            curr = conn.cursor()
            curr.execute(already_exist_q)
            rows = curr.fetchall()
            id = rows[0][0]
            chat_text = rows[0][1]
            time_stamp = datetime.datetime.now()
            if len(rows) > 0:
                chat_dict = json.loads(chat_text)
                chat_dict[str(time_stamp)] = {
                        "question": query,
                        "response": res,
                        "time": str(time_stamp),
                        "like": None
                }
                chat = json.dumps(chat_dict)
                update_q = f"""
                UPDATE ca_live_query_conversation set chat_text=%s,modified_time=%s where 
                id = %s
                """

                curr.execute(update_q, (chat, time_stamp, id))
                conn.commit()
                conn.close()
                return id, time_stamp
        except psycopg2.Error as e:
            print("Error connecting to PostgresSQL:", e)


def update_like_dislike_status(action, id, time_stamp):

    try:
        conn = psycopg2.connect(host=HOST, user=USER, password=PASS, dbname=NAME, connect_timeout=5)
        curr = conn.cursor()

        q = f"""
        Select chat_text from live_query_conversation where id={id}
        """
        curr.execute(q)
        row = curr.fetchall()
        chat_text = row[0][0]
        chat_dict = json.loads(chat_text)
        like_value = chat_dict[time_stamp]['like']
        chat_dict[time_stamp]['like'] = '0' if like_value == action else action
        chat = json.dumps(chat_dict)

        update_q = f"""
        UPDATE live_query_conversation set chat_text=%s where 
        id = %s
        """
        curr.execute(update_q, (chat, id))
        conn.commit()
        conn.close()
        return True
    except psycopg2.Error as e:
        print("Error connecting to PostgresSQL:", e)
        return False



