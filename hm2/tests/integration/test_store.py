from time import sleep
import unittest
from pathlib import Path
import os
import sys
import hashlib
import datetime
import json

path = str(Path(os.path.abspath(__file__)).parent.parent.parent)
sys.path.insert(1, path)
from store import Store
from tests.integration.test import cases
import api

class TestStore(unittest.TestCase):
    def setUp(self):
        self.store = Store()

    def test_set_simlpe_value(self):
        key = "simple key"
        self.store.set(key=key, value=42, timeout=60)
        self.assertEqual(int(self.store.get(key=key)), 42)

    def test_timeout(self):
        key = "key"
        self.store.set(key=key, value=12, timeout=3)
        self.assertEqual(int(self.store.get(key=key)), 12)
        sleep(3)
        self.assertEqual(self.store.get(key=key), None)

    def test_cache_empty_key(self):
        key = "don't exist"
        self.assertEqual(self.store.cache_get(key=key), None)

    def test_cache_positive(self):
        key = "another key"
        self.store.cache_set(key=key, value=8, timeout=60)
        self.assertEqual(int(self.store.cache_get(key=key)), 8)

class TestStoreForwardAPI(unittest.TestCase):
    def setUp(self):
        self.store = Store()

    @cases([
        ({"client_ids": [1, 2, 3], "date": "24.07.2022"}, {'1': ['computer science'], '2': ['programming'], '3': ['otus', 'python3']}),
    ])
    def test_valid_interest(self, arguments, rigth_response):
        self.store.set(key="i:1", value=json.dumps(["computer science"]), timeout=60)
        self.store.set(key="i:2", value=json.dumps(["programming"]), timeout=60)
        self.store.set(key="i:3", value=json.dumps(["otus", "python3"]), timeout=60)

        request = {"account": "horns&hoofs", "login": "admin", "method": "clients_interests", "arguments": arguments}
        request["token"] = hashlib.sha512((datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT).encode()).hexdigest()
        response, code = api.method_handler({"body": request, "headers": {}}, {}, self.store)
        self.assertEqual(rigth_response, response)
        self.assertEqual(200, code)



if __name__ == "__main__":
    unittest.main()
