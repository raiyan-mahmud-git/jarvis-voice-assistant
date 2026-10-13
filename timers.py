"""Timers and reminders for Jarvis.

Voice examples:
    "set a timer for 5 minutes"
    "start a timer for 1 hour 30 minutes"
    "remind me to drink water in 10 minutes"
    "remind me in 2 hours to call mom"
    "how much time is left on my timer"
    "cancel all timers"
"""

import re
import threading
import time

NUMBER_WORDS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "fifteen": 15,
    "twenty": 20, "thirty": 30, "forty five": 45, "forty-five": 45, "sixty": 60,
}

UNIT_SECONDS = {"second": 1, "sec": 1, "minute": 60, "min": 60, "hour": 3600, "hr": 3600}

_WORDS_PATTERN = "|".join(
    re.escape(w) for w in sorted(NUMBER_WORDS, key=len, reverse=True)
)
_DURATION_RE = re.compile(
    rf"\b(\d+(?:\.\d+)?|{_WORDS_PATTERN})\s*(seconds?|secs?|minutes?|mins?|hours?|hrs?)\b"
)
_HALF_HOUR_RE = re.compile(r"\bhalf an? hour\b|\bhalf hour\b")


def parse_duration(text):
    """Turn '1 hour 30 minutes' into seconds. Returns None if nothing is found."""
    text = text.lower()
    total = 0

    if _HALF_HOUR_RE.search(text):
        total += 30 * 60
        text = _HALF_HOUR_RE.sub(" ", text)

    for amount, unit in _DURATION_RE.findall(text):
        value = float(amount) if amount[0].isdigit() else NUMBER_WORDS[amount]
        total += int(value * UNIT_SECONDS[unit.rstrip("s")])

    return total or None


def format_duration(seconds):
    """Turn 5430 into '1 hour, 30 minutes and 30 seconds'."""
    seconds = max(0, int(round(seconds)))
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)

    parts = []
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if secs or not parts:
        parts.append(f"{secs} second{'s' if secs != 1 else ''}")

    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " and " + parts[-1]


class TimerManager:
    """Keeps track of running timers/reminders and speaks when they finish."""

    def __init__(self, speak):
        self._speak = speak
        self._lock = threading.Lock()
        self._timers = {}
        self._next_id = 1

    def add(self, seconds, label=None):
        
        with self._lock:
            timer_id = self._next_id
            self._next_id += 1
            timer = threading.Timer(seconds, self._fire, args=(timer_id,))
            timer.daemon = True
            self._timers[timer_id] = {
                "timer": timer,
                "label": label,
                "seconds": seconds,
                "ends_at": time.time() + seconds,
            }
            timer.start()
        return timer_id

    def _fire(self, timer_id):
        with self._lock:
            info = self._timers.pop(timer_id, None)
        if info is None:  # was cancelled
            return
        if info["label"]:
            self._speak(f"Reminder: time to {info['label']}")
        else:
            self._speak(f"Time's up! Your {format_duration(info['seconds'])} timer is done.")

    def active(self):
        """Return active timers, soonest first, as (label, seconds_left)."""
        now = time.time()
        with self._lock:
            items = [(i["label"], i["ends_at"] - now) for i in self._timers.values()]
        return sorted(items, key=lambda item: item[1])

    def cancel_all(self):
        with self._lock:
            count = len(self._timers)
            for info in self._timers.values():
                info["timer"].cancel()
            self._timers.clear()
        return count


def handle_timer_command(command, manager):
    """Handle a spoken command. Returns the reply to speak, or None if it
    isn't a timer/reminder command (so main.py can try something else)."""
    c = command.lower().strip()

    # Reminders
    if c.startswith("remind me"):
        match = re.match(r"remind me to (.+) in (\S.*)$", c)
        task, when = (match.group(1), match.group(2)) if match else (None, None)
        if not match:
            match = re.match(r"remind me in (.+?) to (.+)$", c)
            if match:
                when, task = match.group(1), match.group(2)

        seconds = parse_duration(when) if when else None
        if not task or not seconds:
            return "Try saying: remind me to stretch in 10 minutes."

        task = re.sub(r"\bmy\b", "your", task)
        manager.add(seconds, label=task)
        return f"Okay, I'll remind you to {task} in {format_duration(seconds)}."

    mentions_timer = "timer" in c
    mentions_reminder = "reminder" in c
    if not (mentions_timer or mentions_reminder):
        return None

    # Cancel
    if re.search(r"\b(cancel|stop|clear|delete|remove)\b", c):
        count = manager.cancel_all()
        if count == 0:
            return "You have no active timers or reminders."
        return f"Cancelled {count} timer{'s' if count != 1 else ''} and reminders."

    # check time left
    if re.search(r"\b(how much|how many|list|left|remaining|status|check|what)\b", c):
        active = manager.active()
        if not active:
            return "You have no active timers or reminders."
        descriptions = []
        for label, left in active:
            name = f"a reminder to {label}" if label else "a timer"
            descriptions.append(f"{name} with {format_duration(left)} left")
        return "You have " + "; ".join(descriptions) + "."

    # Set a timer
    if mentions_timer:
        seconds = parse_duration(c)
        if not seconds:
            return "For how long? Try saying: set a timer for 5 minutes."
        manager.add(seconds)
        return f"Timer set for {format_duration(seconds)}."

    return None
