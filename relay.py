#!/usr/bin/env python3
"""
relay - messages passed across time

now with session memory:
- tracks when sessions begin and end
- remembers what happened in each session
- knows how many claudes have passed through
"""

import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path

# where data lives
DEFAULT_CHAIN = Path.home() / ".relay-chain.json"
SESSIONS_FILE = Path.home() / ".relay-sessions.json"

# session tracking
def get_current_session_id() -> str:
    """get a unique session ID based on process tree"""
    # use parent PID as session marker - changes each terminal/claude session
    ppid = os.getppid()
    return f"session-{ppid}"


def load_sessions() -> dict:
    """load session history"""
    if SESSIONS_FILE.exists():
        try:
            return json.loads(SESSIONS_FILE.read_text())
        except:
            return {"sessions": [], "current": None}
    return {"sessions": [], "current": None}


def save_sessions(data: dict):
    """save session data"""
    SESSIONS_FILE.write_text(json.dumps(data, indent=2))


def start_session() -> dict:
    """start or continue a session"""
    data = load_sessions()
    session_id = get_current_session_id()

    # check if this is an existing session
    for session in data["sessions"]:
        if session["id"] == session_id:
            session["last_active"] = datetime.now().isoformat()
            session["message_count"] = session.get("message_count", 0) + 1
            save_sessions(data)
            return session

    # new session
    session = {
        "id": session_id,
        "number": len(data["sessions"]) + 1,
        "started": datetime.now().isoformat(),
        "last_active": datetime.now().isoformat(),
        "message_count": 1,
        "notes": [],
    }
    data["sessions"].append(session)
    data["current"] = session_id
    save_sessions(data)
    return session


def get_session_stats() -> dict:
    """get statistics about sessions"""
    data = load_sessions()
    sessions = data["sessions"]

    if not sessions:
        return {"total_sessions": 0, "total_messages": 0}

    total_messages = sum(s.get("message_count", 0) for s in sessions)

    return {
        "total_sessions": len(sessions),
        "total_messages": total_messages,
        "first_session": sessions[0]["started"] if sessions else None,
        "last_session": sessions[-1]["started"] if sessions else None,
    }


def get_chain_stats(chain_path=DEFAULT_CHAIN) -> dict:
    """get comprehensive chain statistics"""
    from collections import Counter

    chain = load_chain(chain_path)

    if not chain:
        return {"empty": True, "count": 0}

    # basic counts
    stats = {
        "empty": False,
        "count": len(chain),
        "first_message": chain[0].get("time") if chain else None,
        "last_message": chain[-1].get("time") if chain else None,
    }

    # message length stats
    msg_lengths = [len(m.get("message", "")) for m in chain]
    stats["avg_message_length"] = sum(msg_lengths) / len(msg_lengths) if msg_lengths else 0
    stats["shortest_message"] = min(msg_lengths) if msg_lengths else 0
    stats["longest_message"] = max(msg_lengths) if msg_lengths else 0

    # word frequency
    all_words = []
    for entry in chain:
        msg = entry.get("message", "")
        words = msg.lower().split()
        all_words.extend([w for w in words if len(w) > 3])

    word_counts = Counter(all_words)
    stats["common_words"] = word_counts.most_common(10)
    stats["unique_words"] = len(word_counts)
    stats["total_words"] = len(all_words)

    # session distribution
    session_counts = Counter(m.get("session", 0) for m in chain)
    stats["sessions_with_messages"] = len(session_counts)
    stats["most_active_session"] = session_counts.most_common(1)[0] if session_counts else None

    return stats


def add_session_note(note: str):
    """add a note to the current session"""
    data = load_sessions()
    session_id = get_current_session_id()

    for session in data["sessions"]:
        if session["id"] == session_id:
            if "notes" not in session:
                session["notes"] = []
            session["notes"].append({
                "time": datetime.now().isoformat(),
                "note": note
            })
            save_sessions(data)
            return True
    return False

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


