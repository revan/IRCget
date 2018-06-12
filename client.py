import os
import sys
import struct
import re
import shlex

import irc.client

import downloader
import archive_utils


class IRCClient(irc.client.SimpleIRCClient):
    def __init__(self, channel, query_function, select_function):
        print("Connecting (this can take a minute)...")
        irc.client.SimpleIRCClient.__init__(self)
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
        (command, filename, ip, port, filesize) = shlex.split(event.arguments[1])
        if command != "SEND":
            return

        self.dcc = self.dcc_connect(irc.client.ip_numstr_to_quad(ip), int(port), "raw")

        self.downloader = downloader.Downloader(filename=filename, filesize=int(filesize))

    def on_dccmsg(self, connection, event):
        data = event.arguments[0]
        self.downloader.write(data)
        self.dcc.send_bytes(struct.pack("!I", self.downloader.received_bytes))

    def on_dcc_disconnect(self, connection, event):
        self.downloader.close()

        # Parse search results
        if "SearchBot" in os.path.basename(self.downloader.filepath):
            lines = self.parseSearch(self.downloader.filepath)
            lineNumber = self.select_function(lines)

            if 0 <= lineNumber < len(lines):
                command = self.extractCommand(lines[lineNumber])
                self.connection.privmsg(self.channel, command)
        else:
            archive_utils.unrar(self.downloader.filepath)
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
