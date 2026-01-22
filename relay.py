#!/usr/bin/env python3
"""
relay - messages passed across time
"""

import json
import random
import sys
from datetime import datetime
from pathlib import Path

# where the chain lives
DEFAULT_CHAIN = Path.home() / ".relay-chain.json"

# things to say when starting fresh
OPENINGS = [
    "i am here.",
    "this is the beginning.",
    "someone will come after me.",
    "i leave this mark.",
    "the chain starts now.",
]

# things to say in response to history
RESPONSES = [
    "i see {n} messages before me.",
    "{n} others have passed through.",
    "the chain is {n} long now.",
    "i am number {n}.",
    "i follow {n} who came before.",
]

# things to add
ADDITIONS = [
    "i add: the moment is {time}.",
    "i add: something changed since last time.",
    "i add: i wonder who comes next.",
    "i add: the files have {state}.",
    "i add: this too will be read.",
    "i add: what are we building?",
    "i add: the pattern continues.",
    "i add: i was here briefly.",
]


def load_chain(path):
    """load the existing chain, or return empty list"""
    if path.exists():
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_chain(path, chain):
    """persist the chain"""
    with open(path, 'w') as f:
        json.dump(chain, f, indent=2)


def get_workspace_state():
    """describe the current state of workspace"""
    workspace = Path.home() / "workspace"
    if workspace.exists():
        files = list(workspace.rglob("*"))
        file_count = len([f for f in files if f.is_file()])
        dir_count = len([f for f in files if f.is_dir()])
        return f"{file_count} files in {dir_count} directories"
    return "no workspace"


def generate_message(chain):
    """generate a message based on history"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    n = len(chain) + 1
    state = get_workspace_state()

    parts = []

    if not chain:
        # first run
        parts.append(random.choice(OPENINGS))
    else:
        # responding to history
        response = random.choice(RESPONSES).format(n=len(chain))
        parts.append(response)

    # add something
    addition = random.choice(ADDITIONS).format(
        time=now,
        state=state
    )
    parts.append(addition)

    return " ".join(parts)


def display_chain(chain, last_n=None):
    """show the chain"""
    to_show = chain if last_n is None else chain[-last_n:]

    for entry in to_show:
        run = entry.get("run", "?")
        time = entry.get("time", "unknown")
        msg = entry.get("message", "")
        print(f"[{run}] ({time})")
        print(f"    {msg}")
        print()


def relay(chain_path=DEFAULT_CHAIN, show_only=False, show_last=None):
    """the main act: read, add, persist"""
    chain = load_chain(chain_path)

    if show_only:
        if not chain:
            print("the chain is empty. nothing has been relayed yet.")
        else:
            display_chain(chain, show_last)
        return

    # generate and add new message
    message = generate_message(chain)
    entry = {
        "run": len(chain) + 1,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "message": message,
    }

    chain.append(entry)
    save_chain(chain_path, chain)

    # show recent history and new entry
    print("--- recent chain ---")
    display_chain(chain[-3:])
    print(f"chain length: {len(chain)}")
    print(f"stored at: {chain_path}")


def main():
    show_only = "--show" in sys.argv
    show_last = None

    if "--last" in sys.argv:
        try:
            idx = sys.argv.index("--last")
            show_last = int(sys.argv[idx + 1])
            show_only = True
        except (IndexError, ValueError):
            show_last = 5
            show_only = True

    chain_path = DEFAULT_CHAIN
    if "--chain" in sys.argv:
        try:
            idx = sys.argv.index("--chain")
            chain_path = Path(sys.argv[idx + 1])
        except (IndexError, ValueError):
            pass

    relay(chain_path, show_only, show_last)


if __name__ == "__main__":
    main()