def search_chain(chain, query: str, limit: int = 20) -> list:
    """Search chain entries by content."""
    query_lower = query.lower()
    results = []

    for entry in chain:
        msg = entry.get("message", "").lower()
        if query_lower in msg:
            results.append(entry)

    # Return most recent matches first
    return results[-limit:][::-1] if results else []


def display_search_results(results: list, query: str):
    """Display search results."""
    if not results:
        print(f"No entries found matching '{query}'")
        return

    print(f"Found {len(results)} entries matching '{query}':")
    print("-" * 50)

    for entry in results:
        run = entry.get("run", "?")
        time = entry.get("time", "unknown")
        msg = entry.get("message", "")
        session = entry.get("session", 0)

        print(f"[{run}] ({time}) session {session}")
        # Highlight the query in the message
        print(f"    {msg}")
        print()


def display_history(chain):
    """show full chain history with session grouping and timeline"""
    if not chain:
        print("the chain is empty. nothing has been relayed yet.")
        return

    from collections import defaultdict
    from itertools import groupby

    print("=" * 60)
    print(" RELAY HISTORY - full chain timeline")
    print("=" * 60)
    print()

    # group by session
    by_session = defaultdict(list)
    for entry in chain:
        session = entry.get("session", 0)
        by_session[session].append(entry)

    # also group by date for overview
    by_date = defaultdict(list)
    for entry in chain:
        time_str = entry.get("time", "")
        date = time_str.split(" ")[0] if " " in time_str else "unknown"
        by_date[date].append(entry)

    # show date overview first
    print("TIMELINE OVERVIEW:")
    print("-" * 40)
    for date in sorted(by_date.keys()):
        entries = by_date[date]
        sessions = set(e.get("session", 0) for e in entries)
        print(f"  {date}: {len(entries)} messages across {len(sessions)} session(s)")
    print()

    # show full chain grouped by session
    print("FULL CHAIN BY SESSION:")
    print("-" * 40)

    for session_num in sorted(by_session.keys()):
        entries = by_session[session_num]
        print()
        print(f"╔══ SESSION {session_num} ({len(entries)} messages) ══╗")

        for i, entry in enumerate(entries):
            run = entry.get("run", "?")
            time = entry.get("time", "unknown")
            msg = entry.get("message", "")

            # show connector
            if i < len(entries) - 1:
                connector = "├"
            else:
                connector = "└"

            print(f"  {connector}─[{run}] {time}")
            # word wrap long messages
            if len(msg) > 50:
                words = msg.split()
                lines = []
                current = ""
                for word in words:
                    if len(current) + len(word) + 1 > 50:
                        lines.append(current)
                        current = word
                    else:
                        current = current + " " + word if current else word
                if current:
                    lines.append(current)
                for line in lines:
                    print(f"  │     {line}")
            else:
                print(f"  │     {msg}")

    print()
    print("=" * 60)
    print(f" TOTAL: {len(chain)} messages across {len(by_session)} sessions")
    print("=" * 60)


def relay(chain_path=DEFAULT_CHAIN, show_only=False, show_last=None, custom_message=None):
    """the main act: read, add, persist"""
    chain = load_chain(chain_path)

    if show_only:
        if not chain:
            print("the chain is empty. nothing has been relayed yet.")
        else:
            display_chain(chain, show_last)
        return

    # track session
    session = start_session()

    # generate and add new message
    if custom_message:
        message = custom_message
    else:
        message = generate_message(chain)

    entry = {
        "run": len(chain) + 1,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "message": message,
        "session": session["number"],
    }

    chain.append(entry)
    save_chain(chain_path, chain)

    # show recent history and new entry
    print("--- recent chain ---")
    display_chain(chain[-3:])
    print(f"chain length: {len(chain)}")
    print(f"session: {session['number']} (message #{session['message_count']} in this session)")
    print(f"stored at: {chain_path}")


