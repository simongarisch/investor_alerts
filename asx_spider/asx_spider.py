#!/home/henry/anaconda3/envs/asx_alerts/bin/python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from datetime import datetime, time
import random
import csv
import json
import mysql.connector



class AsxSpider:
    """An object that:
        -stores and refreshes a list of proxy servers and user agents
        -scrapes and returns announcement data from ASX.com"""

    def __init__(self):
        self.proxies = []
        self.proxies_updated_at = datetime.now()
        self.asx_announcements = []
        self.last_url_entry = ""
        self.cnx = None
        self.mysql_config = self.get_mysql_config()

    @classmethod
    def get_user_agent(self):
        """Return a random user agent with the fake_useragent tool"""
        ua = UserAgent().random
        return ua

    @classmethod
    def get_mysql_config(self):
        """Reads a mysql config.json file and returns the config ARGS"""

        with open('mysql_config.json', 'r') as config:
            mysql_config = json.load(config)
            return mysql_config

    def refresh_proxies(self):
        """Return a list of elite proxy servers
        from free-proxy-list.net"""

        url = "https://free-proxy-list.net/anonymous-proxy.html"

        headers = {
                "User-Agent": self.get_user_agent()
                }

        try:
            result = requests.get(url, headers=headers, timeout=5)

            if result.status_code != 200:
                print("Request status code for refresh_proxies() did not return 200")
                return False

            content = result.content.decode('utf-8')

            soup = BeautifulSoup(content, "lxml")

            data = soup.select("tbody tr")[:50]

            if data:
                for items in data:
                    proxy = ':'.join([item.text for item in items.select("td")[:2]])
                    self.proxies.append(proxy)
            else:
                # Raise an error message / admin notification
                return False

            print("INFO: Fresh proxies successfully obtained")
            self.proxies_updated_at = datetime.now()
            return True

        except requests.ConnectionError as e:
            print("OOPS!! Connection Error. Make sure you are connected to Internet. Technical Details given below.\n")
            print(str(e))
        except requests.Timeout as e:
            print("OOPS!! Timeout Error")
            print(str(e))
        except requests.RequestException as e:
            print("OOPS!! General Error")
            print(str(e))
        except KeyboardInterrupt:
            print("Someone closed the program")


        print("WARNING: Could not refresh proxies")
        return False

    def check_proxies(self):
        """Checks if proxies exist and are not stale"""

        if not self.proxies:
            return True
        elif (datetime.now() - self.proxies_updated_at).total_seconds() > 10*60:
            return True

        return False


    def check_url(self, url, cursor):
        """Checks if a url parameter has already been inserted into the db and
        returns True if it has, and False if the url does not exist in the db"""

        cursor.execute("SELECT id FROM announcements_announcement WHERE url = '%s'" % url)
        company_id = cursor.fetchone()
        if company_id:
            return True
        else:
            return False


    def parse_asx_data(self, soup):
        """Parse the soup scraped from from ASX.com"""

        raw_data = soup.find_all("td")

        i = 0
        n = 4

        if raw_data:
            cnx = mysql.connector.connect(**self.mysql_config)
            cursor = cnx.cursor(buffered=True)
            while True:
                # Sort the request data into the announcement rows
                if len(raw_data) == 0 or i == len(raw_data):
                    break
                announcement_data = raw_data[i:i+n]

                # Get the url of the announcement, and check if it has already been created in the db
                url = announcement_data[3].a["href"]
                url = int(url[-7:])

                if self.check_url(url, cursor):
                    break

                announcement_clean = self.extract_announcement_data(announcement_data, url)
                i += n
                self.asx_announcements.append(announcement_clean)
        else:
            # Raise an error message / admin notification
            return False

        # Announcement data needs to be reversed (sorted by date ascending) so that the lastest announcement is added to the db last
        # The announcement that appears first on asx.com needs to be added to db last. This allows the scraper to check for 'fresh' announcements
        self.asx_announcements.reverse()
        cursor.close()
        cnx.close()
        return True

    @classmethod
    def extract_announcement_data(self, announcement_data, url):
        """Process a list of 4 'TDs' and extracts, parses and then returns
        specific announcement data from it"""

        # Get the ASX code of the announcement
        asx_code = str(announcement_data[0].string)
        # Get the datetime of the announcement
        datetime_str = "%s %s" % (announcement_data[1].contents[0].strip() , announcement_data[1].find(class_="dates-time").string.strip())
        announcement_datetime = datetime.strptime(datetime_str, "%d/%m/%Y %I:%M %p")
        # Get the price sensitivity of the announcement
        if announcement_data[2].find(class_="pricesens") is None:
            price_sensitive = False
        else:
            price_sensitive = True
        # Get the price sensitivity of the announcement
        headline = announcement_data[3].a.contents[0].strip()
        # Get the pages string of the announcement
        pages = str(announcement_data[3].find(class_="page").string).split()[0]
        # Get the filesize string of the announcement
        filesize = announcement_data[3].find(class_="filesize").string.strip()
        announcement_clean = (
            asx_code,
            announcement_datetime,
            price_sensitive,
            headline,
            url,
            pages,
            filesize
        )
        return announcement_clean

    def get_asx_announcements(self):
        """Requests raw announcement data from ASX.com and return as soup"""


        while len(self.proxies) > 0:
            try:
                self.asx_announcements = []

                proxy_index = random.randint(0,len(self.proxies)-1)
                proxy = self.proxies[proxy_index]

                url = "https://www.asx.com.au/asx/statistics/todayAnns.do"

                proxies = {
                "https": "http://%s" % proxy
                }

                headers = {
                "User-Agent": self.get_user_agent()
                }

                result = requests.get(url, proxies=proxies, headers=headers, timeout=5)

                if result.status_code != 200:
                    print("Request status code for get_asx_announcements() did not return 200")
                    return False

                content = result.content.decode('utf-8')
                soup = BeautifulSoup(content, "lxml")
                print("Scraped ASX page with: %s" % proxy)

                no_announcements = "No company announcements have been published by ASX"
                if no_announcements in soup.select("p")[0].text:
                    print("After scanning: There have been no ASX announcements today")
                    return True

                self.parse_asx_data(soup)

                return True

            except requests.exceptions.ProxyError as e:
                del self.proxies[proxy_index]
