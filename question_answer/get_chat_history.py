import datetime

import psycopg2
from decouple import config
import json

from langchain_core.messages import HumanMessage, AIMessage


HOST = config('DB_HOST')
NAME = config('DB_NAME')
USER = config('DB_USER')
PASS = config('DB_PASS')


def get_chat_from_db(class_id, member_id):
    try:
        conn = psycopg2.connect(host=HOST, user=USER, password=PASS, dbname=NAME, connect_timeout=5)
        q = f"Select chat_text from live_query_conversation where member_id = {member_id} and video_id = {class_id} ORDER BY created_time desc LIMIT 1"
        curr = conn.cursor()
        curr.execute(q)
        rows = curr.fetchall()
        if len(rows) > 0:
            return rows[0][0]
        return None
    except psycopg2.Error as e:
        print("Error connecting to PostgresSQL:", e)


def get_latest_chat_history(class_id, member_id):
    chat_str = get_chat_from_db(class_id=class_id, member_id=member_id)

    if chat_str:
        chat_dict = json.loads(chat_str)
        chat_time_list = chat_dict.keys()
        sorted_chat_time = sorted(chat_time_list)[-5:]
        latest_chat_list = [chat_dict[chat_time] for chat_time in sorted_chat_time]
        return latest_chat_list
    return []


# def get_processed_chat_history(class_id, member_id):
#     chat_history_list = get_latest_chat_history(class_id=class_id, member_id=member_id)
#     chat_list = []
#     for chat_history in chat_history_list:
#         chat_list.append(f"human: {chat_history['question']}")
#         chat_list.append(f"AI: {chat_history['response']}")
#
#     return "\n".join(chat for chat in chat_list)


def get_processed_chat_history(class_id, member_id):
    chat_history_list = get_latest_chat_history(class_id=class_id, member_id=member_id)
    chat_list = []
    for chat_history in chat_history_list:
        chat_list.append(HumanMessage(content=chat_history['question']))
        chat_list.append(AIMessage(content=chat_history['response']))

    return chat_list


def update_create_chat_history(query, refresh, class_id, member_id, package_id, res):
    if not int(refresh):
        chat = json.dumps({
            str(datetime.datetime.now()): {
                "question": query,
                "response": res,
                "time": str(datetime.datetime.now()),
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
            curr.execute(q, (member_id, chat, package_id, class_id, datetime.datetime.now()))
            conn.commit()
            conn.close()
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
            if len(rows) > 0:
                id = rows[0][0]
                chat_text = rows[0][1]
                chat_dict = json.loads(chat_text)
                chat_dict[str(datetime.datetime.now())] = {
                        "question": query,
                        "response": res,
                        "time": str(datetime.datetime.now()),
                        "like": None
                }
                chat = json.dumps(chat_dict)
                update_q = f"""
                UPDATE live_query_conversation set chat_text=%s,modified_time=%s where 
                id = %s
                """

                curr.execute(update_q, (chat, datetime.datetime.now(), id))
                conn.commit()
                conn.close()
        except psycopg2.Error as e:
            print("Error connecting to PostgresSQL:", e)











