from flasgger import swag_from
from flask import Blueprint, request

from helper import *

community_bp = Blueprint('community', __name__, url_prefix='/community')


# show all communities via a user
@community_bp.route("/user/<int:uid>", methods=['GET'])
@swag_from('../api_doc/community/show.yml')
def show_community(uid):
    result = []
    for i in read_all_data('community'):
        temp = community_to_json(i)
        liked_list = i[7]
        temp['flag'] = 0
        temp['user_name'] = get_row_id('user', 'uid', i[2])['user_name']
        if liked_list:
            liked_list = liked_list.split(',')
            if '' in liked_list:
                liked_list.remove('')

            if str(uid) in liked_list:
                temp['flag'] = 1
        result.append(temp)

    return result, 200


# write a new article in community
@community_bp.route("/write", methods=['PUT'])
@swag_from('../api_doc/community/write.yml')
def write_article():
    res_details = request.json  # {uid, rid, title, content, img}
    if not res_details['content']:
        return "content is empty", 400
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        engine = db.get_engine()
        with engine.connect() as conn:
            insert_sql = "insert into community (aid, rid, uid, title, content, img, release_time) " \
                         "values (null, '{}', '{}', '{}', " \
                         "'{}', '{}', '{}') ;".format(
                res_details['rid'], res_details['uid'], res_details['title'], res_details['content'],
                res_details['img'], timestamp)
            conn.execute(insert_sql)
        return res_details, 200
    except:
        return "community db put error", 400


# show a community article
@community_bp.route('/<int:aid>', methods=['GET'])
@swag_from('../api_doc/community/get.yml')
def get_article(aid):
    # basic restaurant info
    community_info = get_row_id('community', 'aid', aid)
    if community_info is None:
        return "cannot find community info", 400
    result = community_to_json(community_info)
    return result, 200


# like and dislike a community article
@community_bp.route('/like', methods=['PUT'])
@swag_from('../api_doc/community/like.yml')
def like_article():
    res_details = request.json
    aid = res_details['aid']
    uid = res_details['uid']

    # get article info
    community_info = get_row_id('community', 'aid', aid)
    likes = community_info[6]
    likes_uid_list = community_info[7]
    type_ = 'like'
    if likes_uid_list is None:
        likes_uid_list = str(uid)
    else:
        likes_uid_list = likes_uid_list.split(',')
        if '' in likes_uid_list:
            likes_uid_list.remove('')
        if str(uid) in likes_uid_list:
            type_ = 'dislike'
            likes_uid_list.remove(str(uid))
        else:
            likes_uid_list.append(str(uid))
        likes_uid_list = ','.join(likes_uid_list)

    if likes is None:
        likes = 1
    else:
        if type_ == 'like':
            likes += 1
        else:
            likes -= 1
    try:
        engine = db.get_engine()
        with engine.connect() as conn:
            update_sql = "update community set likes = '{}', likes_uid_list = '{}' where aid = '{}';".format(
                likes, likes_uid_list, aid
            )
            conn.execute(update_sql)
        return type_, 200
    except:
        return "community db put error", 401


# delete a community article
@community_bp.route('/delete', methods=['DELETE'])
@swag_from('../api_doc/community/delete.yml')
def delete_article():
    aid = request.headers.get('aid')
    uid = int(request.headers.get('uid'))

    # get article info
    community_info = get_row_id('community', 'aid', aid)
    if community_info is None:
        return "cannot find community info", 400
    if community_info[2] != uid:
        return "not the owner", 401
    try:
        engine = db.get_engine()
        with engine.connect() as conn:
            delete_sql = "delete from community where aid = '{}';".format(aid)
            conn.execute(delete_sql)
        return "delete success", 200
    except:
        return "community db put error", 402


# count the total likes of a user
@community_bp.route('/count_likes/<int:uid>', methods=['GET'])
@swag_from('../api_doc/community/count_likes.yml')
def count_likes(uid):
    result = 0
    try:
        for i in get_mutiple_rows('community', 'uid', uid):
            if i[6] is None:
                continue
            result += int(i[6])
        return str(result), 200
    except:
        return "database error", 400