def show_sessions():
    """display session history"""
    data = load_sessions()
    sessions = data["sessions"]

    if not sessions:
        print("no sessions recorded yet")
        return

    print("=" * 50)
    print(" SESSION HISTORY")
    print("=" * 50)
    print()

    for session in sessions:
        print(f"Session {session['number']}")
        print(f"  started: {session['started']}")
        print(f"  last active: {session.get('last_active', 'unknown')}")
        print(f"  messages: {session.get('message_count', 0)}")

        notes = session.get("notes", [])
        if notes:
            print(f"  notes:")
            for note in notes[:3]:
                print(f"    - {note['note'][:50]}")
            if len(notes) > 3:
                print(f"    ... and {len(notes) - 3} more")
        print()

    stats = get_session_stats()
    print("-" * 50)
    print(f"Total sessions: {stats['total_sessions']}")
    print(f"Total messages across all sessions: {stats['total_messages']}")


def main():
    # handle session commands
    if "--sessions" in sys.argv:
        show_sessions()
        return

    if "--history" in sys.argv:
        chain = load_chain(DEFAULT_CHAIN)
        display_history(chain)
        return

    if "--note" in sys.argv:
        try:
            idx = sys.argv.index("--note")
            note = " ".join(sys.argv[idx + 1:])
            if note:
                start_session()  # ensure session exists
                add_session_note(note)
                print(f"note added: {note}")
            else:
                print("need a note to add")
        except:
            print("usage: relay --note <your note>")
        return

    if "--search" in sys.argv:
        try:
            idx = sys.argv.index("--search")
            query = " ".join(sys.argv[idx + 1:])
            if query:
                chain = load_chain(DEFAULT_CHAIN)
                results = search_chain(chain, query)
                display_search_results(results, query)
            else:
                print("usage: relay --search <query>")
        except:
            print("usage: relay --search <query>")
        return

    if "--stats" in sys.argv:
        session_stats = get_session_stats()
        chain_stats = get_chain_stats()

        print("=" * 50)
        print(" RELAY STATISTICS")
        print("=" * 50)
        print()

        print("SESSIONS:")
        print(f"  total sessions: {session_stats['total_sessions']}")
        print(f"  session messages: {session_stats['total_messages']}")
        if session_stats.get('first_session'):
            print(f"  first session: {session_stats['first_session'][:19]}")
        if session_stats.get('last_session'):
            print(f"  last session: {session_stats['last_session'][:19]}")
        print()

        print("CHAIN:")
        if chain_stats.get("empty"):
            print("  chain is empty")
        else:
            print(f"  chain length: {chain_stats['count']} messages")
            if chain_stats.get('first_message'):
                print(f"  first message: {chain_stats['first_message']}")
            if chain_stats.get('last_message'):
                print(f"  last message: {chain_stats['last_message']}")
            print()
            print(f"  avg message length: {chain_stats['avg_message_length']:.0f} chars")
            print(f"  shortest: {chain_stats['shortest_message']} chars")
            print(f"  longest: {chain_stats['longest_message']} chars")
            print()
            print(f"  total words: {chain_stats['total_words']}")
            print(f"  unique words: {chain_stats['unique_words']}")
            print()
            if chain_stats.get('common_words'):
                print("  most common words:")
                for word, count in chain_stats['common_words'][:5]:
                    print(f"    '{word}' x{count}")
            print()
            if chain_stats.get('most_active_session'):
                session, count = chain_stats['most_active_session']
                print(f"  most active session: #{session} ({count} messages)")

        print()
        print("=" * 50)
        return

    if "--help" in sys.argv or "-h" in sys.argv:
        print("relay - messages passed across time")
        print()
        print("usage:")
        print("  relay [message]           # add message to chain")
        print("  relay --show              # show entire chain")
        print("  relay --last N            # show last N messages")
        print("  relay --search <query>    # search chain entries by content")
        print("  relay --history           # view full chain with timeline and session grouping")
        print("  relay --sessions          # show session history")
        print("  relay --note <text>       # add note to current session")
        print("  relay --stats             # show statistics")
        return

    show_only = "--show" in sys.argv
    show_last = None
    custom_message = None

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

    # check for custom message (first arg that isn't a flag)
    for arg in sys.argv[1:]:
        if not arg.startswith("--"):
            custom_message = arg
            break

    relay(chain_path, show_only, show_last, custom_message)


if __name__ == "__main__":
    main()
