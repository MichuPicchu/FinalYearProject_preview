from flasgger import swag_from
from flask import Blueprint, request

from helper import *

rest_bp = Blueprint('restaurant', __name__, url_prefix='/restaurant')


# return all restaurants
@rest_bp.route("/", methods=['GET'])
def show():
    result = []
    for i in read_all_data('restaurant'):
        result.append(restaurant_to_json(i))
    return result, 200


# update rating for every restaurant
@rest_bp.route("/update_rating", methods=['PUT'])
@swag_from('../api_doc/restaurant/update_rating.yml')
def update_rating():
    engine = db.get_engine()
    sql = "SELECT rid, avg(rating) FROM " \
          "voucher INNER JOIN voucher_info vi on voucher.gvid = vi.gvid " \
          "WHERE rating IS NOT NULL " \
          "GROUP BY rid;"
    with engine.connect() as conn:
        result = conn.execute(sql)
        temp = result.fetchall()
    res = {}
    try:
        for rid, rating in temp:
            with engine.connect() as conn:
                update_sql = "UPDATE restaurant SET avg_rating = {} WHERE rid = {};".format(rating, rid)
                conn.execute(update_sql)
            res[rid] = rating
        return res, 200
    except:
        return "update rating error", 400


# show a restaurant by restaurant id
@rest_bp.route("/<int:rid>", methods=['GET'])
@swag_from('../api_doc/restaurant/show.yml')
def get_restaurant(rid):
    restaurant_info = get_row_id('restaurant', 'rid', rid)
    result = restaurant_to_json(restaurant_info)

    voucher_info = get_mutiple_rows('voucher_info', 'rid', rid)
    voucher_temp_list = []
    voucher_info_id_set = set()
    for i in voucher_info:
        if i['num'] == 0:
            continue
        voucher_temp_list.append(voucher_info_to_json(i))
        voucher_info_id_set.add(i[0])
    result['voucher_info'] = voucher_temp_list

    # question and rating
    review_list = []

    if voucher_info_id_set:
        engine = db.get_engine()
        with engine.connect() as conn:
            if len(voucher_info_id_set) == 1:
                query_sql = "SELECT user_name, review, rating " \
                            "FROM user INNER JOIN voucher ON user.uid = voucher.booked " \
                            "WHERE gvid = {} AND review IS NOT NULL;".format(voucher_info_id_set.pop())
            else:
                query_sql = "SELECT user_name, review, rating " \
                            "FROM user INNER JOIN voucher ON user.uid = voucher.booked " \
                            "WHERE gvid IN {} AND review IS NOT NULL;".format(tuple(voucher_info_id_set))
            res = conn.execute(query_sql)
            rr = res.fetchall()
            for i in rr:
                temp = {'user_name': i[0], 'review': i[1], 'rating': i[2]}
                review_list.append(temp)

    question_list = get_all_question(rid)
    result['question'] = question_list

    # menu info
    menu_info = get_row('menu', 'rid', rid)
    result['menu_url'] = menu_info['image']
    result['menu_type'] = menu_info['type']

    return result, 200


