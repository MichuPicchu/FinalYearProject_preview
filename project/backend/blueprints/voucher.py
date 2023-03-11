import datetime as d

from flasgger import swag_from
from flask import Blueprint, request

from helper import *
from .restaurant import update_rating

voucher_bp = Blueprint('voucher', __name__, url_prefix='/voucher')


# return voucher database
@voucher_bp.route('/')
def show():
    result = []
    for i in read_all_data('voucher'):
        result.append(voucher_to_json(i))
    print('#rows: ', len(result))
    return result, 200


# return voucher_info database
@voucher_bp.route('/voucher_info', methods=['GET'])
def get_voucher_info():
    result = []
    for i in read_all_data('voucher_info'):
        result.append(voucher_info_to_json(i))
    print('#rows: ', len(result))
    return result, 200


# get voucher info data given gvid
@voucher_bp.route('/get_from_gvid', methods=['GET'])
@swag_from('../api_doc/voucher/get_from_gvid.yml')
def get_gvid():
    gvid = request.headers.get('gvid')
    engine = db.get_engine()
    try:
        query = "SELECT * FROM voucher_info WHERE gvid = '{gvid}';".format(gvid=gvid)
        with engine.connect() as conn:
            result = conn.execute(query)
        return voucher_info_to_json(result.fetchone()), 200
    except:
        return 'No such gvid', 404


# get voucher data given vid
@voucher_bp.route('/get_from_vid', methods=['GET'])
@swag_from('../api_doc/voucher/get_from_vid.yml')
def get_voucher():
    vid = request.headers.get('vid')
    engine = db.get_engine()
    try:
        with engine.connect() as conn:
            query_sql = f"SELECT vid, voucher_info.rid, name, discount, session_time, code, title, description\
                            FROM voucher_info\
                                     INNER JOIN voucher v on voucher_info.gvid = v.gvid\
                                     INNER JOIN restaurant ON voucher_info.rid = restaurant.rid\
                            WHERE vid = {vid};"
            res = conn.execute(query_sql)
            rr = res.fetchone()
            result = {
                'vid': rr[0],
                'rid': rr[1],
                'r_name': rr[2],
                'discount': rr[3],
                'session_time': rr[4].strftime('%Y-%m-%d %H:%M:%S'),
                'code': rr[5],
                'title': rr[6],
                'description': rr[7]
            }
            return result, 200
    except:
        return "SQL error", 400


# generate new vouchers
@voucher_bp.route('/generate', methods=['POST'])
@swag_from('../api_doc/voucher/generate.yml')
def generate():
    res_details = request.json
    engine = db.get_engine()
    rid = res_details['rid']
    session_time = datetime.now() + d.timedelta(days=7)
    session_time = session_time.replace(minute=0, second=0)
    num = int(res_details['num'])
    discount = res_details['discount']
    title = res_details['title']
    description = res_details['description']
    regular = 'weekly'
    flag = 'active'
    if res_details['meridiem'] and res_details['regular'] and res_details['regular_time']:
        flag = 'regularly'
        regular_time = datetime.strptime(res_details['regular_time'], '%H')
        regular = res_details['regular']
        meridiem = res_details['meridiem']

        if meridiem == 'pm':
            regular_time += d.timedelta(hours=12)

        if regular == 'daily':
            schedule.every().day.do(generate_voucher_job, rid=rid, num=num,
                                    discount=discount, regular=regular, title=title,
                                    description=description)
        elif regular == 'weekly':
            schedule.every(7).day.at(regular_time.strftime('%H:%M')).do(generate_voucher_job, rid=rid, num=num,
                                                                        discount=discount, regular=regular, title=title,
                                                                        description=description)
        else:
            schedule.every(30).day.at(regular_time.strftime('%H:%M')).do(generate_voucher_job, rid=rid, num=num,
                                                                         discount=discount, regular=regular,
                                                                         title=title, description=description)

        run_continuously(schedule)

    if flag == 'active':
        with engine.connect() as conn:
            insert_sql = "insert into voucher_info (gvid, rid, session_time, num, discount, regular, title, description) " \
                         "values (NULL, '{}', '{}', '{}', " \
                         "'{}', '{}', '{}', '{}') ;".format(
                rid, session_time, num, discount, regular, title, description
            )
            conn.execute(insert_sql)
        new_gvid = get_newest_id('voucher_info', 'gvid')
        generate_vouchers(new_gvid, num)
    return 'success', 200


# description: given a restaurant id (rid), return the vouchers that belong to restaurant
@voucher_bp.route('/restaurant', methods=['GET'])
@swag_from('../api_doc/voucher/restaurant.yml')
def check_voucher():
    rid = request.headers.get('rid')
    engine = db.get_engine()
    query = "SELECT gvid FROM voucher_info WHERE rid = {rid};".format(
        rid=rid
    )
    with engine.connect() as conn:
        result = conn.execute(query)
    gvid_list = tuple(set(([x[0] for x in result.fetchall()])))

    if gvid_list:
        query2 = "SELECT * FROM voucher WHERE gvid IN {list};".format(
            list=gvid_list
        )
        with engine.connect() as conn:
            result = conn.execute(query2)
        answer = result.fetchall()

        result = []
        for i in answer:
            temp = voucher_to_json(i)
            result.append(temp)
        return result, 400

    else:
        return "no voucher for restaurant", 400


