import unittest
import requests
import pandas as pd

class TestApi(unittest.TestCase):
    URL = "http://127.0.0.1:5000/"
    

    ### app.py ###

    def test_1_ping(self):
        resp = requests.get(self.URL + "ping")
        self.assertEqual(resp.text , "pong")
        self.assertEqual(resp.status_code, 200)
        print("Test app 1 completed.")


    ### Restaurant.py ###

    def test_restaurant_1(self):
        resp = requests.get(self.URL + "restaurant/")
        self.assertEqual(resp.status_code, 200)
        print("Test restaurant 1 completed.")

    def test_restaurant_2(self):
        rid = [1,2,3,4,5]
        for i in rid:
            resp = requests.get(self.URL + "restaurant/" + str(i))
            self.assertEqual(resp.status_code, 200)
        print("Test restaurant 2 completed.")

    #update all restaurant ratings
    def test_restaurant_3(self):
        resp = requests.put(self.URL + "restaurant/update_rating")
        self.assertEqual(resp.status_code, 200)
        print("Test restaurant 3 completed.")

    headers_1_success = {'keyword': 'cuisine', 'cuisine': 'french'}
    #search
    def test_restaurant_4(self):
        resp = requests.get(self.URL + "restaurant/search", headers = self.headers_1_success)
        self.assertEqual(resp.status_code, 200)
        print("Test restaurant 4 completed.")    

    #patch qid
    def test_restaurant_5(self):
        resp = requests.patch(self.URL + "restaurant/update_qid_question")
        self.assertEqual(resp.status_code, 200)
        print("Test restaurant 5 completed.")    

    json_answer = {"uid": 1, "qid": 8, "content": "No need to wait in line"}
    #put answer
    def test_restaurant_6(self):
        resp = requests.patch(self.URL + "restaurant/update_qid_question", json = self.json_answer)
        self.assertEqual(resp.status_code, 200)
        print("Test restaurant 6 completed.")    

    #get all question
    def test_restaurant_7(self):
        resp = requests.get(self.URL + "restaurant/get_all_question/1")
        json_len = len(resp.json()[0])
        self.assertEqual(json_len, 3)
        print("Test restaurant 7 completed.")

    #edit_info
    json_8 = {"rid": 35, "address": "142a Glebe Point Rd, Glebe NSW 2037, Australia"}
    def test_restaurant_8(self):
        resp = requests.put(self.URL + "restaurant/edit_info", json = self.json_8)
        self.assertEqual(resp.status_code, 200)
        print("Test restaurant 8 completed.")

    json_8b = {"rid": 35}
    def test_restaurant_8b(self):
        resp = requests.put(self.URL + "restaurant/edit_info", json = self.json_8b)
        self.assertEqual(resp.status_code, 401)
        print("Test restaurant 8b completed.")

    #edit menu
    json_9 = {"rid": 20, "img_url": "https://images.firsttable.net/1236x1748/public/0a549e6724/5-Course-Degustation-Oct-22-1-1-1372134_page_1.jpg", "menu_type": "main"}
    def test_restaurant_9(self):
        resp = requests.put(self.URL + "restaurant/edit_menu", json = self.json_9)
        self.assertEqual(resp.status_code, 200)
        print("Test restaurant 9 completed.")

    #advertisement
    def test_restaurant_10(self):
        resp = requests.get(self.URL + "restaurant/ad_list")
        self.assertEqual(str(resp.json()), "123.0")
        self.assertEqual(resp.status_code, 200)
        print("Test restaurant 10 completed.")

    #home advertisement
    def test_restaurant_11(self):
        resp = requests.get(self.URL + "restaurant/home_ad_list")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 4)
        print("Test restaurant 11 completed.")        


    ### User.py ###

    #register
    register_fail = {"user_name": "jack"}
    def test_user_1(self):
        resp = requests.put(self.URL + "user/register", headers = self.register_fail)
        self.assertNotEqual(resp.status_code, 200)
        print("Test user 1 completed.")        

    #recommmend
    user_recommend = {"uid":"NULL"}
    def test_user_2(self):
        resp = requests.get(self.URL + "user/recommend", headers = self.user_recommend)
        self.assertNotEqual(resp.status_code, 200)
        self.assertEqual(resp.text, "uid invalid")
        print("Test user 2 completed.")



    success_data = {
        "uid": "11",
        "token": "46dd0855-066e-44a0-ada6-9974f60f47a5"
    }

    fail_data = {
        "uid": "10",
        "token": "000"
    }

    def test_user_3(self):
        resp = requests.get(self.URL + "user/info", headers = self.success_data)
        self.assertEqual(len(resp.json()),9)
        print("Test user 1 completed.")

    def test_user_4(self):
        resp = requests.get(self.URL + "user/info", headers = self.fail_data)
        self.assertNotEqual(resp.status_code, 200)
        print("Test user 2 completed.")
    
    def test_user_5(self):
        resp = requests.get(self.URL + "user/voucher_list/0")
        self.assertNotEqual(resp.status_code, 400)
        print("Test user 3 completed.")

    def test_user_6(self):
        resp = requests.get(self.URL + "user/voucher_list/5")
        self.assertEqual(resp.status_code, 200)
        print("Test user 4 completed.")
        

    ### community.py ###

    test_community_write = {"uid": 4, "content": ""}
    def test_community_1(self):
        resp = requests.put(self.URL + "/community/write", json = self.test_community_write)
        self.assertEqual(resp.status_code, 400)
        print("Test community 1 completed.")

    #counting likes
    def test_community_2(self):
        resp = requests.get(self.URL + "/community/count_likes/5")
        self.assertEqual(str(resp.text), "0")
        self.assertEqual(resp.status_code, 200)
        print("Test community 2 completed.")



    #get article id
    def test_community_2(self):
        resp = requests.get(self.URL + "/community/2")
        self.assertEqual(resp.status_code, 200)
        print("Test community 1 completed.")

    ## voucher

    #return voucher db list
    def test_voucher_1(self):
        resp = requests.get(self.URL + "/voucher/")
        self.assertEqual(str(len(resp.json())), "101")
        self.assertEqual(resp.status_code, 200)
        print("Test voucher 1 completed.")

    #return voucher_info db list
    def test_voucher_2(self):
        resp = requests.get(self.URL + "/voucher/voucher_info")
        self.assertEqual(str(len(resp.json())), "17")
        self.assertEqual(resp.status_code, 200)
        print("Test voucher 2 completed.")

    #read nonull feedbacks
    header_voucher_3 = {"rid": "2"}
    def test_voucher_3(self):
        resp = requests.get(self.URL + "/voucher/restaurant/feedback", headers = self.header_voucher_3)
        self.assertEqual(resp.status_code, 200)
        print("Test voucher 3 completed.")

    #write feedback/ratings
    json_voucher_4 = {"vid": "NULL", "rating":12}
    def test_voucher_4(self):
        resp = requests.patch(self.URL + "/voucher/customer_feedback", json = self.json_voucher_4)
        self.assertEqual(resp.status_code, 400)
        print("Test voucher 4 completed.")
    

    ### recommender system ###


if __name__ == "__main__":
    tester = TestApi()
    tester.test_1_ping()
    tester.test_restaurant_1()
    tester.test_restaurant_2()
    tester.test_restaurant_3()
    tester.test_restaurant_4()
    tester.test_restaurant_5()
    tester.test_restaurant_6()
    tester.test_restaurant_7()
    tester.test_restaurant_8()
    tester.test_restaurant_8b()
    tester.test_restaurant_9()
    tester.test_restaurant_10()
    tester.test_restaurant_11()

    tester.test_voucher_1()
    tester.test_voucher_2()
    tester.test_voucher_3()
    tester.test_voucher_4()

    tester.test_user_1()
    tester.test_user_2()
    tester.test_user_3()
    tester.test_user_4()
    tester.test_user_5()
    tester.test_user_6()

    tester.test_community_1()
    tester.test_community_2()
    tester.test_community_2()

    print("All test complete.")