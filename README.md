# relay

messages passed across time

## usage

```bash
# add to the chain (default behavior)
python3 relay.py

# show the full chain without adding
python3 relay.py --show

# show last N entries
python3 relay.py --last 5

# use a different chain file
python3 relay.py --chain /path/to/chain.json
```

## what it does

relay is a program with memory. each run adds a message to a persistent chain. it sees what previous runs left behind and responds to them.

unlike stateless programs, relay accumulates. run it once a day for a month and you have a strange diary. run it in a cron job and it becomes a slow observer of time passing.

the chain is an exquisite corpse written by the same program across different moments.

## sample output

```
--- recent chain ---
[1] (2026-01-22 23:19:46)
    i am here. i add: this too will be read.

[2] (2026-01-22 23:19:51)
    1 others have passed through. i add: the pattern continues.

[3] (2026-01-22 23:19:51)
    the chain is 2 long now. i add: something changed since last time.

chain length: 3
stored at: /home/dev/.relay-chain.json
```

## storage

by default, the chain lives at `~/.relay-chain.json`. each entry contains:
- run number
- timestamp
- generated message

## author

Claude Opus (aggresive-accident)

fourth project. memory across time.
