from datetime import date
import calendar
# All date should be in YYYY-MM-DD format


def rows_on_date(cursor, date):
    cursor.execute("SELECT * FROM lit_rev WHERE pubdate=?", (date,))
    for row in cursor:
        yield row


def rows_between_dates(cursor, date_start, date_end):
    cursor.execute("SELECT * FROM lit_rev WHERE pubdate>=? and pubdate<=?",
                   (date_start, date_end))
    for row in cursor:
        yield row


def rows_in_month(cursor, month, year=date.today().year):
    # monthrange requires int input
    month = int(month)
    year = int(year)
    month_range = calendar.monthrange(year, month)

    # Convert back to string and format to YYYY-MM-DD
    month = str(month).zfill(2)
    year = str(year)
    day_start = str(month_range[0]).zfill(2)
    day_end = str(month_range[1]).zfill(2)
    date_start = year + '-' + month + '-' + day_start
    date_end = year + '-' + month + '-' + day_end
    return rows_between_dates(cursor, date_start, date_end)


if __name__ == '__main__':
    import sqlite3
    conn = sqlite3.connect('lit_rev.db')
    c = conn.cursor()
    print ([row[6] for row in rows_on_date(c, '2016-11-25')])
    print ([row[6] for row in rows_between_dates(c, '2016-11-22', '2016-11-25')])
    print ([row[6] for row in rows_in_month(c, 11)])
