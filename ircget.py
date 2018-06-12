#!/bin/python3

import os
import sys
import struct
import argparse
import re

import irc.client
import jaraco.logging
import jaraco.stream

import downloader
import archive_utils


class IRCGet(irc.client.SimpleIRCClient):
    def __init__(self, channel, query_function, select_function):
        print("Connecting (this can take a minute)...")
        irc.client.SimpleIRCClient.__init__(self)
        self.remaining = 0
        self.channel = channel
        self.query_function = query_function
        self.select_function = select_function

    def on_welcome(self, connection, event):
        if irc.client.is_channel(self.channel):
            connection.join(self.channel)
            print("Joined channel")
            self.search()
        else:
            print(self.channel, "is not a channel.")
            self.connection.quit()

    def on_ctcp(self, connection, event):
        # Here we process SEND messages.
        # We receive the message: SEND "filename" ip port file_size
        # TODO replace with shlex
        args = event.arguments[1].split()
        if args[0] != "SEND":
            return

        # Try extract text in quotes as filename, if there are quotes
        s = event.arguments[1]
        if re.compile('".*"').search(s) is not None:
            quotes_index = [i for i in range(len(s)) if s[i] == '"']
            filename = os.path.basename(s[quotes_index[0] + 1: quotes_index[1]])

            s = s[:quotes_index[0]] + s[quotes_index[1] + 1:]

            # We've removed the quoted filename, so now we fix the address and port
            s = s.split()
            args[2] = s[1]
            args[3] = s[2]
            print("file size: %s" % s[3])
        else:
            filename = os.path.basename(args[1])

        peeraddress = irc.client.ip_numstr_to_quad(args[2])
        peerport = int(args[3])
        self.dcc = self.dcc_connect(peeraddress, peerport, "raw")

        self.downloader = downloader.Downloader(filename=filename)

    def on_dccmsg(self, connection, event):
        data = event.arguments[0]
        self.downloader.write(data)
        self.dcc.send_bytes(struct.pack("!I", self.downloader.received_bytes))

    def on_dcc_disconnect(self, connection, event):
        self.downloader.close()

        # Parse search results
        if "SearchBot" in os.path.basename(self.downloader.filepath):
            lines = self.parseSearch(self.downloader.filepath)
            selections = self.select_function(lines)

            self.remaining = len(selections)

            for select in selections:
                line = int(select)
                if 0 <= line < len(lines):
                    command = self.extractCommand(lines[line])
                    self.connection.privmsg(self.channel, command)

        else:
            archive_utils.unrar(self.downloader.filepath)

            self.remaining -= 1
            if self.remaining > 0:
                print("Still waiting for %d downloads to complete." % (self.remaining))
            else:
                self.search()


    def on_disconnect(self, connection, event):
        print("Disconnecting.")
        sys.exit(0)

    def search(self):
        query = self.query_function()
        self.connection.privmsg(self.channel, "@search %s" % (query))

    def parseSearch(self, filepath):
        searchResultsPath = archive_utils.unzip(filepath)

        with open(searchResultsPath, "r") as f:
            return [line for line in f]

    def extractCommand(self, line):
        """Strips cruft from end of line."""
        return re.search('!.*?(\.rar|\.zip|\.epub|\.mobi|\.pdf|\..{3})', line).group(0)


def get_args():
    # TODO replace with saner arg parsing
    parser = argparse.ArgumentParser(
        description="Interactively search for and download files via IRC.",
    )
    parser.add_argument('server')
    parser.add_argument('nickname')
    parser.add_argument('channel')
    parser.add_argument('-p', '--port', default=6667, type=int)
    jaraco.logging.add_arguments(parser)
    return parser.parse_args()


def query():
    """Callback to get query"""
    return input('Search for (ctrl+c to exit): ')

def select(lines):
    """Callback to select lines from search results"""
    for i, line in enumerate(lines):
        print('[' + str(i) + '] ' + line)

    return input('Selections (space separated): ').split()


def main():
    args = get_args()
    jaraco.logging.setup(args)

    c = IRCGet(args.channel, query, select)

    # Don't crash on non UTF-8 input
    irc.client.ServerConnection.buffer_class = jaraco.stream.buffer.LenientDecodingLineBuffer

    c.connect(args.server, args.port, args.nickname)
    c.start()

if __name__ == "__main__":
    main()
