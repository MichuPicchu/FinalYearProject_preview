import unittest
import requests
import pandas as pd

class TestApi(unittest.TestCase):
    URL = "http://127.0.0.1:5000/"
    

    ## download
    
    def test_download(self):
        resp = requests.get(self.URL + "user/recommend/download_csv_from_db")
        self.assertEqual(resp.status_code, 200)    
        print("Test 1 completed.")

    
    ## fill_csv

    test_data_1 = {
        "location" : "backend/recommendation_db_tests/recommendation_db_example_1_edit.csv"
    }

    def test_recommend_1_a(self):   #row of nonchange
        resp = requests.get(self.URL + "user/recommend/fill_csv", headers = self.test_data_1)
        res = pd.read_csv(self.test_data_1["location"], sep=',', header='infer', index_col=0)
        expected_result = ['2', '5', '2', '0.0', '0.0', '2.0', '0', '0', '0', '0', '1.0', '1.0', '0', '0', '0', '0', '0', '0', '0', '0', '1']
        self.assertEqual(res.index[1].split('\t'), expected_result)
        self.assertEqual(resp.status_code, 200)    
        print("Test 1a completed.")
    def test_recommend_1_b(self):   #specific change
        resp = requests.get(self.URL + "user/recommend/fill_csv", headers = self.test_data_1)
        res = pd.read_csv(self.test_data_1["location"], sep=',', header='infer', index_col=0)
        output = res.index[5].split('\t')
        self.assertEqual(round(float(output[10]),2), 2.41)
        print("Test 1b completed.")
    def test_recommend_1_c(self):   #shape
        resp = requests.get(self.URL + "user/recommend/fill_csv", headers = self.test_data_1)
        res = pd.read_csv(self.test_data_1["location"], sep=',', header='infer', index_col=0)
        expected_rows = 23      #rows
        expected_cols = 51      #columns
        self.assertEqual(len(res.index), expected_rows)
        self.assertEqual(len(res.index[0]), expected_cols)
        print("Test 1c completed.")         

    test_data_2 = {
        "location" : "backend/recommendation_db_tests/recommendation_db_demo_example_edit.csv"
    }

    def test_recommend_2_a(self):   #row of nonchange
        resp = requests.get(self.URL + "user/recommend/fill_csv", headers = self.test_data_2)
        res = pd.read_csv(self.test_data_2["location"], sep=',', header='infer', index_col=0)
        expected_result = ['1', '2.0', '3', '2.0', '4.0', '2.0', '2.0', '3', '2.0', '2', '2.0', '2.0', '2.0', '5.0', '2.0']
        self.assertEqual(res.index[0].split('\t'), expected_result)
        print("Test 2a completed.")
    def test_recommend_2_b(self):   #specific change
        resp = requests.get(self.URL + "user/recommend/fill_csv", headers = self.test_data_2)
        res = pd.read_csv(self.test_data_2["location"], sep=',', header='infer', index_col=0)
        output = res.index[6].split('\t')
        self.assertEqual(round(float(output[14]),2), 2.18)
        print("Test 2b completed.")
    def test_recommend_2_c(self):   #shape
        resp = requests.get(self.URL + "user/recommend/fill_csv", headers = self.test_data_2)
        res = pd.read_csv(self.test_data_2["location"], sep=',', header='infer', index_col=0)
        expected_rows = 22      #rows
        expected_cols = 51      #columns
        self.assertEqual(len(res.index), expected_rows)
        self.assertEqual(len(res.index[0]), expected_cols)
        print("Test 2c completed.")  

    ## recommend list

    recommend_headers_1 = {"location": "backend/recommendation_db_tests/recommendation_db_demo.csv", "uid" : "27"}
    def test_recommend_list_1(self):
        resp = requests.get(self.URL + "user/recommend", headers = self.recommend_headers_1)
        self.assertEqual(resp.json()[0]['name'], 'glass brasserie')     #correct rid recommendation
        self.assertEqual(str(resp.json()[0]['rid']), '19')
        print("Test recommend_list 1 completed.") 

    recommend_headers_2 = {"location": "backend/recommendation_db_tests/recommendation_db_demo.csv", "uid" : "1"}
    def test_recommend_list_2(self):
        resp = requests.get(self.URL + "user/recommend", headers = self.recommend_headers_2)
        # print(resp.json()[1])
        self.assertEqual(str(resp.json()[1]['rid']), '7')       #not rid4 since he has already been to that restaurant
        print("Test recommend_list 2 completed.")

    recommend_headers_3 = {"location": "backend/recommendation_db_tests/recommendation_db_demo.csv", "uid" : "3"}
    def test_recommend_list_3(self):
        resp = requests.get(self.URL + "user/recommend", headers = self.recommend_headers_3)
        self.assertEqual(resp.status_code, 403)     #uid doesnt exist in db
        print("Test recommend_list 3 completed.") 

    recommend_headers_4 = {"location": "backend/recommendation_db_tests/recommendation_db_demo.csv", "uid" : "9"}
    def test_recommend_list_4(self):
        resp = requests.get(self.URL + "user/recommend", headers = self.recommend_headers_4)
        # print(resp.json())
        self.assertEqual(resp.status_code, 403)     #uid doesnt exist in db
        print("Test recommend_list 4 completed.") 

    recommend_headers_5 = {"location": "backend/recommendation_db_tests/recommendation_db_demo.csv", "uid" : "10"}
    def test_recommend_list_5(self):
        resp = requests.get(self.URL + "user/recommend", headers = self.recommend_headers_5)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(str(resp.json()[0]['rid']), '19')
        self.assertEqual(str(resp.json()[1]['rid']), '18')
        self.assertEqual(str(resp.json()[2]['rid']), '6')
        self.assertEqual(str(resp.json()[3]['rid']), '2')
        print("Test recommend_list 5 completed.") 


if __name__ == "__main__":
    tester = TestApi()
    
    tester.test_download()
    tester.test_recommend_1_a()
    tester.test_recommend_1_b()
    tester.test_recommend_1_c()

    tester.test_recommend_2_a()
    tester.test_recommend_2_b()
    tester.test_recommend_2_c()

    tester.test_recommend_list_1()
    tester.test_recommend_list_2()
    tester.test_recommend_list_3()
    tester.test_recommend_list_4()
    tester.test_recommend_list_5()

    print("All test complete.")