
import logging as log
import os

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from time import sleep, time

#local imports
import record

from custom import css_selectors, xpath_selectors, page_references, text_content
from helpers import join_url, strip_query, timestring, path_safe, extract_user


class FBScraper(object):

    """delay is the seconds to wait for infinite scroll items to populate
    """
    def __init__(self, output_dir=None, min_delay=2):
        self.driver = webdriver.Firefox()
        #store in the current directory by default
        self.output_dir = output_dir if output_dir else ''
        self.min_delay = min_delay
        self.loads = 0
        self.load_time = 0
        self.settings = {
            'posts': True,
            'friends': True,
            'photos': True,
            'likes': True,
            'about': True,
            'groups': True,
        }
        self.def_foldername = '%TARGET%'
        self.def_filename = '%TIMESTAMP%-%TYPE%'
        self.foldernaming = self.def_foldername
        self.filenaming = self.def_filename

    def __del__(self):
        self.driver.quit()

    def set_output_dir(self, folder):
        self.output_dir = folder

    def reset_foldername(self):
        self.foldernaming = self.def_foldername

    def reset_filename(self):
        self.filenaming = self.def_filename

    def login(self, user, password):
        self.load('https://www.facebook.com/login.php')
        self._js("document.querySelector('{}').value = '{}';".format(css_selectors.get('email_field'), user))
        self._js("document.querySelector('{}').value = '{}';".format(css_selectors.get('password_field'), password))
        self._js("document.querySelector('{}').submit();".format(css_selectors.get('login_form')))
        self.delay()
        return 'login' not in self.driver.current_url

    """Execute the javascript <code> and log into the terminal if <show> is True.
    """
    def _js(self, code, show=False):
        if show:
            log.info('Executing Javascript: %s', code)
        return self.driver.execute_script(code)

    def _naming_keywords(self, orig, target, name):
        result = orig.replace('%TARGET%', target)
        result = result.replace('%TYPE%', name)
        result = result.replace('%TIMESTAMP%', timestring())
        return result

    def _output_file(self, target, name):
        folder = self._naming_keywords(self.foldernaming, target, name)
        filename = self._naming_keywords(self.filenaming, target, name)
        return os.path.join(self.output_dir, folder, filename)

    def _update_delay(self, seconds):
        self.load_time += seconds
        self.loads += 1

    """Sleeps the average amount of time it has taken to load a page or at least self.min_delay seconds.
    """
    def delay(self):
        avg = self.load_time / self.loads
        secs = max(avg, self.min_delay)
        log.info('Sleeping %f seconds', secs)
        sleep(secs)

    """Load url in the browser if it's not already loaded. Use force=True to force a reload.
    """
    def load(self, url, force=False):
        if url == self.driver.current_url and not force:
            return
        start = time()
        self.driver.get(url)
        self._update_delay(time() - start)

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

    def selective_scrape(self, settings):
        self.settings = settings

    def _scrape_all(self, target, targeturl):
        if not self._valid_user(targeturl):
            log.info('%s is a missing page!', targeturl)
            return
        log.info('Scraping user %s at URL: %s', target, targeturl)
        if self.settings['posts']:
            self._scrape_posts(target, targeturl)
        if self.settings['friends']:
            self._scrape_friends(target, targeturl)
        if self.settings['photos']:
            self._scrape_photos(target, targeturl)
        if self.settings['likes']:
            self._scrape_likes(target, targeturl)
        if self.settings['about']:
            self._scrape_about(target, targeturl)
        if self.settings['groups']:
            self._scrape_groups(target, targeturl)
        log.info('Finished scraping user %s', target)

    def _scrape_posts(self, target, targeturl):
        posts_scraped = 0
        rec = record.Record(self._output_file(target, 'posts'), ['date', 'post', 'translation', 'permalink'])
        log.info('Scraping posts into %s', rec.filename)

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
                try:
                    p.find_element_by_css_selector(css_selectors.get('see_more')).click()
                except NoSuchElementException:
                    pass

                #get the text before we get the translation
                post_text = p.text

                #expand the see translations link if it exists
                translation = ''
                try:
                    st = p.find_element_by_link_text(text_content.get('see_translation_text'))
                    st_parent = st.find_element_by_xpath('../..')
                    st.click()
                    self.delay()
                    translation = st_parent.find_element_by_css_selector(css_selectors.get('translation')).text
                except NoSuchElementException:
                    pass

                date_el = p.find_element_by_xpath(xpath_selectors.get('post_date'))
                p_time = timestring(date_el.get_attribute('data-utime'))
                p_link = date_el.find_element_by_xpath('..').get_attribute('href')
                rec.add_record({
                    'date': p_time,
                    'post': post_text,
                    'translation': translation,
                    'permalink': p_link,
                })

                posts_scraped += 1
                #keep translation as a unicode string while merging
                if translation:
                    translation = u'==== TRANSLATION ====\n{}\n'.format(translation)
                log.info(('Scraped post #%d\n\n#### START POST ####\n%s\n%s'
                          '####  END POST  ####\n'), posts_scraped, post_text, translation)

            #scroll to the bottom of the page
            self._js("window.scrollTo(0, document.body.scrollHeight);")
            #wait for the posts to populate
            self.delay()

        log.info('Scraped %d posts into %s', posts_scraped, rec.filename)


    def _scrape_likes(self, target, targeturl):
        likes_scraped = 0
        rec = record.Record(self._output_file(target, 'likes'), ['name', 'url'])
        log.info('Scraping likes into %s', rec.filename)

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
                log.info('Scraped like #%d: %s', likes_scraped, name)

            #scroll to the bottom of the page
            self._js("window.scrollTo(0, document.body.scrollHeight);")
            #wait for likes to populate
            self.delay()

        log.info('Scraped %d likes into %s', likes_scraped, rec.filename)

    def _scrape_friends(self, target, targeturl):
        friends_scraped = 0
        rec = record.Record(self._output_file(target, 'friends'), ['name', 'profile'])
        log.info('Scraping friends into %s', rec.filename)

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
                log.info('Scraped friend #%d: %s', friends_scraped, name)

            #scroll to the bottom of the page
            self._js("window.scrollTo(0, document.body.scrollHeight);")
            #wait for the friends to populate
            self.delay()

        log.info('Scraped %d friends into %s', friends_scraped, rec.filename)

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
        log.info('Scraping photos into %s', album.name)
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
                log.info('Scraped photo #%d: %s', scraped, img_url)

            #scroll to the bottom of the page
            self._js("window.scrollTo(0, document.body.scrollHeight);")
            #wait for photos to populate
            self.delay()

        log.info('Scraped %d photos into %s', scraped, album.name)

    def _scrape_about(self, target, targeturl):
        self.load(join_url(targeturl, page_references.get('about_page')))
        about_links = self.driver.find_elements_by_css_selector(css_selectors.get('about_links'))
        rec = record.Record(self._output_file(target, 'about'), ['section', 'text'])
        for l in about_links:
            l.click()
            self.delay()
            title = l.get_attribute('title')
            main_pane = self.driver.find_element_by_css_selector(css_selectors.get('about_main'))
            rec.add_record({'section': title, 'text': main_pane.text})
            log.info('Scraped section %s with the following text:\n#### START ####\n%s\n####  END  ####',
                     title, main_pane.text)

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
                log.info('Scraped group #%d: %s', scraped, name)

            #scroll to bottom and wait for new items to populate
            self._js("window.scrollTo(0, document.body.scrollHeight);")
            self.delay()

        log.info('Scraped %d groups into %s', scraped, rec.filename)
