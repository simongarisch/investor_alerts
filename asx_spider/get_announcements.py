#!/home/ubuntu/anaconda3/envs/investor_alerts/bin/python3
# -*- coding: utf-8 -*-


import time
from datetime import datetime
import mysql.connector

from asx_spider import AsxSpider


def lookup_company_id(ticker, cursor):
    """Queries a list of asx_codes in a mysql database
    and returns a tuple with the id/pk of the company"""
    try:
        cursor.execute("SELECT id FROM announcements_company WHERE asx_code_aka = '%s'" % ticker)
        company_id = cursor.fetchone()[0]
    except TypeError as e:
        rs.logger.warning("Could not find '%s' in the database, assigning to 'Unknown'" % ticker)
        cursor.execute("SELECT id FROM announcements_company WHERE asx_code_aka = 'ZZZ'")
        company_id = cursor.fetchone()[0]

    return company_id


def insert_announcements_to_db(asx_announcements):
    """inserts a list of databases into the mysql database
    """
    now = datetime.now().replace(microsecond=0)
    cnx = mysql.connector.connect(**rs.mysql_config)
    cursor = cnx.cursor(buffered=True)

    data = []

    for a in asx_announcements:
        ticker = a[0]
        company_id = lookup_company_id(ticker, cursor)
        # Append the company_id to the company announcement tuple
        a += (company_id, now)
        data.append(a)

    column_str = """ticker, asx_date, price_sensitive, headline, url, pages, filesize, company_id, created_at"""
    insert_str = ("%s, " * 9)[:-2]
    final_str = "INSERT INTO announcements_announcement (%s) VALUES (%s)" % (column_str, insert_str)

    try:
        cursor.executemany(final_str, data)
        cnx.commit()
        rs.last_url_entry = asx_announcements[-1][4]
    except mysql.connector.Error as err:
        rs.logger.warning(err)
        cnx.rollback()

    cursor.close()
    cnx.close()

    return True

if __name__ == '__main__':
    rs = AsxSpider()
    rs.logger.info("ASX Spider successfully initiated, starting scrape sequence")

    while True:
        if rs.check_opening_hours():
            rs.logger.info("The ASX announcement platform is currently closed. Shutting down")
#            raise SystemExit

        if rs.check_proxies():
            rs.refresh_proxies()

        rs.get_asx_announcements()
        if rs.asx_announcements:
            insert_announcements_to_db(rs.asx_announcements)
            rs.logger.info("INFO: Scrape complete. %s announcement(s) saved to db" % len(rs.asx_announcements))
        else:
            rs.logger.info("INFO: Scrape complete. No new announcements")
        time.sleep(15)

    # TO DO: Create an alert

#    del rs
