#!/bin/python3

import argparse

import irc.client
import jaraco.logging
import jaraco.stream

import client


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

    return int(input('Selection (line number): '))


def main():
    args = get_args()
    jaraco.logging.setup(args)

    # Don't crash on non UTF-8 input
    irc.client.ServerConnection.buffer_class = jaraco.stream.buffer.LenientDecodingLineBuffer

    c = client.IRCClient(args.channel, query, select)
    c.connect(args.server, args.port, args.nickname)
    c.start()


if __name__ == "__main__":
    main()
