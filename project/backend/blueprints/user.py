import numpy as np
from flasgger import swag_from
from flask import Blueprint, request, jsonify

from helper import *
from .restaurant import update_rating

user_bp = Blueprint('user', __name__, url_prefix='/user')


# get all data
@user_bp.route('/debug', methods=['GET'])
def debug():
    db_ = read_all_data('user')
    print(db_)
    return "", 200


# register user
@user_bp.route('/register', methods=['PUT'])
@swag_from('../api_doc/user/register.yml')
def register():
    res_details = request.json
    engine = db.get_engine()
    check_exist = get_row('user', 'user_name', res_details['user_name'])
    if check_exist:
        return "error: This username has been used already. Please try another username", 400

    res_details["token"] = str(uuid.uuid4())
    now = datetime.now()
    res_details["join_date"] = now.strftime("%Y/%m/%d")
    res_details["join_time"] = now.strftime("%H:%M:%S")

    try:
        with engine.connect() as conn:
            insert_sql = "insert into user (uid, user_name, role, password, join_date, join_time, preference, token, rid) " \
                         "values (null, '{}', '{}', '{}', " \
                         "'{}', '{}',  LOWER('{}') ,'{}', NULL) ;".format(
                res_details['user_name'], res_details['role'], res_details['password'], res_details['join_date'],
                res_details['join_time'], res_details['preference'], res_details['token']
            )
            conn.execute(insert_sql)
        res = {
            "token": res_details["token"],
            "user_name": res_details["user_name"],
            "role": res_details["role"],
            "preference": res_details["preference"],
            "uid": get_row('user', 'user_name', res_details['user_name'])['uid'],
            "password": res_details["password"]
        }
        return res, 200
    except:
        return "error", 401


# Post rating
@user_bp.route('/rating', methods=['POST'])
@swag_from('../api_doc/user/rating.yml')
def rating():
    res_details = request.json
    vid = res_details['vid']
    rating = res_details['rating']
    with db.get_engine().connect() as conn:
        query = f"UPDATE voucher SET rating = {rating} WHERE vid = {vid};"
        conn.execute(query)
    update_rating()
    return "success", 200


# Login user
@user_bp.route('/login', methods=['GET'])
@swag_from('../api_doc/user/login.yml')
def login():
    user_name = request.headers.get('user_name')
    password = request.headers.get('password')
    role = request.headers.get('role')
    user_data = get_row('user', 'user_name', user_name)
    if not user_data:
        return "error: Could not retrieve data from database", 500

    if user_data['rid']:
        res_info = get_row('restaurant', 'rid', user_data['rid'])
    if user_data[3] == password:
        if user_data[2] == role:
            authentication_data = {
                'token': user_data[7],
                'uid': user_data[0],
                'user_name': user_data[1],
                'preference': user_data[6].title(),
                'role': user_data[2],
                'password': user_data[3],
                'rid': user_data[8],
                'r_name': res_info['name'] if user_data['rid'] else None,
                'r_address': res_info['address'] if user_data['rid'] else None,
                'r_postcode': res_info['postcode'] if user_data['rid'] else None,
                'r_cuisine': res_info['cuisine'] if user_data['rid'] else None,
                'r_intro': res_info['intro'] if user_data['rid'] else None,
                'r_hours': res_info['operating_hours'] if user_data['rid'] else None,
                'r_fee': res_info['paid_fee'] if user_data['rid'] else None,
            }
            return authentication_data, 200

    return "error", 400


# Get info for given uid
@user_bp.route('/info', methods=['GET'])
@swag_from('../api_doc/user/info.yml')
def info():
    uid = request.headers.get('uid')
    token = request.headers.get('token')
    user_data = get_row_id('user', 'uid', uid)

    if not user_data:
        return "error: couldnt get database data.", 500

    if not token:
        return "please enter token", 400

    if user_data[7] == token:
        return_data = {
            "uid": user_data[0],
            "user_name": user_data[1],
            "role": user_data[2],
            "password": user_data[3],
            "join_date": str(user_data[4]),
            "join_time": str(user_data[5]),
            "preference": user_data[6],
            "token": user_data[7],
            "rid": user_data[8]
        }
        return return_data, 200
    return "token error", 400


