"""Funções de utilidade comum.
"""
import calendar
from datetime import date, timedelta


def over_a_year(start: date, end: date) -> int:
    """Calculates wether or not the period from `start` to `end` comprises
    less, equal or more than a year.

    Args:
        start (date): the beginning of the interval.
        end (date): the beginning of the interval.

    Returns:
        int: -1 if less than a year, 0 if exactly a year, 1 if more than
            a year.
    """
    add_leap = 0
    if calendar.isleap(start.year) and start.month < 3:
        add_leap = add_leap + 1
    if calendar.isleap(end.year) and end.month > 3:
        add_leap = add_leap + 1
    if end - start == timedelta(days=365 + add_leap):
        return 0
    if end - start > timedelta(days=365 + add_leap):
        return 1
    return -1