# search and filter restaurant by name
@rest_bp.route("/search", methods=['GET'])
@swag_from('../api_doc/restaurant/search.yml')
def search():
    print(request.headers)
    result = []
    keyword = request.headers.get('keyword')
    keyword = keyword.lower()
    cuisine = request.headers.get('cuisine')
    discount = request.headers.get('discount')
    preference = request.headers.get('preference')
    uid = request.headers.get('uid')
    engine = db.get_engine()
    # filter by preference
    preference_rid_list = []
    if preference and preference != 'null' and uid:
        if preference == 'hadbooking':
            pre_sql = f"SELECT DISTINCT(rid) FROM restaurant " \
                      f"WHERE rid IN (SELECT DISTINCT(rid) FROM " \
                      f"voucher_info INNER JOIN voucher v on voucher_info.gvid = v.gvid " \
                      f"WHERE v.booked={uid}) ;"
        else:
            pre_sql = f"SELECT DISTINCT(rid) FROM restaurant " \
                      f"WHERE rid NOT IN (SELECT DISTINCT(rid) FROM " \
                      f"voucher_info INNER JOIN voucher v on voucher_info.gvid = v.gvid " \
                      f"WHERE v.booked={uid}) ;"
        with engine.connect() as conn:
            res = conn.execute(pre_sql)
            preference_rid_list = res.fetchall()
    if preference_rid_list:
        preference_rid_list = [i[0] for i in preference_rid_list]
    query_result = []
    rid_result = set()
    if discount and discount.lower() == 'true':
        sql = "SELECT rid FROM restaurant WHERE rid IN (SELECT DISTINCT rid FROM voucher_info WHERE num>0);"
    elif discount and discount.lower() == 'false':
        sql = "SELECT rid FROM restaurant WHERE rid NOT IN (SELECT DISTINCT rid FROM voucher_info WHERE num>0);"
    else:
        sql = "SELECT rid FROM restaurant;"

    with engine.connect() as conn:
        res = conn.execute(sql)
        rid_list = res.fetchall()
    rid_list = [i[0] for i in rid_list]
    # intersection rid_list and preference_rid_list
    if preference_rid_list:
        rid_list = list(set(rid_list).intersection(set(preference_rid_list)))
    for search_type in ['name', 'address', 'postcode', 'cuisine']:
        with engine.connect() as conn:
            cursor = conn.execute(f"SELECT * FROM restaurant WHERE LOWER({search_type}) LIKE '%%{keyword}%%'")
        for i in cursor.fetchall():

            if i[0] not in rid_result and i[0] in rid_list:
                rid_result.add(i[0])
                query_result.append(i)

    if query_result:
        for row in query_result:
            judge_search = True
            if ((cuisine != 'null') or (not cuisine)) and cuisine != row[4]:
                judge_search = False
            temp = {
                "Rid": row[0],
                "Name": row[1],
                "Introduction": row[8],
                "Photos": row[9]
            }
            if judge_search is True:
                result.append(temp)
    return result, 200


# post question
@rest_bp.route("/put_question", methods=['PUT'])
@swag_from('../api_doc/restaurant/post_question.yml')
def put_question():
    res_details = request.json  # {rid, uid, title, content}
    print(res_details)
    res_details["flag"] = 0
    res_details["type"] = "question"

    try:
        engine = db.get_engine()
        with engine.connect() as conn:
            insert_sql = "insert into question (id, rid, qid, uid, type, content, flag, title) " \
                         "values (null, '{}', null, '{}', " \
                         "'{}', '{}', '{}', '{}') ;".format(
                res_details['rid'], res_details['uid'], res_details['type'], res_details['content'],
                res_details['flag'], 'test'
            )
            print(insert_sql)
            conn.execute(insert_sql)
    except:
        return "community db put error", 400

    auto_update_qid_questions()  # auto update the NULL qid to = its own id.

    return res_details, 200


# updates the qid of all questions
@rest_bp.route("/update_qid_question", methods=['PATCH'])
def auto_update_qid_questions():
    engine = db.get_engine()
    with engine.connect() as conn:
        result = conn.execute(f"select * from question where qid is NULL;")
    row = result.fetchall()
    with engine.connect() as conn:
        for i in row:
            temp2 = question_to_json(i)
            new_qid = conn.execute(f"select max(qid) from question;").fetchone()[0] + 1
            sql = """
                    UPDATE question SET qid = "{}"
                    where id = {} ;
                    """.format(
                new_qid, temp2['id']
            )
            print(sql)
            conn.execute(sql)
    return "updated qid questions", 200