#                print("An error occurred with the proxy: Removing the proxy and trying again...")
            except requests.exceptions.ConnectionError as e:
                del self.proxies[proxy_index]
#                print("An error occurred with the proxy: Removing the proxy and trying again...")
#                print("OOPS!! Connection Error. Make sure you are connected to Internet. Technical Details given below.\n")
#                print(str(e))
            except requests.exceptions.Timeout as e:
                print("OOPS!! Timeout Error")
                print(str(e))
            except requests.exceptions.RequestException as e:
                print("OOPS!! General Error")
                print(str(e))
            except KeyboardInterrupt:
                print("Someone closed the program")


    def get_asx_companies(self):
        """Requests a csv file from asx.com that contains a list (updated daily)
        of all listed companies (excluding exchange traded funds) and returns a
        list with companies sorted as:
            -company name
            -asx_code
            -gics industry
        """

        while len(self.proxies) > 0:
            try:
                proxy_index = random.randint(0,len(self.proxies)-1)
                proxy = self.proxies[proxy_index]

                csv_url = 'https://www.asx.com.au/asx/research/ASXListedCompanies.csv'

                proxies = {
                "https": "http://%s" % proxy
                }

                headers = {
                "User-Agent": self.get_user_agent()
                }

                result = requests.get(csv_url, proxies=proxies, headers=headers, timeout=5)

                if result.status_code != 200:
                    print("Request status code for get_asx_companies() did not return 200")
                    return False

                print(proxy)

                decoded_content = result.content.decode('utf-8')

                cr = csv.reader(decoded_content.splitlines(), delimiter=',')
                my_list = list(cr)

                # remove table header and white space
                del my_list[0:3]

                print("Successfully obtained ASX companies CSV")

                return my_list

            except requests.exceptions.ProxyError as e:
                del self.proxies[proxy_index]
                print("An error occurred with the proxy: Removing the proxy and trying again...")
            except requests.exceptions.ConnectionError as e:
                del self.proxies[proxy_index]
                print("An error occurred with the proxy: Removing the proxy and trying again...")
                print("OOPS!! Connection Error. Make sure you are connected to Internet. Technical Details given below.\n")
                print(str(e))
            except requests.exceptions.Timeout as e:
                print("OOPS!! Timeout Error")
                print(str(e))
            except requests.exceptions.RequestException as e:
                print("OOPS!! General Error")
                print(str(e))
            except KeyboardInterrupt:
                print("Someone closed the program")

    def get_asx_etfs_marketindex(self):
        """Requests data from marketwatch.com.au that contains a list of all
        exchange traded funds and returns a list with etfs sorted as:
            -company name
            -asx_code
            -industry (Default = exchange traded funds)
        """
        while len(self.proxies) > 0:
            try:
                proxy_index = random.randint(0,len(self.proxies)-1)
                proxy = self.proxies[proxy_index]

                url = "https://www.marketindex.com.au/asx-etfs"

                proxies = {
                "https": "http://%s" % proxy
                }

                headers = {
                "User-Agent": UserAgent().random
                }

                result = requests.get(url, proxies=proxies, headers=headers, timeout=5)

                if result.status_code != 200:
                    print("Request status code for get_asx_etfs() did not return 200")
                    return False

                print("successfully obtained ETF data")
                content = result.content
                soup = BeautifulSoup(content, "lxml")
                data = soup.select("tbody tr")

                exceptions = ["WLE", "SLF", "STW", "SFY", "IJR"]

                my_list = []
                if data:
                    for items in data:
                        etf_data = [item.text for item in items.select("td")[1:3]]
                        etf_data.append("Exchange Traded Fund")
                        if etf_data[1] not in exceptions:
                            my_list.append(etf_data)
                return my_list

            except requests.exceptions.ProxyError as e:
                del self.proxies[proxy_index]
                print("An error occurred with the proxy: Removing the proxy and trying again...")
            except requests.exceptions.ConnectionError as e:
                del self.proxies[proxy_index]
                print("An error occurred with the proxy: Removing the proxy and trying again...")
                print("OOPS!! Connection Error. Make sure you are connected to Internet. Technical Details given below.\n")
                print(str(e))
            except requests.exceptions.Timeout as e:
                print("OOPS!! Timeout Error")
                print(str(e))
            except requests.exceptions.RequestException as e:
                print("OOPS!! General Error")
                print(str(e))
            except KeyboardInterrupt:
                print("Someone closed the program")


    @classmethod
    def check_opening_hours(self):
        """A method to check if:
            - It is a current trading day (non weekend or public holiday)
            - The ASX announcements platform is running (7:30am AEST to 7:30pm AEST / 8:30pm dayliight savings)
        More info: ASX Listing Rules Guidance Note 14 """
        # Check for weekend day
        now = datetime.now()
        if now.weekday() > 4:
            return True
        # To do: Catch daylight savings days, Catch public holidays
        elif time(7,30) <= now.time() <= time(19,30):
            return False

        return True
