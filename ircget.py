#!/bin/python3

import os
import sys
import struct
import argparse
import re

import irc.client
import irc.logging


class IRCGet(irc.client.SimpleIRCClient):
    def __init__(self, channel, query_function, select_function):
        print("Initializing...")
        irc.client.SimpleIRCClient.__init__(self)
        self.received_bytes = 0
        self.remaining = 0
        self.done = False
        self.channel = channel
        self.filename = ''
        self.query_function = query_function
        self.select_function = select_function

    def on_welcome(self, connection, event):
        if irc.client.is_channel(self.channel):
            connection.join(self.channel)
            print("Joined channel")
        else:
            print(self.channel, "is not a channel.")
            self.connection.quit()

    def on_join(self, connection, event):
        # JOIN message is received when anyone joins, including us
        if not self.done:
            self.done = True
            self.search()

    def on_ctcp(self, connection, event):
        try:
            print(event.arguments[1])
            args = event.arguments[1].split()
            if args[0] != "SEND":
                return

            try:
                # Try extract text in quotes as filename
                s = event.arguments[1]
                quotes_index = [i for i in range(len(s)) if s[i] == '"']
                s = s[:quotes_index[0]] + s[quotes_index[1] + 1:]
                print(s)

                self.filename = os.path.basename(s[quotes_index[0] + 1: quotes_index[1]])

                # We've removed the quoted filename, so now we fix the address and port
                s = s.split()
                args[2] = s[1]
                args[3] = s[2]
            except:
                self.filename = os.path.basename(args[1])

            if os.path.exists(self.filename):
                print("A file named", self.filename, "already exists. Deleting.")
                os.remove(self.filename)
            self.file = open(self.filename, "wb")
            peeraddress = irc.client.ip_numstr_to_quad(args[2])
            peerport = int(args[3])
            self.dcc = self.dcc_connect(peeraddress, peerport, "raw")
        except Exception as inst:
            pass

    def on_dccmsg(self, connection, event):
        data = event.arguments[0]
        self.file.write(data)
        self.received_bytes = self.received_bytes + len(data)
        self.dcc.send_bytes(struct.pack("!I", self.received_bytes))

    def on_dcc_disconnect(self, connection, event):
        try:
            self.file.close()
        except:
            pass
        print("Received file %s (%d bytes)." % (self.filename, self.received_bytes))
        self.received_bytes = 0

        # Parse search results
        if "SearchBot" in self.filename:
            lines = self.parseSearch()
            selections = self.select_function(lines)

            self.remaining = len(selections)

            for select in selections:
                command = self.extractCommand(lines[int(select)])
                self.connection.privmsg(self.channel, command)

        else:
            print("Attempting unrar...")
            os.system("unrar e \"%s\"" % (self.filename))

            self.remaining -= 1
            if self.remaining > 0:
                print("Waiting for %d downloads to complete." % (self.remaining))
            else:
                self.search()


    def on_disconnect(self, connection, event):
        print("Disconnecting.")
        sys.exit(0)

    def search(self):
        query = self.query_function()
        self.connection.privmsg(self.channel, "@search %s" % (query))

    def parseSearch(self):
        print("Extracting zip")
        os.system("unzip %s -d /tmp/ircget" % (self.filename))
        os.system("mv /tmp/ircget/* /tmp/ircsearchresults.txt")
        with open("/tmp/ircsearchresults.txt", "r") as f:
            return [line for line in f]

    def extractCommand(self, line):
        """Strips cruft from end of line."""
        return re.search('!.*?(\.rar|\.zip|\.epub|\.mobi|\.pdf)', line).group(0)


def get_args():
    parser = argparse.ArgumentParser(
        description="Interactively search for and download files via IRC.",
    )
    parser.add_argument('server')
    parser.add_argument('nickname')
    parser.add_argument('channel')
    parser.add_argument('-p', '--port', default=6667, type=int)
    irc.logging.add_arguments(parser)
    return parser.parse_args()


def query():
    """Callback to get query"""
    return input('Search for: ')

def select(lines):
    """Callback to select lines from search results"""
    for i, line in enumerate(lines):
        print('[' + str(i) + '] ' + line)

    return input('Selections (space separated): ').split()


def main():
    args = get_args()
    irc.logging.setup(args)

    c = IRCGet(args.channel, query, select)

    # Don't crash on non UTF-8 input
    irc.client.ServerConnection.buffer_class = irc.buffer.LenientDecodingLineBuffer

    try:
        c.connect(args.server, args.port, args.nickname)
    except irc.client.ServerConnectionError as x:
        print(x)
        sys.exit(1)
    c.start()

if __name__ == "__main__":
    main()