# patch uid information
@user_bp.route("/patch", methods=['PATCH'])
@swag_from('../api_doc/user/patch.yml')
def patch():
    res_details = request.json
    uid = res_details['uid']
    request_keys = list(res_details.keys())
    select_row = get_row('user', 'uid', uid)
    new_name = select_row[1]
    new_password = select_row[3]
    new_preference = select_row[6]
    if 'user_name' in request_keys:
        new_name = res_details['user_name']
        if get_row('user', 'user_name', new_name):
            return "error: This username has been used already. Please try another username", 400
        res = {"user_name": new_name}
    elif 'password' in request_keys:
        new_password = res_details['password']
        res = {"password": new_password}
    elif 'preference' in request_keys:
        new_preference = res_details['preference']
        res = {"preference": new_preference.title()}
    else:
        return "error: no valid key in request", 400

    engine = db.get_engine()
    try:
        with engine.connect() as conn:
            sql = "UPDATE user SET user_name = '{}', password = '{}', preference= LOWER('{}')" \
                  "where uid = '{}' ;".format(
                new_name, new_password, new_preference, uid)
            conn.execute(sql)
        return res, 200
    except:
        return "update error", 400


# get voucher list for given uid
@user_bp.route('/voucher_list/<int:uid>', methods=['GET'])
@swag_from('../api_doc/user/voucher.yml')
def get_user_vouchers(uid):
    voucher_data = get_mutiple_rows_where_id('voucher', 'booked', uid)
    result = []
    if len(voucher_data) > 0:
        for i in voucher_data:
            if i[4]:
                continue
            voucher_info_data = get_row('voucher_info', 'gvid', i[1])
            r_name = get_row('restaurant', 'rid', voucher_info_data['rid'])['name']
            voucher_info_data_dict = voucher_info_to_json(voucher_info_data)
            voucher_data_dict = voucher_to_json(i)
            temp = {**voucher_info_data_dict, **voucher_data_dict, 'r_name': r_name}
            result.append(temp)

    return result, 200


# get the rating voucher list given uid
@user_bp.route('/rating_voucher_list/<int:uid>', methods=['GET'])
@swag_from('../api_doc/user/rating_voucher.yml')
def get_user_rating_vouchers(uid):
    voucher_data = get_mutiple_rows_where_id('voucher', 'booked', uid)
    result = []
    if len(voucher_data) > 0:
        for i in voucher_data:
            if i[4] and i[6]:
                continue
            if i[6] or not i[4]:
                continue
            voucher_info_data = get_row('voucher_info', 'gvid', i[1])
            r_name = get_row('restaurant', 'rid', voucher_info_data['rid'])['name']
            voucher_info_data_dict = voucher_info_to_json(voucher_info_data)
            voucher_data_dict = voucher_to_json(i)
            temp = {**voucher_info_data_dict, **voucher_data_dict, 'r_name': r_name}
            result.append(temp)

    return result, 200


# recommender system: download csv from database
@user_bp.route('/recommend/download_csv_from_db', methods=['GET'])
def recommend_dl():
    # {used, rating, rid}
    engine = db.get_engine()
    with engine.connect() as conn:
        query = "SELECT gvid, used, rating FROM voucher WHERE rating is not NULL;"
        result = conn.execute(query)
    row = result.fetchall()

    temp_list = []
    for i in row:
        temp = {
            'user': i[1],
            'rating': i[2],
            'rid': int(get_rid_from_gvid(i[0])[0])
        }
        temp_list.append(temp)

    user_list = get_user_list()
    restaurant_list = get_restaurant_list()
    restaurant_indices = [x[0] for x in restaurant_list]
    user_indices = [x[0] for x in user_list]

    u = len(user_list)
    r = len(restaurant_list)

    rec_array = np.zeros((u, r))
    for k in temp_list:
        row = user_indices.index(k['user'])
        col = restaurant_indices.index(k['rid'])
        rating = k['rating']
        rec_array[row][col] = rating

    ##convert array to pandas db
    rec_df = pd.DataFrame(rec_array, [x[0] for x in user_list], [x[0] for x in restaurant_list])
    rec_df.to_csv('backend/recommendation_db.csv', sep='\t')

    return "downloaded", 200


# fill the csv with recommendations
# 1. calculate similarity
# 2. calculate recommendation score
@user_bp.route('/recommend/fill_csv', methods=['GET'])
def recommend():
    csv_location = request.headers.get("location")

    try:
        location = csv_location
        rec_df = upload_db(location)
    except:
        return "cannot find csv", 400
    (u, r) = rec_df.shape

    # 1. find similarity between restaurants (item) (columns) - create dataframe and store that.
    res_similarity_matrix = np.diag(np.ones((r)))

    for i in range(0, r - 1):
        for j in range(i + 1, r):
            r1 = rec_df.iloc[:, i]
            r2 = rec_df.iloc[:, j]
            similarity = sim(r1, r2)

            res_similarity_matrix[i][j] = similarity

    similarity_matrix = res_similarity_matrix + res_similarity_matrix.transpose() - np.diag(np.ones((r)))

    # 2.calculate recommendation score
    for user in range(0, u):  # for all users
        for rest in range(0, r):  # for all restaurant
            if rec_df.iloc[user, rest] == 0:

                # 1. find the restaurants with high similarity (N = 2)
                similar_restaurants = return_largest_2_values(similarity_matrix[rest])

                # 2. get the score compared with these two restaurants
                (s_1_index, s_1_score) = similar_restaurants[0]
                (s_2_index, s_2_score) = similar_restaurants[1]
                rating_1 = rec_df.iloc[user, s_1_index]
                rating_2 = rec_df.iloc[user, s_2_index]

                if rating_1 == 0:
                    s_1_score = 0
                if rating_2 == 0:
                    s_2_score = 0

                try:
                    score = (s_1_score * int(rating_1) + s_2_score * int(rating_2)) / (s_1_score + s_2_score)
                except:
                    score = 0
                rec_df.iloc[user, rest] = score

    pd.set_option('display.max_columns', None)
    rec_df.to_csv(location, sep='\t')

    return jsonify(rec_df.to_dict(orient="index")), 200


