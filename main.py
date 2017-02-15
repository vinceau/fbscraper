# -*- coding: utf-8 -*-

import argparse
import time

from datetime import datetime
from selenium import webdriver
from urlparse import urljoin, urlparse

from record import Record

post_selector = 'div.fbUserContent._5pcr'
login_file = 'login.txt'

class FBScraper(object):

    def __init__(self):
        self.driver = webdriver.Firefox()

    def __del__(self):
        self.driver.quit()

    def login(self, user, password):
        self.driver.get('https://www.facebook.com/login.php')
        self._run_js("document.querySelector('#email').value = '{}';".format(user))
        self._run_js("document.querySelector('#pass').value = '{}';".format(password))
        self._run_js("document.querySelector('#login_form').submit();")
        time.sleep(3)
        return 'login' not in self.driver.current_url
        
    def _run_js(self, code):
        print('Executing Javascript: <{}>'.format(code))
        return self.driver.execute_script(code)

    def scrape_userid(self, targetid):
        #self.driver.get(targeturl)
        self._scrape_all_friends(targetid)

    def _scrape_all_friends(self, targetid):
        friends_scraped = 0
        rec = Record(timestring() + 'friends', ['name', 'profile'])

        #load the friends page
        friendsurl = self._targeturl(targetid) + '&sk=friends'
        self.driver.get(friendsurl)

        friends_selector = "//ul[contains(@data-pnref, 'friends')]//div[contains(@class, 'uiProfileBlockContent')]//a[@data-hovercard]"
        all_friends = self.driver.find_elements_by_xpath(friends_selector)
        while len(all_friends) > friends_scraped:
            for friend in all_friends[friends_scraped:]:
                name = friend.text
                friend_url = stripquery(friend.get_attribute('href'))
                rec.add_record({'name': name, 'profile': friend_url})
                friends_scraped += 1

            #scroll to the bottom of the page
            self._run_js("window.scrollTo(0, document.body.scrollHeight);")
            #wait for the friends to populate
            time.sleep(3)
            all_friends = self.driver.find_elements_by_xpath(friends_selector)

        print('Scraped {} friends into {}'.format(friends_scraped, rec.filename))

    def _targeturl(self, targetid):
        return 'https://www.facebook.com/profile.php?id=' + targetid


def timestring():
    return datetime.now().strftime("%Y%m%d-%H%M-")

def stripquery(url):
    return urljoin(url, urlparse(url).path)


def main():
    parser = argparse.ArgumentParser(description='Crawl a bunch of Facebook sites and record the posts.')
    parser.add_argument('--input', '-i', dest='inputfile', required=False,
                        help='a file to read a list of Facebook usernames from', metavar='FILE')
    args = parser.parse_args()

    url = 'index'
    filename = timestring() + url + '.csv'

    with open(login_file, 'r') as f:
        lines = f.readlines()
        fb_user = lines[0].strip()
        fb_pass = lines[1].strip()
        fbs = FBScraper()
        if fbs.login(fb_user, fb_pass):
            fbs.scrape_userid('100004667535058')


if __name__ == "__main__":
    main()
