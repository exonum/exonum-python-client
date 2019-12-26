# pylint: disable=missing-docstring, protected-access
# type: ignore

import unittest
from unittest.mock import patch, Mock
import random

random.seed(0)

from exonum_client.client import ExonumClient, Subscriber
from .testing_utils import *


class TestExonumClient(unittest.TestCase):
    # This test case replaces the get and post functions from the Exonum client with the mock one.
    # Thus testing of HTTP interacting could be done without actual Exonum client:

    def setUp(self):
        self.client = ExonumClient(
            hostname=EXONUM_IP, public_api_port=EXONUM_PUBLIC_PORT, private_api_port=EXONUM_PRIVATE_PORT
        )


# Subscriber tests
class TestSubscriber(unittest.TestCase):
    def setUp(self):
        address = "address"
        port = 8080
        self.subscriber = Subscriber(address, port)

    def test_set_handler(self):
        result = "some result"

        def handler(data):
            return data

        self.subscriber.set_handler(handler)

        self.assertEqual(self.subscriber._handler(result), result)

    def test_wait_for_new_event(self):
        self.subscriber._ws_client = Mock()

        self.assertEqual(self.subscriber.wait_for_new_event(), None)