# get feedback on the restaurant
@voucher_bp.route('/restaurant/feedback', methods=['GET'])
@swag_from('../api_doc/voucher/feedback.yml')
def get_feedback_ratings():
    output = check_voucher()[0]  # need rid

    rating = []
    review = []
    for i in output:
        if i['rating'] is not None:
            rating.append(i['rating'])
        if i['review'] is not None:
            review.append(i['review'])

    temp = {'rating': rating, 'review': review}
    return temp, 200


# get the customer feedback
@voucher_bp.route('/customer_feedback', methods=['PATCH'])
@swag_from('../api_doc/voucher/customer_feedback.yml')
def write_feedback_ratings():
    res_details = request.json  # need vid, and review or rating
    engine = db.get_engine()
    try:
        with engine.connect() as conn:
            sql = "UPDATE voucher SET review = '{}', rating = {} where vid = {} ;".format(
                res_details['review'], res_details['rating'], res_details['vid'])
            conn.execute(sql)
        update_rating()
        return "success", 200
    except:
        return "update error", 400


# book voucher given uid and gvid
@voucher_bp.route('/book_voucher', methods=['PATCH'])
@swag_from('../api_doc/voucher/book_voucher.yml')
def book_voucher():
    res_details = request.json  # {uid, gvid}
    if 'uid' not in res_details:
        return "please enter uid", 200
    if 'gvid' not in res_details:
        return "please enter gvid", 200

    if get_row('user', 'uid', res_details['uid'])['rid']:
        return "merchant user should not book voucher", 400

    engine = db.get_engine()
    with engine.connect() as conn:
        sql = f"SELECT * FROM voucher WHERE booked = {res_details['uid']} AND gvid = {res_details['gvid']};"
        result = conn.execute(sql)
        if result.fetchall():
            return "this user already booked", 401
    # check if the num column in voucher_info > 0:
    try:

        query = "SELECT * FROM voucher_info WHERE gvid = {};".format(
            res_details['gvid']
        )
        with engine.connect() as conn:
            result = conn.execute(query)
    except:
        return "voucher_info error", 200
    row = result.fetchone()
    if not row:
        return "invalid gvid", 200
    row_json = voucher_info_to_json(row)
    if row_json["num"] <= 0:
        return "not enough vouchers to book", 200

    # update the first null item in 'booked' column in voucher.
    query = "SELECT * FROM voucher WHERE gvid = {} and booked is null order by vid asc limit 1 ;".format(
        row_json["gvid"]
    )
    with engine.connect() as conn:
        result = conn.execute(query)
    row = result.fetchone()
    if not row:
        return "invalid gvid in voucher table", 200
    update_data = voucher_to_json(row)
    try:
        with engine.connect() as conn:
            sql = "UPDATE voucher SET booked = {} where vid = {} ;".format(
                res_details['uid'], update_data['vid'])
            conn.execute(sql)
    except:
        return "error updating", 402

    # update the num column in voucher_info to i-1.
    voucher_num_update()

    return {"uid": res_details['uid'], "code": update_data['code'], "vid": update_data['vid']}, 200


# updates the number of available coupons in voucher_info and voucher
@voucher_bp.route('/num_voucher_update', methods=['PATCH'])
@swag_from('../api_doc/voucher/num_voucher_update.yml')
def voucher_num_update():
    engine = db.get_engine()
    with engine.connect() as conn:
        result = conn.execute(f"SELECT gvid FROM voucher_info")
    row = result.fetchall()
    gvid_list = [x[0] for x in row]

    update_nums = {}
    with engine.connect() as conn:
        for i in gvid_list:
            query = "SELECT count(*) FROM voucher WHERE gvid = {} and booked is null ;".format(i)
            result = conn.execute(query)
            num = result.fetchone()[0]
            update_nums[i] = num

    # update the nums in voucher_info
    try:
        with engine.connect() as conn:
            for key, value in update_nums.items():
                sql = "UPDATE voucher_info SET num = {} where gvid = {} ;".format(
                    value, key)
                conn.execute(sql)

        return "successful update the remaining number of each voucher", 200
    except:
        return "error updating", 400


# use the voucher
@voucher_bp.route('/use_voucher', methods=['PATCH'])
@swag_from('../api_doc/voucher/use_voucher.yml')
def use():
    res_details = request.json  # {uid, code}
    engine = db.get_engine()
    rid = res_details['rid']
    code_ = res_details['code']
    with engine.connect() as conn:
        sql = f"SELECT * FROM voucher INNER JOIN voucher_info vi on voucher.gvid = vi.gvid WHERE " \
              f"code ='{code_}';"

        result = conn.execute(sql)
        row = result.fetchone()

    if not row:
        return "invalid code", 400
    elif row['used']:
        return "voucher already used", 401
    elif str(row['rid']) != str(rid):
        return "This is not a voucher for your restaurant and you are not entitled to write it off", 402
    elif not row['booked']:
        return "voucher not booked", 403

    uid = row['booked']
    try:
        with engine.connect() as conn:
            sql = f"UPDATE voucher SET used = {uid} WHERE code = '{code_}';"
            conn.execute(sql)
        return "success", 200
    except:
        return "database error", 405
