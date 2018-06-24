#!/home/henry/anaconda3/envs/asx_alerts/bin/python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from datetime import datetime, time
import random
import time as t



class AsxSpider:
    """An object that:
        -stores and refreshes a list of proxy servers and user agents
        -scrapes and returns announcement data from ASX.com"""
    
    def __init__(self):
        self.proxies = []
        self.updated_at = datetime.now()
     
    def get_user_agent(self):
        """Return a random user agent with the fake_useragent tool"""
        ua = UserAgent().random
        
        return ua
    
    def refresh_proxies(self):
        """Return a list of elite proxy servers 
        from free-proxy-list.net"""
        
        url = "https://free-proxy-list.net/"
        
        headers = {
                "User-Agent": self.get_user_agent()
                }
        
        try:
            print("Attempting to refresh proxies")
            result = requests.get(url, headers=headers, timeout=5)
        
            if result.status_code != 200:
                print("Request status code for refresh_proxies() did not return 200")
                return False
            
            content = result.content
            
            soup = BeautifulSoup(content, "lxml")
        
            proxy_list = []
            
            data = soup.select("tbody tr")[:50] 
            
            if data:
                for items in data:
                    proxy = ':'.join([item.text for item in items.select("td")[:2]])
                    proxy_list.append(proxy)
            else:
                # Raise an error message / admin notification
                return False
            
            print("Fresh proxies successfully obtained")
            self.updated_at = datetime.now()
            self.proxies = proxy_list
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
        
        
        
        return False
    
    def check_proxies(self):
        """Checks if proxies exist and are not stale"""
        
        if len(self.proxies) == 0:        
            return True
        elif (self.updated_at - datetime.now()).total_seconds() > 10*60:
            return True
        
        return False
    
    
    def parse_asx_data(self, soup):
        """Parse the soup scraped from from ASX.com"""
        
        
        raw_data = soup.find_all("td")
        
        base_url = "https://www.asx.com.au"
        last_url_entry = "Some url" # Lookup from database
        
        i = 0
        n = 4
        scanning = True
        base_url = "https://www.asx.com.au"
        last_url_entry = "Some url" # Lookup from database
        self.asx_announcements = []
         
        if raw_data:
            while scanning:
                # Sort the request data into the announcement rows
                if len(raw_data) == 0 or i == len(raw_data):
                    break
                announcement_data = raw_data[i:i+n]
                # Get the url of the announcement, and check if it has already been created in the db
                url = base_url + announcement_data[3].a["href"]
                if url == last_url_entry:
                    break
                # Get the ASX code of the announcement
                asx_code = announcement_data[0].string
                # Get the datetime of the announcement
                date = announcement_data[1].contents[0].strip()
                time = announcement_data[1].find(class_="dates-time").string.strip()
                datetime_str = "%s %s" % (date , time)
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
                
                i += n
                self.asx_announcements.append(announcement_clean)
        else:
            # Raise an error message / admin notification
            return False
            
        # Announcement data needs to be reversed (sorted by date ascending) so that the lastest announcement is added to the db last
        # The announcement that appears first on asx.com needs to be added to db last. This allows the scraper to check for 'fresh' announcements
        self.asx_announcements.reverse()
        return
    

    def get_asx_announcements(self):
        """Requests raw announcement data from ASX.com and return as soup"""
    
            
        url = "https://www.asx.com.au/asx/statistics/todayAnns.do"
        
        
        while True:
            try:
                proxy_index = random.randint(0,len(self.proxies)-1)
                proxy = self.proxies[proxy_index]
                
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
                
                content = result.content
                
                soup = BeautifulSoup(content, "lxml")
                
                print("successfully obtained announcement data")
                
                self.parse_asx_data(soup)
        
                return
                
                break
                    
            except requests.exceptions.ProxyError as e:
                del(self.proxies[proxy_index])
                print("An error occurred with the proxy: Removing the proxy and trying again...")
                pass
            except requests.exceptions.ConnectionError as e:
                del(self.proxies[proxy_index])
                print("An error occurred with the proxy: Removing the proxy and trying again...")
                print("OOPS!! Connection Error. Make sure you are connected to Internet. Technical Details given below.\n")
                print(str(e))
            except requests.exceptions.Timeout as e:
                print("OOPS!! Timeout Error")
                print(str(e))
                pass
            except requests.exceptions.RequestException as e:
                print("OOPS!! General Error")
                print(str(e))
            except KeyboardInterrupt:
                print("Someone closed the program")
        


    def check_opening_hours(self):
        """A program to check if:
            - It is a current trading day (non weekend or public holiday)
            - The ASX announcements platform is running (7:30am AEST to 7:30pm AEST / 8:30pm dayliight savings)
        More info: ASX Listing Rules Guidance Note 14 """
        # Check for weekend day
        now = datetime.now()
        if now.weekday() > 4:
            return True
        # To do: Catch daylight savings days, Catch public holidays
        elif time(7,30) <= now.time() <= time(20,30):
            return False
    
        return True


rs = AsxSpider()
n = 0

while n < 100:
    if rs.check_opening_hours():
        print("The ASX announcement platform is currently closed. Shutting down")
#        raise SystemExit
    
    if rs.check_proxies():
        rs.refresh_proxies()
    
    rs.get_asx_announcements()
#    print(rs.asx_announcements[0])
    print(rs.asx_announcements[-1])
    n += 1
    t.sleep(10)

# Write to database
# Create an alert

del[rs]