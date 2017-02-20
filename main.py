# -*- coding: utf-8 -*-

import sys;
try:
    #allow printing of non-standard characters to stdout
    reload(sys);
    sys.setdefaultencoding("utf8")
except NameError:
    #we're on Python 3 so we already good
    pass

import argparse
import os
import logging as log

from builtins import input
from getpass import getpass
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from time import sleep

#local imports
import record

from custom import css_selectors, xpath_selectors, page_references, text_content
from helpers import join_url, strip_query, timestring, path_safe, extract_user

#seconds to wait for infinite scroll items to populate
delay = 2


class FBScraper(object):

    def __init__(self, output_dir=None):
        self.driver = webdriver.Firefox()
        #store in the current directory by default
        self.output_dir = output_dir if output_dir else ''

    def __del__(self):
        self.driver.quit()

    def login(self, user, password):
        self.load('https://www.facebook.com/login.php')
        self._js("document.querySelector('{}').value = '{}';".format(css_selectors.get('email_field'), user))
        self._js("document.querySelector('{}').value = '{}';".format(css_selectors.get('password_field'), password))
        self._js("document.querySelector('{}').submit();".format(css_selectors.get('login_form')))
        sleep(delay)
        return 'login' not in self.driver.current_url

    """Execute the javascript <code> and log into the terminal if <show> is True.
    """
    def _js(self, code, show=False):
        if show:
            log.info('Executing Javascript: {}'.format(code))
        return self.driver.execute_script(code)

    def _output_file(self, target, name):
        return os.path.join(self.output_dir, target, timestring() + '-' + target + '-' + name)

    """Load url in the browser if it's not already loaded. Use force=True to force a reload.
    """
    def load(self, url, force=False):
        if url == self.driver.current_url and not force:
            return
        self.driver.get(url)

    """Check if the given targeturl is a valid user profile.
    Does this by checking if a certain error message text is contained inside the page body.
    """
    def _valid_user(self, targeturl):
        try:
            self.load(targeturl)
            header_text = self.driver.find_element_by_css_selector(css_selectors.get('error_header')).text
            return text_content.get('error_header_text').lower() not in header_text.lower()
        except NoSuchElementException:
            return True

    """Infer whether the target is an id, username, or a URL and scrape accordingly.
    Not guaranteed to be accurate since usernames could also be fully numbers (I think).
    """
    def scrape(self, target):
        if not target:
            log.info('Invalid Facebook ID, Username, or URL!')
            return
        #check if target is a URL
        check = target
        if extract_user(target) is not None:
            check = extract_user(target)
        if check.isdigit():
            self.scrape_by_id(check)
        else:
            self.scrape_by_username(check)

    def scrape_by_id(self, targetid):
        self._scrape_all(targetid, 'https://www.facebook.com/profile.php?id=' + targetid)

    def scrape_by_username(self, target):
        self._scrape_all(target, 'https://www.facebook.com/' + target)

    def _scrape_all(self, target, targeturl):
        if not self._valid_user(targeturl):
            log.info('{} is a missing page!'.format(targeturl))
            return
        log.info('Scraping user {} at URL: {}'.format(target, targeturl))
        self._scrape_posts(target, targeturl)
        self._scrape_friends(target, targeturl)
        self._scrape_photos(target, targeturl)
        self._scrape_likes(target, targeturl)
        self._scrape_about(target, targeturl)
        self._scrape_groups(target, targeturl)
        log.info('Finished scraping user {}'.format(target))

    def _scrape_posts(self, target, targeturl):
        posts_scraped = 0
        rec = record.Record(self._output_file(target, 'posts'), ['date', 'post', 'permalink'])
        log.info('Scraping posts into {}'.format(rec.filename))

        #load their timeline page
        self.load(targeturl)
        while True:
            all_posts = self.driver.find_elements_by_css_selector(css_selectors.get('user_posts'))
            #break if there are no more posts left
            if len(all_posts) <= posts_scraped:
                break

            #scrape each post
            for p in all_posts[posts_scraped:]:
                #expand the see more links
                see_mores = p.find_elements_by_css_selector(css_selectors.get('see_more'))
                if len(see_mores) > 0:
                    for sm in see_mores:
                        sm.click()
                date_el = p.find_element_by_xpath(xpath_selectors.get('post_date'))
                p_time = timestring(date_el.get_attribute('data-utime'))
                p_link = date_el.find_element_by_xpath('..').get_attribute('href')
                rec.add_record({
                    'date': p_time,
                    'post': p.text,
                    'permalink': p_link,
                })
                posts_scraped += 1
                log.info('Scraped post #{}\n\n#### START POST ####\n{}\n####  END POST  ####\n'.format(posts_scraped, p.text))

            #scroll to the bottom of the page
            self._js("window.scrollTo(0, document.body.scrollHeight);")
            #wait for the posts to populate
            sleep(delay)

        log.info('Scraped {} posts into {}'.format(posts_scraped, rec.filename))


    def _scrape_likes(self, target, targeturl):
        likes_scraped = 0
        rec = record.Record(self._output_file(target, 'likes'), ['name', 'url'])
        log.info('Scraping likes into {}'.format(rec.filename))

        #load the likes page
        likesurl = join_url(targeturl, page_references.get('likes_page'))
        self.load(likesurl)

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
                log.info('Scraped like #{}: {}'.format(likes_scraped, name))

            #scroll to the bottom of the page
            self._js("window.scrollTo(0, document.body.scrollHeight);")
            #wait for likes to populate
            sleep(delay)

        log.info('Scraped {} likes into {}'.format(likes_scraped, rec.filename))

    def _scrape_friends(self, target, targeturl):
        friends_scraped = 0
        rec = record.Record(self._output_file(target, 'friends'), ['name', 'profile'])
        log.info('Scraping friends into {}'.format(rec.filename))

        #load the friends page
        friendsurl = join_url(targeturl, page_references.get('friends_page'))
        self.load(friendsurl)

        while True:
            all_friends = self.driver.find_elements_by_css_selector(css_selectors.get('friends_selector'))
            #break if no more friends
            if len(all_friends) <= friends_scraped:
                break

            for friend in all_friends[friends_scraped:]:
                name = friend.text
                friend_url = strip_query(friend.get_attribute('href'))
                rec.add_record({'name': name, 'profile': friend_url})
                friends_scraped += 1
                log.info('Scraped friend #{}: {}'.format(friends_scraped, name))

            #scroll to the bottom of the page
            self._js("window.scrollTo(0, document.body.scrollHeight);")
            #wait for the friends to populate
            sleep(delay)

        log.info('Scraped {} friends into {}'.format(friends_scraped, rec.filename))

    def _scrape_photos(self, target, targeturl):
        #scrape main photos
        photos_url = join_url(targeturl, page_references.get('photos_page'))
        self._scrape_album(target, 'photos', photos_url, 'photo_selector')
        
        #scrape all albums
        self.load(join_url(targeturl, page_references.get('albums')))
        albums = self.driver.find_elements_by_css_selector(css_selectors.get('indiv_albums'))
        for album_name, album_url in [(a.text, a.get_attribute('href')) for a in albums]:
            self._scrape_album(target, 'album-' + path_safe(album_name), album_url, 'album_photo')

    def _scrape_album(self, target, album_name, albumurl, css):
        album = record.Album(self._output_file(target, album_name))
        log.info('Scraping photos into {}'.format(album.name))
        self.load(albumurl)

        scraped = 0
        while True:
            all_photos = self.driver.find_elements_by_css_selector(css_selectors.get(css))
            #break if no more photos
            if len(all_photos) <= scraped:
                break

            for p in all_photos[scraped:]:
                img_url = p.get_attribute('data-starred-src')
                album.add_image(img_url)
                scraped += 1
                log.info('Scraped photo #{}: {}'.format(scraped, img_url))

            #scroll to the bottom of the page
            self._js("window.scrollTo(0, document.body.scrollHeight);")
            #wait for photos to populate
            sleep(delay)

        log.info('Scraped {} photos into {}'.format(scraped, album.name))

    def _scrape_about(self, target, targeturl):
        self.load(join_url(targeturl, page_references.get('about_page')))
        about_links = self.driver.find_elements_by_css_selector(css_selectors.get('about_links'))
        rec = record.Record(self._output_file(target, 'about'), ['section', 'text'])
        for l in about_links:
            l.click()
            sleep(delay)
            title = l.get_attribute('title')
            main_pane = self.driver.find_element_by_css_selector(css_selectors.get('about_main'))
            rec.add_record({'section': title, 'text': main_pane.text})
            log.info('Scraped section {} with the following text:\n#### START ####\n{}\n####  END  ####'
                     .format(title, main_pane.text))

    def _scrape_groups(self, target, targeturl):
        self.load(join_url(targeturl, page_references.get('groups_page')))

        scraped = 0
        rec = record.Record(self._output_file(target, 'groups'), ['name', 'url'])
        while True:
            #get groups, break if no more groups
            groups = self.driver.find_elements_by_xpath(xpath_selectors.get('groups'))
            if len(groups) <= scraped:
                break

            #extract group info
            for g in groups:
                name = g.text
                url = g.get_attribute('href')
                rec.add_record({'name': name, 'url': url})
                scraped += 1
                log.info('Scraped group #{}: {}'.format(scraped, name))

            #scroll to bottom and wait for new items to populate
            self._js("window.scrollTo(0, document.body.scrollHeight);")
            sleep(delay)

        log.info('Scraped {} groups into {}'.format(scraped, rec.filename))

