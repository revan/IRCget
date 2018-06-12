import os
import threading
import unittest

import irc.client
import jaraco.stream

import client
from test_secrets import ADDRESS, CHANNEL, NICK, QUERY, SELECTION


class TestFull(unittest.TestCase):

    def setUp(self):
        irc.client.ServerConnection.buffer_class = jaraco.stream.buffer.LenientDecodingLineBuffer


    def test_Full(self):
        old_ls = os.listdir('.')

        def runClient():
            c = client.IRCClient(CHANNEL, lambda: QUERY, lambda _: SELECTION, loop=False)
            c.connect(ADDRESS, 6667, NICK)
            c.start()

        t = threading.Thread(target=runClient)
        t.start()
        t.join()

        new_ls = os.listdir('.')

        self.assertLess(len(old_ls), len(new_ls), 'New file should be present')


if __name__ == '__main__':
    unittest.main()