def return_largest_2_values(itemList):
    return [(i[0], i[1]) for i in sorted(enumerate(itemList), key=lambda x: x[1])][-2:-4:-1]


def mean_of_nonZero_series(series):
    temp = series.tolist()
    return np.mean([x for x in temp if x != 0])


def sim(r1, r2):  # Pearson Correlation
    mean_r1 = r1.mean()
    mean_r2 = r2.mean()
    A = sum((r1 - mean_r1) * (r2 - mean_r2))
    B = np.sqrt(sum((r1 - mean_r1) ** 2)) * np.sqrt(sum((r2 - mean_r2) ** 2))
    return round(A / B, 2)


def get_user_vouchers_rid_only(uid):
    voucher_data = get_mutiple_rows_where_id('voucher', 'booked', uid)
    result = []
    if len(voucher_data) > 0:
        for i in voucher_data:
            voucher_info_data = get_row('voucher_info', 'gvid', i[1])
            voucher_info_data_dict = voucher_info_to_json(voucher_info_data)
            voucher_data_dict = voucher_to_json(i)
            temp = {**voucher_info_data_dict, **voucher_data_dict}
            result.append(temp)

    return list(set([x["rid"] for x in result])), 200


# get recommendation list
@user_bp.route('/recommend', methods=['GET'])
def recommend_user():
    NOR = 4  # number of recommendations

    uid = request.headers.get("uid")
    try:
        uid = int(request.headers.get("uid"))
    except:
        return "uid invalid", 401

    csv_location = request.headers.get("location")
    try:
        location = csv_location
        rec_df = upload_db(location)
    except:
        return "cannot find csv", 402

    try:
        temp = rec_df.loc[uid]
    except:
        return "cannot find uid in database", 403
    temp_restaurant_list = temp.sort_values(ascending=True)

    # order of rid (highest to lowest)
    recommendation_list = list(zip(temp_restaurant_list.index.tolist()[::-1], temp_restaurant_list.tolist()[::-1]))

    # return at least 3 star ratings:
    star_3_up_list = [x for x in recommendation_list if x[1] >= 3]

    # find out the ones that they havent been to
    uid_book_history = get_user_vouchers_rid_only(uid)[0]

    # remove booked history items from recommend list (dont want to recommend restaurants theyve been to)
    recommendations = [x for x in star_3_up_list if int(x[0]) not in uid_book_history]
    current_rid_list = [x[0] for x in recommendations]

    # if number of items > 5, then cut it to 5.
    NUM_ITEMS = len(recommendations)
    if NUM_ITEMS > NOR:
        current_rid_list = current_rid_list[0:NOR]
    # if the list of items is less than 5, then recommend general top rated restaurants
    elif NUM_ITEMS < NOR:
        ITEMS_NEED = NOR - NUM_ITEMS
        engine = db.get_engine()
        query = "select rid from restaurant where rid not in ({}) order by avg_rating desc limit {};".format(
            ','.join(current_rid_list), ITEMS_NEED)
        with engine.connect() as conn:
            result = conn.execute(query)
        added_rec_list = result.fetchall()

        current_rid_list = current_rid_list + [str(x[0]) for x in added_rec_list]

    # given current_rid_list, get the image_url, restaurant_name, introduction of restaurant
    top_N_recommendations = []
    for i in current_rid_list:
        engine = db.get_engine()
        query = "select rid, name, intro, photos from restaurant where rid = {};".format(i)
        with engine.connect() as conn:
            result = conn.execute(query)
        temp = result.fetchone()
        temp_json = {"rid": temp[0], "name": temp[1], "intro": brief_introduction(temp[2]), "image": temp[3]}
        top_N_recommendations.append(temp_json)

    return top_N_recommendations, 200


def get_rid_from_gvid(gvid):
    engine = db.get_engine()
    with engine.connect() as conn:
        query = "SELECT rid FROM voucher_info WHERE gvid = {} ;".format(gvid)
        result = conn.execute(query)
    row = result.fetchone()
    return str(row[0]), 200
