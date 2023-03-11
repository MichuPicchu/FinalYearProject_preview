import sqlite3
import threading
import time
import uuid
from datetime import datetime
import pandas as pd
import schedule

from exts import db


def read_all_data(table_name):
    engine = db.get_engine()
    with engine.connect() as conn:
        result = conn.execute(f"SELECT * FROM {table_name}")
    return result.fetchall()


def write_in_sqlite(dataframe, database_file, table_name, dtype=None):
    cnx = sqlite3.connect(database_file)
    dataframe.to_sql(table_name,
                     if_exists='append',
                     con=cnx)


def get_column(database_file, table_name, column_name):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    query = "SELECT {column_name} FROM {table_name}".format(column_name=column_name,
                                                            table_name=table_name)
    cursor.execute(query)
    return cursor.fetchall()


def get_row_id(table_name, column, id):  # get row given id ***
    engine = db.get_engine()
    query = "SELECT * FROM {table_name} WHERE {column} = {keyword};".format(
        table_name=table_name,
        column=column,
        keyword=id
    )
    with engine.connect() as conn:
        print(query)
        result = conn.execute(query)
    return result.fetchone()


# for recommender system
def get_user_list():
    engine = db.get_engine()
    query = "SELECT uid, user_name, preference FROM user;"
    with engine.connect() as conn:
        result = conn.execute(query)
    temp = result.fetchall()

    return_json = []
    for i in temp:
        temp_json = (i[0], i[1], i[2])
        return_json.append(temp_json)

    return return_json


# for recommender system
def get_restaurant_list():
    engine = db.get_engine()
    query = "SELECT rid, name FROM restaurant;"
    with engine.connect() as conn:
        result = conn.execute(query)
    temp = result.fetchall()

    return_json = []
    for i in temp:
        temp_json = (i[0], i[1])
        return_json.append(temp_json)

    return return_json


def upload_db(location):
    res = pd.read_csv(location, sep=',', header='infer', index_col=0)
    return res


def get_row(table_name, column, keyword):  # get row given column string ***
    engine = db.get_engine()
    query = "SELECT * FROM {table_name} WHERE {column} = '{keyword}';".format(
        table_name=table_name,
        column=column,
        keyword=keyword
    )
    with engine.connect() as conn:
        print(query)
        result = conn.execute(query)
    return result.fetchone()


def get_mutiple_rows(table_name, column, keyword):
    engine = db.get_engine()
    query = "SELECT * FROM {table_name} WHERE {column} = '{keyword}';".format(
        table_name=table_name,
        column=column,
        keyword=keyword
    )
    with engine.connect() as conn:
        result = conn.execute(query)
    return result.fetchall()


def get_mutiple_rows_where_id(table_name, column, keyword):
    engine = db.get_engine()
    query = "SELECT * FROM {table_name} WHERE {column} = {keyword};".format(
        table_name=table_name,
        column=column,
        keyword=keyword
    )
    with engine.connect() as conn:
        result = conn.execute(query)
    return result.fetchall()


def get_newest_id(table_name, column):
    engine = db.get_engine()
    query = "SELECT MAX({column}) FROM {table_name};".format(
        column=column,
        table_name=table_name
    )
    with engine.connect() as conn:
        result = conn.execute(query)
    return result.fetchone()[0]


def generate_vouchers(gvid, num):
    engine = db.get_engine()
    for i in range(num):
        code_ = str(uuid.uuid4())
        print('code:', code_)
        with engine.connect() as conn:
            conn.execute(
                f"INSERT INTO voucher (vid, gvid, code, booked, used, review, rating) VALUES "
                f"(NULL, {gvid}, '{code_}', NULL, NULL, NULL, NULL)")


def voucher_to_json(db_output):
    temp = {
        'vid': db_output[0],
        'gvid': db_output[1],
        'code': db_output[2],
        'booked': db_output[3],
        'used': db_output[4],
        'review': db_output[5],
        'rating': db_output[6]
    }
    return temp


def voucher_info_to_json(db_output):
    temp = {
        'gvid': db_output[0],
        'rid': db_output[1],
        'title': db_output[2],
        'session_time': db_output[3].strftime('%Y-%m-%d %H:%M:%S'),
        'num': db_output[4],
        'discount': db_output[5],
        'regular': db_output[6],
        'description': db_output[7],
    }
    return temp


def restaurant_to_json(i):
    temp = {
        'rid': i[0],
        'name': i[1],
        'address': i[2],
        'postcode': i[3],
        'cuisine': i[4],
        'avg_rating': i[6],
        'special_cond': i[7],
        'intro': i[8],
        'photos': i[9],
        'operating_hours': i[10],
        'url': i[11]

    }
    return temp


def menu_to_json(i):
    temp = {
        'mid': i[0],
        'rid': i[1],
        'image': i[2],
        'type': i[3]
    }
    return temp


def ad_list_to_json(i):
    temp = {
        'rid': i[0],
        'paid_fee': i[1]
    }
    return temp


def update_discount_flag():
    engine = db.get_engine()
    with engine.connect() as conn:
        ...


def community_to_json(i):
    temp = {
        'aid': i[0],
        'rid': i[1],
        'uid': i[2],
        'title': i[3],
        'content': i[4],
        'img': i[5],
        'release_time': i[8].strftime('%Y-%m-%d %H:%M:%S')
    }
    return temp


def question_to_json(db_output):
    temp = {
        'id': db_output[0],
        'rid': db_output[1],
        'qid': db_output[2],
        'uid': db_output[3],
        'type': db_output[4],
        'content': db_output[5],
        'flag': db_output[6],
        'title': db_output[7],
    }
    return temp


# given an introduction, cut the intro to just first 30 words
def brief_introduction(intro):
    passage_list = intro.split(' ')
    return ' '.join(passage_list[:30]) + '...'


def run_continuously(self, interval=0):
    cease_continuous_run = threading.Event()

    class ScheduleThread(threading.Thread):
        @classmethod
        def run(cls):
            while not cease_continuous_run.is_set():
                self.run_pending()
                time.sleep(interval)

    continuous_thread = ScheduleThread()
    continuous_thread.start()
    return cease_continuous_run


def generate_voucher_job(rid, num, discount, regular, title, description):
    session_time = datetime.now()
    with db.get_engine().connect() as conn:
        insert_sql = "insert into voucher_info (gvid, rid, session_time, num, discount, regular, title, description) " \
                     "values (NULL, '{}', '{}', '{}', " \
                     "'{}', '{}', '{}', '{}') ;".format(
            rid, session_time, num, discount, regular, title, description
        )
        conn.execute(insert_sql)
    new_gvid = get_newest_id('voucher_info', 'gvid')
    generate_vouchers(new_gvid, num)

