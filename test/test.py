import unittest

import os
import tempfile
import requests
import http.server
import threading
import datetime

from nordpool import elspot
from nordpool_db import NordpoolDb

import http.server # Our http server handler for http requests
from urllib.parse import quote

PORT = 9000

class StoppableHTTPServerRequestHandler(http.server.SimpleHTTPRequestHandler):
    def parse_path_from_uri(self, uri):
        return quote(self.path, safe='/?&=')

    def do_GET(self):
        file_path = "test/httpd%s" % self.parse_path_from_uri(self.path)
        document_content = None
        if os.path.isfile(file_path):
            f = open(file_path)
            document_content = f.read()
            f.close()

        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(bytes('Hello world!\n', 'utf-8'))
        elif document_content is not None:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(bytes(document_content, 'utf-8'))
        else:
            self.send_error(404)

class StoppableHTTPServer(http.server.HTTPServer):
    def run(self):
        try:
            self.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            # Clean-up server (close socket, etc.)
            self.server_close()

class TestGeneral(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.server = StoppableHTTPServer(("127.0.0.1", 4141), StoppableHTTPServerRequestHandler)
        self.thread = threading.Thread(None, self.server.run)
        self.thread.start()

    @classmethod
    def tearDownClass(self):
        self.server.shutdown()
        self.thread.join()

    def test_create_and_simple_unit_tests(self):
        tmp_handle, tmp_name = tempfile.mkstemp(prefix='npdb_test_')
        os.close(tmp_handle)

        npdb = NordpoolDb(tmp_name)

        # datetime_to_sqlstring()
        test_cases = [
            [datetime.datetime(1971, 9, 11), '1971-09-11 00:00:00'],
            [datetime.datetime(2034, 12, 1, 3, 4, 5), '2034-12-01 03:04:05'],
        ]

        for this_case in test_cases:
            self.assertEqual(npdb.datetime_to_sqlstring(this_case[0]), this_case[1])

        del npdb

        self.assertTrue(os.path.exists(tmp_name))

        os.remove(tmp_name)

    def test_httpd_alive(self):
        response = requests.get("http://localhost:4141/")
        response_content = response.content

        self.assertEqual(response_content.decode('utf-8'), 'Hello world!\n', msg="httpd server does not respond")

    def test_correct_currency(self):
        prices_spot = elspot.Prices()
        prices_spot.API_URL = 'http://localhost:4141/%i'

        result = prices_spot.hourly(areas=['FI'], end_date=datetime.datetime(2022,11,3))
        self.assertEqual(result['currency'], 'EUR')
    
    def test_store_and_retrieve_prices(self):
        prices_spot = elspot.Prices()
        prices_spot.API_URL = 'http://localhost:4141/%i'

        tmp_handle, tmp_name = tempfile.mkstemp(prefix='npdb_test_')
        os.close(tmp_handle)

        npdb = NordpoolDb(tmp_name)

        npdb.update_data(prices_spot.hourly(areas=['FI'], end_date=datetime.datetime(2022,11,3)))
        npdb.update_data(prices_spot.hourly(areas=['FI'], end_date=datetime.datetime(2022,11,2)))

        test_cases = [
            [datetime.datetime(2022, 11, 2, 1, 20, 0), 100.9],
            [datetime.datetime(2022, 11, 2, 1, 0, 0), 100.9],
            [datetime.datetime(2022, 11, 3, 1, 20, 0), 29.24],
            [datetime.datetime(2022, 11, 3, 1, 0, 0), 29.24],
            [datetime.datetime(2022, 11, 1, 12, 0, 0), None],
        ]

        for this_case in test_cases:
            self.assertEqual(npdb.get_price_value('FI', this_case[0]), this_case[1])

        os.remove(tmp_name)

if __name__ == '__main__':
    unittest.main()
