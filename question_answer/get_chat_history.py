import datetime

import pymysql
from decouple import config
import json

HOST = config('DB_HOST')
NAME = config('DB_NAME')
USER = config('DB_USER')
PASS = config('DB_PASS')


def get_chat_from_db(class_id, member_id):
    try:
        print("connection to db for chat history...............")
        print("start_time:", datetime.datetime.now())
        conn = pymysql.connect(host=HOST, user=USER, passwd=PASS, db=NAME, connect_timeout=5)
        print("end_time: ", datetime.datetime.now())
        q = f"Select chat_text from live_query_conversation where member_id = {member_id} and video_id = {class_id} ORDER BY created_time desc LIMIT 1"
        curr = conn.cursor()
        print("executing query for chat history...............")
        print("start_time:", datetime.datetime.now())
        row_count = curr.execute(q)
        print("end_time:", datetime.datetime.now())
        rows = curr.fetchall()
        if len(rows) > 0:
            return rows[0][0]
        return None
    except pymysql.MySQLError as err:
        print(err)


def get_latest_chat_history(class_id, member_id):
    chat_str = get_chat_from_db(class_id=class_id, member_id=member_id)

    if chat_str:
        chat_dict = json.loads(chat_str)
        chat_time_list = chat_dict.keys()
        sorted_chat_time = sorted(chat_time_list)[-5:]
        latest_chat_list = [chat_dict[chat_time] for chat_time in sorted_chat_time]
        return latest_chat_list
    return []


def get_processed_chat_history(class_id, member_id):
    chat_history_list = get_latest_chat_history(class_id=class_id, member_id=member_id)
    chat_list = []
    for chat_history in chat_history_list:
        chat_list.append(f"human: {chat_history['question']}")
        chat_list.append(f"AI: {chat_history['response']}")

    return "\n".join(chat for chat in chat_list)
