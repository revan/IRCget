#IRCget

Tool for downloading files from an IRC server.
Far from polished, but working.

Accepts server address, nickname, and channel from command line args. Prompts user for query, parses search result, prompts user for selections from results, and downloads those.

IRC is a messy standard so the string parsing may break between servers. 

Also be advised this accepts all files and unzips / unrars them blindly.

Requires:

```
irc (python library)
unzip
unrar
```

TODO:

-	Concurrent downloads, or enforce serial downloads across hosts
-	`curses` UI