# post answer
@rest_bp.route("/put_answer", methods=['PUT'])
@swag_from('../api_doc/restaurant/post_answer.yml')
def put_answer():
    res_details = request.json  # {uid, qid, content}

    if "qid" not in res_details:
        return "please enter qid", 400
    else:
        try:
            engine = db.get_engine()
            query = "select * from question where qid = '{}';".format(
                res_details['qid']
            )
            with engine.connect() as conn:
                print('query: ', query)
                temp = conn.execute(query)
                temp1 = temp.fetchone()
                result = question_to_json(temp1)
        except:
            return "cannot get id from user db error", 400

    res_details['rid'] = result['rid']
    res_details['title'] = result['title']
    res_details["type"] = "answer"
    print(res_details)

    # from uid, check whether answerer is customer or merchant.
    try:
        engine = db.get_engine()
        query = "select role from user where uid = '{}';".format(
            res_details['uid']
        )
        with engine.connect() as conn:
            print('query: ', query)
            temp = conn.execute(query)
    except:
        return "get role from user error", 200
    result = temp.fetchone()
    if result[0] == "customer":
        res_details["flag"] = 0
    elif result[0] == "merchant":
        res_details["flag"] = 1

    try:
        engine = db.get_engine()
        with engine.connect() as conn:
            insert_sql = "insert into question (id, rid, qid, uid, type, content, flag, title) " \
                         "values (null, '{}', '{}', '{}', " \
                         "'{}', '{}', '{}', '{}') ;".format(
                res_details['rid'], res_details['qid'], res_details['uid'], res_details['type'], res_details['content'],
                res_details['flag'], res_details['title']
            )
            print(insert_sql)
            conn.execute(insert_sql)
    except:
        return "question db put error", 400

    return res_details, 200


# get all questions and answers for a restaurant
@rest_bp.route("/get_all_question/<int:rid>", methods=['GET'])
@swag_from('../api_doc/restaurant/get_all_question.yml')
def get_all_question(rid):
    res = []
    qid_list = []
    sql = f"SELECT distinct qid FROM question WHERE rid={rid};"
    with db.get_engine().connect() as conn:
        result = conn.execute(sql)
        for row in result:
            qid_list.append(row[0])

    for qid in qid_list:
        sql = f"SELECT * FROM question WHERE qid={qid} AND rid={rid};"
        temp = {"qid": qid}
        question_dict = {}
        answer_list = []
        with db.get_engine().connect() as conn:
            result = conn.execute(sql)
            for row in result:
                uid = row['uid']
                user_name = get_row('user', 'uid', uid)['user_name']
                if row['type'] == "question":
                    question_dict['uid'] = uid
                    question_dict['user_name'] = user_name
                    question_dict['content'] = row['content']
                else:
                    answer_list.append({
                        "uid": uid,
                        "user_name": user_name,
                        "content": row['content'],
                        "flag": row['flag'],
                        "id": row['id']
                    })
            temp['question'] = question_dict
            temp['answer'] = answer_list
        res.append(temp)
    return res


# edit restaurant profile
@rest_bp.route("/edit_info", methods=['PUT'])
@swag_from('../api_doc/restaurant/edit_info.yml')
def edit_info():
    res_details = request.json  # {rid}
    rid = res_details['rid']
    request_keys = list(res_details.keys())

    if 'name' in request_keys:
        new_name = res_details['name']
        if get_row('restaurant', 'name', new_name):
            return "name already exists", 400
        sql = f"UPDATE restaurant SET name='{new_name}' WHERE rid={rid};"
        res = {'name': new_name}
    elif 'address' in request_keys:
        new_address = res_details['address']
        sql = f"UPDATE restaurant SET address='{new_address}' WHERE rid={rid};"
        res = {'address': new_address}
    elif 'postcode' in request_keys:
        new_postcode = res_details['postcode']
        sql = f"UPDATE restaurant SET postcode='{new_postcode}' WHERE rid={rid};"
        res = {'postcode': new_postcode}
    elif 'cuisine' in request_keys:
        new_cuisine = res_details['cuisine']
        sql = f"UPDATE restaurant SET cuisine='{new_cuisine}' WHERE rid={rid};"
        res = {'cuisine': new_cuisine}
    elif 'intro' in request_keys:
        new_intro = res_details['intro']
        sql = f"UPDATE restaurant SET intro='{new_intro}' WHERE rid={rid};"
        res = {'intro': new_intro}
    elif 'paid_fee' in request_keys:
        new_paid_fee = res_details['paid_fee']
        sql = f"UPDATE restaurant SET paid_fee='{new_paid_fee}' WHERE rid={rid};"
        res = {'paid_fee': new_paid_fee}
    elif 'operating_hours' in request_keys:
        new_operating_hours = res_details['operating_hours']
        sql = f"UPDATE restaurant SET operating_hours='{new_operating_hours}' WHERE rid={rid};"
        res = {'operating_hours': new_operating_hours}
    else:
        return "invalid input", 401

    engine = db.get_engine()
    with engine.connect() as conn:
        conn.execute(sql)

    return res, 200