def main():
    #configure logging level
    log.basicConfig(format='%(levelname)s:%(message)s', level=log.INFO)

    parser = argparse.ArgumentParser(description='Crawl a bunch of Facebook sites and record the posts.')
    parser.add_argument('--input', '-i', dest='inputfile', required=False,
                        help='a file to read a list of Facebook usernames from')
    parser.add_argument('--outputdir', '-o', dest='outputdir', required=False,
                        help='the directory to store the scraped files')
    parser.add_argument('--loginfile', '-l', dest='loginfile', required=False,
                        help='the file to read login credentials from (username/email on the first line, and password on the second line)')
    args = parser.parse_args()
    output_dir = args.outputdir if args.outputdir else ''
    fbs = FBScraper(output_dir)

    fb_user = ''
    fb_pass = ''

    #attempt to login
    if args.loginfile:
        with open(args.loginfile, 'r') as f:
            lines = f.readlines()
            fb_user = lines[0].strip()
            fb_pass = lines[1].strip()
    else:
        fb_user = input('Enter your Facebook login email: ')
        fb_pass = getpass('Enter your Facebook password:  ')
    if not fbs.login(fb_user, fb_pass):
        sys.exit('Failed to log into Facebook. Check your credentials and try again.')

    #login successful
    if args.inputfile:
        with open(args.inputfile, 'r') as input_f:
            for line in input_f:
                fbs.scrape(line.strip())
    else:
        log.info('No input file specified. Reading input from stdin.')
        print('Enter the Facebook ID, Username, or URL to scrape followed by the <Enter> key.')
        for line in sys.stdin:
            if not line.strip():
                break
            fbs.scrape(line.strip())
            print('Scrape complete. Enter another Facebook ID, Username, or URL followed by the <Enter> key.')
        print('Exiting...')


if __name__ == "__main__":
    main()
