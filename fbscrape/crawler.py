import logging as log

from selenium.common.exceptions import NoSuchElementException, WebDriverException

# local imports
from base import BaseCrawler
from custom import css_selectors, xpath_selectors, page_references, text_content
from helpers import join_url


class FBCrawler(BaseCrawler):

    def __init__(self):
        BaseCrawler.__init__(self)
        self.stop_request = False
        self.pause_request = False
        self.status = 'init'
        self._set_status('ready')

    def is_valid_target(self, targeturl):
        """Returns True if <targeturl> is a valid profile.
        Does this by checking if a certain error message text is contained inside the page body.
        """
        try:
            self.load(targeturl)
            header_text = self.driver.find_element_by_css_selector(css_selectors.get('error_header')).text
            return text_content.get('error_header_text').lower() not in header_text.lower()
        except NoSuchElementException:
            return True

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
            # don't do anything if we've got a stop request
            if self.stop_request:
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
        try:
            self.load('https://www.facebook.com/login.php')
            self.js("document.querySelector('{}').value = '{}';".format(css_selectors.get('email_field'), user))
            self.js("document.querySelector('{}').value = '{}';".format(css_selectors.get('password_field'), password))
            self.js("document.querySelector('{}').submit();".format(css_selectors.get('login_form')))
            self.delay()
            return 'login' not in self.driver.current_url
        except WebDriverException:
            log.error('Couldn\'t load page. Are you connected to the internet?')
            return False

    def pause(self):
        self.pause_request = True

    def unpause(self):
        self.pause_request = False

    def interrupt(self, callback=None, restart=False):
        self.stop_request = True
        if self.status == 'ready':
            self._set_status('stopped')
        # loop until we are ready to do things
        while self.status != 'stopped':
            pass
        if restart:
            self.restart()
        if callback:
            callback()

    def restart(self):
        self.pause_request = False
        self.stop_request = False
        self._set_status('ready')

    def delay(self, multiplier=1):
        self._set_status('paused')
        BaseCrawler.delay(self, multiplier)
        while (self.pause_request) and not self.stop_request:
            pass
        self._set_status('running')


    def _grab_post_content(self, p, with_translation=True):
        translation = ''

        # if there's original content grab it
        # sometimes facebook automatically shows the translated text and not
        # the original.
        try:
            so = p.find_element_by_link_text(text_content['see_original'])
            # split the post text into the original post and translation
            parts = so.find_elements_by_xpath(xpath_selectors.get('trans_splitter'))
            translation = parts[1].text
            if self.force_click(p, so):
                print('clicked \'see original\'')
            # remove the translation from the post text
            post_text = p.text.replace(text_content['hide_original'], text_content['see_original'])
            post_text = post_text.replace(translation, '')
            if with_translation:
                return post_text, translation
            else:
                return post_text, ''
        except (NoSuchElementException):
            pass

        # grab the text normally
        post_text = p.text

        # expand the see more links if it exists
        try:
            # clicking the see more link can be quite unpredictable
            # sometimes it takes a while for it to load andetimes clicking it seems
            # to do nothing. so wrap it in a while loop.
            sm = p.find_element_by_css_selector(css_selectors.get('see_more'))
            if self.force_click(p, sm):
                print('found and expanded see more')
                post_text = p.text
        except (NoSuchElementException):
            pass

        # grab the translation if it exists and is needed
        if with_translation:
            try:
                st = p.find_element_by_link_text(text_content.get('see_translation_text'))
                st_parent = st.find_element_by_xpath('../..')
                if self.force_click(p, st):
                    translation = st_parent.find_element_by_css_selector(css_selectors.get('translation')).text
                    print('found translation')
            except (NoSuchElementException):
                pass


        return post_text, translation


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

                post_text, translation = self._grab_post_content(p)

                date_el = p.find_element_by_xpath(xpath_selectors.get('post_date'))
                p_time = date_el.get_attribute('data-utime')  # this is unix time!!!
                p_link = date_el.find_element_by_xpath('..').get_attribute('href')

                count += 1
                # date, post_text, permalink, translation, count
                callback(p_time, post_text, p_link, translation, count)

            self.scroll_to_bottom(wait=True)

        return count

    @running
    def crawl_likes(self, targeturl, callback):
        """For each like of a target, execute callback.
        Callback format: Liked Page Name, Liked Page URL, count
        """
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
                callback(like.text, like.get_attribute('href'), count)

            self.scroll_to_bottom(wait=True)

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

            self.scroll_to_bottom(wait=True)

        return count

    @running
    def crawl_photos(self, targeturl, callback):
        """Callback format: photo_source_url, photo_description, photo_post_permalink, count

        The description is not actually the description that was posted with the photo but an
        automatically generated description by Facebook's algorithms. It can detect objects that
        might be contained within the image for example: "trees, person, smiling" could be a description.
        """
        albumurl = join_url(targeturl, page_references.get('photos_page'))
        self.load(albumurl)

        count = 0
        while True:
            all_photos = self.driver.find_elements_by_css_selector(css_selectors.get('photo_selector'))
            # break if no more photos
            if len(all_photos) <= count:
                break

            for p in all_photos[count:]:
                if self.stop_request:
                    return count

                # url of the image
                photo_source_url = p.get_attribute('data-starred-src')

                # get the metadata and store that too
                link = p.find_element_by_css_selector('a')
                photo_description = link.get_attribute('aria-label')
                # get the permalink url of the image post
                photo_post_permalink = link.get_attribute('href')

                count += 1
                callback(photo_source_url, photo_description, photo_post_permalink, count)

            self.scroll_to_bottom(wait=True)

        return count

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

    @running
    def crawl_one_album(self, albumurl, callback):
        """Callback format: photo_source_url, photo_post_permalink, count
        """

        self.load(albumurl)
        count = 0
        while True:
            all_photos = self.driver.find_elements_by_css_selector(css_selectors.get('album_photo'))
            # break if no more photos
            if len(all_photos) <= count:
                break

            for p in all_photos[count:]:
                if self.stop_request:
                    return count

                # url of the image
                try:
                    img = p.find_element_by_css_selector('img')
                except NoSuchElementException:
                    # this is probably a video in the video folder
                    img = p.find_element_by_css_selector('span > div')

                photo_source_url = self.get_bg_img_url(img)
                photo_post_permalink = p.get_attribute('ajaxify')
                count += 1
                callback(photo_source_url, photo_post_permalink, count)

            self.scroll_to_bottom(wait=True)

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
            self.delay()
            title = l.get_attribute('title')
            main_pane = self.driver.find_element_by_css_selector(css_selectors.get('about_main'))
            callback(title, main_pane.text)
            count += 1
        return count

    @running
    def crawl_groups(self, targeturl, callback):
        """Callback format: group_name, group_url, count
        """
        self.load(join_url(targeturl, page_references.get('groups_page')))
        count = 0
        while True:
            # get groups, break if no more groups
            groups = self.driver.find_elements_by_css_selector(css_selectors.get('groups'))
            if len(groups) <= count:
                break

            # extract group info
            for g in groups:
                if self.stop_request:
                    return count

                count += 1
                callback(g.text, g.get_attribute('href'), count)

            self.scroll_to_bottom(wait=True)

        return count


    @running
    def crawl_checkins(self, targeturl, callback):
        """Callback format: check_in_name, check_in_url, count
        """
        self.load(join_url(targeturl, page_references.get('checkins')))
        count = 0
        while True:
            # get groups, break if no more groups
            checkins = self.driver.find_elements_by_css_selector(css_selectors.get('checkins'))
            if len(checkins) <= count:
                break

            # extract check in info
            for p in checkins:
                if self.stop_request:
                    return count

                count += 1
                callback(p.text, p.get_attribute('href'), count)

            self.scroll_to_bottom(wait=True)

        return count


    @running
    def crawl_search_results(self, url, callback, limit=0):
        """Accepts a callback method which has search result's name, url, imageurl,
        as well as the current search result count.
        Limit is the maximum number of results to return. A limit of zero is unlimited.
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
                url = r.find_elements_by_css_selector(css_selectors.get('search_link'))[1]
                name = url.text
                count += 1
                callback(name, url.get_attribute('href'), imageurl, count)

            self.scroll_to_bottom(wait=True)

        return count

    @running
    def crawl_event_guests(self, url, callback, guest_filter=None):
        if guest_filter is None:
            guest_filter = ['interested', 'going', 'invited']
        self.load(url, scroll=False)
        total = 0
        # open guests list
        guest_list = self.driver.find_element_by_css_selector(css_selectors.get('event_guests'))
        guest_list.click()
        self.delay(1.5)
        buttons = self.driver.find_elements_by_css_selector(css_selectors.get('guest_buttons'))
        dialog = buttons[0].find_element_by_xpath('../../..')
        for b in buttons:
            # check to see if we want to scrape these guests
            label = b.text.strip().split(' ')[0].lower()
            if label not in guest_filter:
                continue

            # we want to scrape these guests
            count = 0
            b.click()
            self.delay()
            scroller = dialog.find_element_by_css_selector(css_selectors.get('guest_scroller'))
            while True:
                results = dialog.find_elements_by_css_selector(css_selectors.get('guest_list'))
                if len(results) <= count:
                    break

                for friend in results[count:]:
                    if self.stop_request:
                        return total
                    friend_info = friend.find_element_by_xpath(xpath_selectors.get('event_friend_info'))
                    name = friend_info.text
                    url = friend_info.get_attribute('href')
                    imgurl = friend.find_element_by_css_selector(css_selectors.get('friend_image')).get_attribute('src')
                    count += 1
                    total += 1
                    callback(label, name, url, imgurl, total)

                self.js('a = arguments[0]; a.scrollTo(0, a.scrollHeight);', scroller)
                self.delay()

        return total