# edit restaurant menu
@rest_bp.route("/edit_menu", methods=['PUT'])
def edit_menu():
    res_details = request.json
    rid = res_details['rid']
    img_url = res_details['img_url']
    menu_type = res_details['menu_type']

    with db.get_engine().connect() as conn:
        sql = f"SELECT * FROM menu WHERE rid = '{rid}' AND type = '{menu_type}';"
        result = conn.execute(sql)
        if result.fetchone():
            sql = f"UPDATE menu SET image = '{img_url}' WHERE rid = '{rid}' AND type = '{menu_type}';"
            conn.execute(sql)
            return "update menu successfully", 200
        else:
            sql = f"INSERT INTO menu (rid, type, image) VALUES ('{rid}', '{menu_type}', '{img_url}');"
            conn.execute(sql)
            return "insert menu successfully", 201


# return the top 3 ad restaurants
@rest_bp.route('/ad_list', methods=['GET'])
@swag_from('../api_doc/restaurant/ad_list.yml')
def get_ad_list():
    engine = db.get_engine()
    query = "SELECT paid_fee FROM restaurant ORDER BY paid_fee DESC;"
    with engine.connect() as conn:
        temp = conn.execute(query)
    result = temp.fetchall()

    return str(result[3][0]), 200


# display the ad restaurant list in the homepage
@rest_bp.route('/home_ad_list', methods=['GET'])
@swag_from('../api_doc/restaurant/home_ad_list.yml')
def get_home_ad_list():
    engine = db.get_engine()
    query = "SELECT * FROM restaurant ORDER BY paid_fee DESC;"
    with engine.connect() as conn:
        query_res = conn.execute(query)
    res = []
    for row in query_res.fetchall():
        intro = row['intro'].split(' ')
        intro = ' '.join(intro[:30]) + '...'
        temp = {
            'rid': row['rid'],
            'name': row['name'],
            'photo': row['photos'],
            'intro': intro,
        }
        res.append(temp)

    return res[:4], 200


# delete whole question
@rest_bp.route('/delete_question', methods=['DELETE'])
@swag_from('../api_doc/restaurant/delete_question.yml')
def delete_question():
    data = request.json
    qid = data['qid']
    uid = data['uid']
    if not get_row('question', 'qid', qid):
        return "question does not exist", 400
    engine = db.get_engine()
    with engine.connect() as conn:
        check_uid = conn.execute(f"SELECT uid FROM question WHERE qid = {qid} AND type = 'question';").fetchone()
        if str(check_uid['uid']) != str(uid):
            return "not the owner", 401
        sql = f"DELETE FROM question WHERE qid = {qid};"
        conn.execute(sql)
    return "delete question successfully", 200


# delete single answer
@rest_bp.route('/delete_answer', methods=['DELETE'])
@swag_from('../api_doc/restaurant/delete_answer.yml')
def delete_answer():
    data = request.json
    id_ = data['id']
    uid = data['uid']
    if not get_row('question', 'id', id_):
        return "answer does not exist", 400
    engine = db.get_engine()
    with engine.connect() as conn:
        check_uid = conn.execute(f"SELECT uid FROM question WHERE id = {id_} AND type = 'answer';").fetchone()
        if str(check_uid['uid']) != str(uid):
            return "not the owner", 401
        sql = f"DELETE FROM question WHERE id = {id_};"
        conn.execute(sql)
    return "delete answer successfully", 200
