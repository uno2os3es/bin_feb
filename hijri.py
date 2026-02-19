#!/data/data/com.termux/files/usr/bin/env python3
import datetime

from dh import georgian_to_hijri, perprint


def get_current_ymd():
    """Returns the current year, month, and day as a tuple of integers (year, month, day)."""
    today = datetime.date.today()
    return (today.year, today.month, today.day)


current_year, current_month, current_day = get_current_ymd()
perprint(f"{current_year}-{current_month}-{current_day}=={georgian_to_hijri(current_year, current_month, current_day)}")
