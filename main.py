# -*- coding: utf-8 -*-

import argparse
import time

from selenium import webdriver

#local imports
import record

from custom import css_selectors, xpath_selectors, page_references
from helpers import join_url, strip_query, timestring

post_selector = 'div.fbUserContent._5pcr'
login_file = 'login.txt'

#seconds to wait for infinite scroll items to populate
delay = 2


class FBScraper(object):

    def __init__(self):
        self.driver = webdriver.Firefox()

#   def __del__(self):
#       self.driver.quit()

    def login(self, user, password):
        self.driver.get('https://www.facebook.com/login.php')
        self._run_js("document.querySelector('{}').value = '{}';".format(css_selectors.get('email_field'), user))
        self._run_js("document.querySelector('{}').value = '{}';".format(css_selectors.get('password_field'), password))
        self._run_js("document.querySelector('{}').submit();".format(css_selectors.get('login_form')))
        time.sleep(delay)
        return 'login' not in self.driver.current_url
        
    def _run_js(self, code):
        print('Executing Javascript: <{}>'.format(code))
        return self.driver.execute_script(code)

    def scrape_by_id(self, targetid):
        self._scrape_all(targetid, 'https://www.facebook.com/profile.php?id=' + targetid)

    def scrape_by_username(self, target):
        self._scrape_all(target, 'https://www.facebook.com/' + target)

    def _scrape_all(self, target, targeturl):
        self._scrape_photos(target, targeturl)
        #self._scrape_posts(target, targeturl)
        #self._scrape_likes(target, targeturl)
        #self._scrape_friends(target, targeturl)

    def _scrape_posts(self, target, targeturl):
        posts_scraped = 0
        rec = record.Record(timestring() + '-' + target + '-posts', ['date', 'post', 'permalink'])

        #load their timeline page
        self.driver.get(targeturl)
        while True:
            all_posts = self.driver.find_elements_by_xpath(xpath_selectors.get('user_posts'))
            #break if there are no more posts left
            if len(all_posts) <= posts_scraped:
                break

            #scrape each post
            for p in all_posts[posts_scraped:]:
                date_el = p.find_element_by_xpath(xpath_selectors.get('post_date'))
                p_time = timestring(date_el.get_attribute('data-utime'))
                p_link = date_el.find_element_by_xpath('..').get_attribute('href')
                rec.add_record({
                    'date': p_time,
                    'post': p.text,
                    'permalink': p_link,
                })
                posts_scraped += 1

            #scroll to the bottom of the page
            self._run_js("window.scrollTo(0, document.body.scrollHeight);")
            #wait for the posts to populate
            time.sleep(delay)

        print('Scraped {} posts into {}'.format(posts_scraped, rec.filename))


    def _scrape_likes(self, target, targeturl):
        likes_scraped = 0
        rec = record.Record(timestring() + '-' + target + '-likes', ['name', 'url'])

        #load the likes page
        likesurl = join_url(targeturl, page_references.get('likes_page'))
        self.driver.get(likesurl)

        while True:
            all_likes = self.driver.find_elements_by_xpath(xpath_selectors.get('likes_selector'))
            #break if no more likes
            if len(all_likes) <= likes_scraped:
                break

            for like in all_likes[likes_scraped:]:
                name = like.text
                page_url = like.get_attribute('href')
                rec.add_record({'name': name, 'url': page_url})
                likes_scraped += 1

            #scroll to the bottom of the page
            self._run_js("window.scrollTo(0, document.body.scrollHeight);")
            #wait for the friends to populate
            time.sleep(delay)

        print('Scraped {} likes into {}'.format(likes_scraped, rec.filename))

    def _scrape_friends(self, target, targeturl):
        friends_scraped = 0
        rec = record.Record(timestring() + '-' + target + '-friends', ['name', 'profile'])

        #load the friends page
        friendsurl = join_url(targeturl, page_references.get('friends_page'))
        self.driver.get(friendsurl)

        while True:
            all_friends = self.driver.find_elements_by_xpath(xpath_selectors.get('friends_selector'))
            #break if no more friends
            if len(all_friends) <= friends_scraped:
                break

            for friend in all_friends[friends_scraped:]:
                name = friend.text
                friend_url = strip_query(friend.get_attribute('href'))
                rec.add_record({'name': name, 'profile': friend_url})
                friends_scraped += 1

            #scroll to the bottom of the page
            self._run_js("window.scrollTo(0, document.body.scrollHeight);")
            #wait for the friends to populate
            time.sleep(delay)

        print('Scraped {} friends into {}'.format(friends_scraped, rec.filename))

    def _scrape_photos(self, target, targeturl):
        photos_scraped = 0
        album = record.Album(timestring() + '-' + target + '-photos')

        #load the photos page
        self.driver.get(join_url(targeturl, page_references.get('photos_page')))

        while True:
            all_photos = self.driver.find_elements_by_css_selector(css_selectors.get('photo_selector'))
            #break if no more photos
            if len(all_photos) <= photos_scraped:
                break

            for p in all_photos[photos_scraped:]:
                img_url = p.get_attribute('data-starred-src')
                album.add_image(img_url)
                photos_scraped += 1

            #scroll to the bottom of the page
            self._run_js("window.scrollTo(0, document.body.scrollHeight);")
            #wait for the friends to populate
            time.sleep(delay)

        print('Scraped {} photos into {}'.format(photos_scraped, album.name))



def main():
    parser = argparse.ArgumentParser(description='Crawl a bunch of Facebook sites and record the posts.')
    parser.add_argument('--input', '-i', dest='inputfile', required=False,
                        help='a file to read a list of Facebook usernames from', metavar='FILE')
    args = parser.parse_args()

    url = 'index'
    filename = timestring() + '-' + url + '.csv'

    with open(login_file, 'r') as f:
        lines = f.readlines()
        fb_user = lines[0].strip()
        fb_pass = lines[1].strip()
        fbs = FBScraper()
        if fbs.login(fb_user, fb_pass):
            #fbs.scrape_by_id('100004667535058')
            #fbs.scrape_by_username('sammy.solaxa.9')
            #fbs.scrape_by_username('tariqsediqi')
            #fbs.scrape_by_id('100012735706236')
            #guy with lots of photos (2 pages)
            fbs.scrape_by_username('nicknando.ducaat')


if __name__ == "__main__":
    main()
