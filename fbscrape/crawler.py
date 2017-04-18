import logging as log

from threading import Lock

from selenium import webdriver
from time import sleep, time

# local imports
from custom import css_selectors, xpath_selectors, page_references
from helpers import join_url


class FBCrawler(object):

    def __init__(self, min_delay=2):
        self.driver = webdriver.Firefox()
        self.min_delay = min_delay  # seconds to wait for infinite scroll items to populate
        self.loads = 0
        self.load_time = 0
        self.stop_request = False
        self.pause_request = False
        self.status = 'init'
        self._set_status('ready')
        self.lock = Lock()

    def __del__(self):
        self.driver.quit()

    def _set_status(self, s):
        """Sets s as the new status. Returns the previous status as result.
        """
        temp = self.status
        self.status = s
        return temp

    def running(func):
        """This is a decorator in order to set the status as running when running
        and the status as ready when action is complete
        """
        def do_stuff(self, *args, **kwargs):
            with self.lock:
                # don't do anything if we're not ready
                if self.status != 'ready':
                    return None

                # we're ready to runble
                old = self._set_status('running')
                ret = func(self, *args, **kwargs)
                if self.stop_request:
                    self._set_status('stopped')
                else:
                    self._set_status(old)
                return ret
        return do_stuff

    @running
    def login(self, user, password):
        self.load('https://www.facebook.com/login.php')
        self._js("document.querySelector('{}').value = '{}';".format(css_selectors.get('email_field'), user))
        self._js("document.querySelector('{}').value = '{}';".format(css_selectors.get('password_field'), password))
        self._js("document.querySelector('{}').submit();".format(css_selectors.get('login_form')))
        self._delay()
        return 'login' not in self.driver.current_url

    def _js(self, code):
        return self.driver.execute_script(code)

    def _update_delay(self, seconds):
        self.load_time += seconds
        self.loads += 1

    def pause(self):
        self.pause_request = True

    def unpause(self):
        self.pause_request = False

    def interrupt(self, callback=None):
        self.stop_request = True
        if self.status == 'ready':
            self._set_status('stopped')
        # loop until we are ready to do things
        while self.status != 'stopped':
            pass
        if callback:
            callback()

    def restart(self):
        self.pause_request = False
        self.stop_request = False
        self._set_status('ready')

    def _delay(self):
        """Sleeps the average amount of time it has taken to load a page or at least self.min_delay seconds.
        """
        self._set_status('paused')
        avg = self.load_time / self.loads
        secs = max(avg, self.min_delay)
        log.info('Sleeping %f seconds', secs)
        sleep(secs)
        while (self.pause_request) and not self.stop_request:
            pass
        self._set_status('running')

    def load(self, url, force=False, scroll=True):
        """Load url in the browser if it's not already loaded. Use force=True to force a reload.
        Also keeps track of how long it has taken to load.
        If scroll is True (default) it will scroll to the bottom once load is complete (to trigger infinite scroll).
        """
        if url == self.driver.current_url and not force:
            return
        start = time()
        self.driver.get(url)
        self._update_delay(time() - start)
        if scroll:
            self._scroll_to_bottom()

    def _scroll_to_bottom(self, wait=False):
        """Scrolls to the bottom of the page. Useful for triggering infinite scroll.
        If wait is true (false by default), it will wait for potential items to populate before returning.
        """
        self._js("window.scrollTo(0, document.body.scrollHeight);")
        if wait:
            self._delay()

    @running
    def crawl_posts(self, targeturl, callback):
        count = 0
        # load their timeline page
        self.load(targeturl)
        while True:
            all_posts = self.driver.find_elements_by_css_selector(css_selectors.get('user_posts'))
            # break if there are no more posts left
            if len(all_posts) <= count:
                break

            # scrape each post
            for p in all_posts[count:]:
                if self.stop_request:
                    return count
                count += 1
                callback(p, count)

            self._scroll_to_bottom(wait=True)

        return count

    @running
    def crawl_likes(self, targeturl, callback):
        count = 0
        # load the likes page
        likesurl = join_url(targeturl, page_references.get('likes_page'))
        self.load(likesurl)

        while True:
            all_likes = self.driver.find_elements_by_xpath(xpath_selectors.get('likes_selector'))
            # break if no more likes
            if len(all_likes) <= count:
                break

            for like in all_likes[count:]:
                if self.stop_request:
                    return count
                count += 1
                callback(like, count)

            self._scroll_to_bottom(wait=True)

        return count

    @running
    def crawl_friends(self, targeturl, callback):
        count = 0
        # load the friends page
        friendsurl = join_url(targeturl, page_references.get('friends_page'))
        self.load(friendsurl)

        while True:
            all_friends = self.driver.find_elements_by_css_selector(css_selectors.get('friends_selector'))
            # break if no more friends
            if len(all_friends) <= count:
                break

            for friend in all_friends[count:]:
                if self.stop_request:
                    return count
                count += 1
                friend_info = friend.find_element_by_xpath(xpath_selectors.get('friend_info'))
                name = friend_info.text
                url = friend_info.get_attribute('href')
                imgurl = friend.find_element_by_css_selector(css_selectors.get('friend_image')).get_attribute('src')
                callback(name, url, imgurl, count)

            self._scroll_to_bottom(wait=True)

        return count

    def crawl_photos(self, targeturl, callback):
        photos_url = join_url(targeturl, page_references.get('photos_page'))
        return self._album_crawler(photos_url, 'photo_selector', callback)

    @running
    def crawl_albums(self, targeturl, callback):
        # scrape all albums
        self.load(join_url(targeturl, page_references.get('albums')))
        albums = self.driver.find_elements_by_css_selector(css_selectors.get('indiv_albums'))
        count = 0
        for album_name, album_url in [(a.text, a.get_attribute('href')) for a in albums]:
            if self.stop_request:
                return count
            count += 1
            callback(album_name, album_url, count)
        return count

    def crawl_one_album(self, album_url, callback):
        return self._album_crawler(album_url, 'album_photo', callback)

    @running
    def _album_crawler(self, albumurl, css, callback):
        self.load(albumurl)
        count = 0
        while True:
            all_photos = self.driver.find_elements_by_css_selector(css_selectors.get(css))
            # break if no more photos
            if len(all_photos) <= count:
                break

            for p in all_photos[count:]:
                if self.stop_request:
                    return count
                count += 1
                callback(p, count)

            self._scroll_to_bottom(wait=True)

        return count

    @running
    def crawl_about(self, targeturl, callback):
        self.load(join_url(targeturl, page_references.get('about_page')))
        about_links = self.driver.find_elements_by_css_selector(css_selectors.get('about_links'))
        count = 0
        for l in about_links:
            if self.stop_request:
                return count
            l.click()
            self._delay()
            title = l.get_attribute('title')
            main_pane = self.driver.find_element_by_css_selector(css_selectors.get('about_main'))
            callback(title, main_pane.text)
            count += 1
        return count

    @running
    def crawl_groups(self, targeturl, callback):
        self.load(join_url(targeturl, page_references.get('groups_page')))
        count = 0
        while True:
            # get groups, break if no more groups
            groups = self.driver.find_elements_by_xpath(xpath_selectors.get('groups'))
            if len(groups) <= count:
                break

            # extract group info
            for g in groups:
                if self.stop_request:
                    return count
                count += 1
                callback(g, count)

            self._scroll_to_bottom(wait=True)

        return count

    @running
    def crawl_search_results(self, url, callback, limit=0):
        """Accepts a callback method which has search result's name, url, imageurl,
        as well as the current search result count.
        """
        self.load(url)
        count = 0
        while True:
            results = self.driver.find_elements_by_css_selector(css_selectors.get('search_results'))
            if len(results) <= count:
                break

            for r in results[count:]:
                if self.stop_request or limit > 0 and count >= limit:
                    return count
                imageurl = r.find_element_by_css_selector(css_selectors.get('search_pics')).get_attribute('src')
                url = r.find_element_by_css_selector(css_selectors.get('search_link'))
                name = url.text
                count += 1
                callback(name, url.get_attribute('href'), imageurl, count)

            self._scroll_to_bottom(wait=True)

        return count
