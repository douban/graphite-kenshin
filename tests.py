# coding: utf-8

from unittest import TestCase
from kenshin_api import kenshinFinder


class KenshinTests(TestCase):
    def test_conf(self):
        config = {
            'kenshin': {
                'urls': [
                    'http://host1:8080',
                    'http://host2:8080',
                ]
            }
        }

    def test_metrics(self):
        pass
