import unittest
import requests
import pymongo

APP_URL = 'http://localhost:8000'
COLLECTION = pymongo.MongoClient("mongodb://localhost:27016/").get_database("CapstoneDB")["scrapy_config"]

class UpdateFrequencyTest(unittest.TestCase):
    def test_update_frequency(self, n=150):
        responses: list[requests.Response] = []
        condition = {'_id': {'$regex': r'update_freq_test\d'}}
        COLLECTION.delete_many(condition)

        for i in range(n):
            responses.append(requests.put(
                APP_URL + f'/scrapy_config?municipality=update_freq_test{i}',
                headers={'accept': 'application/json', 'Content-Type': 'application/json'},
                json={'allowed_domains': ['UpdateFrequencyTest']}
            ))
        
        for r in responses:
            self.assertEqual(r.status_code, 200)
        
        responses = []
        configs = list(COLLECTION.find(condition))
        
        for c in configs:
            self.assertEqual(len(c['update_at']), 2)
            for i in [0,1]:
                self.assertGreaterEqual(c['update_at'][i], 0)
                self.assertLessEqual(c['update_at'][i], 365)

        COLLECTION.delete_many(condition)
        
if __name__ == '__main__':
    unittest.main()