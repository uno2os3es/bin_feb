#!/data/data/com.termux/files/usr/bin/env python3
import datetime

import dh


def get_current_ymd():
    """Returns the current year, month, and day as a tuple of integers (year, month, day)."""
    today = datetime.date.today()
    return (today.year, today.month, today.day)


# Example usage:
current_year, current_month, current_day = get_current_ymd()
dh.pp(f"{current_year}-{current_month}-{current_day}=={dh.georgian_to_hijri(current_year, current_month, current_day)}")
