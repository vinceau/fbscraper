
import logging as log
import os

from selenium.common.exceptions import NoSuchElementException, ElementNotVisibleException

# local imports
import record

from crawler import FBCrawler
from custom import css_selectors, xpath_selectors, text_content
from helpers import strip_query, timestring, path_safe, extract_user


class FBScraper(FBCrawler):

    def __init__(self, output_dir=None, min_delay=2):
        FBCrawler.__init__(self)
        # store in the current directory by default
        self.output_dir = output_dir if output_dir else ''
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

    def set_output_dir(self, folder):
        self.output_dir = folder

    def reset_foldername(self):
        self.foldernaming = self.def_foldername

    def reset_filename(self):
        self.filenaming = self.def_filename

    def _naming_keywords(self, orig, target, name):
        result = orig.replace('%TARGET%', target)
        result = result.replace('%TYPE%', name)
        result = result.replace('%TIMESTAMP%', timestring())
        return result

    def _output_file(self, target, name):
        folder = self._naming_keywords(self.foldernaming, target, name)
        filename = self._naming_keywords(self.filenaming, target, name)
        return os.path.join(self.output_dir, folder, filename)

    def _valid_user(self, targeturl):
        """Check if <targeturl> is a valid user profile.
        Does this by checking if a certain error message text is contained inside the page body.
        """
        try:
            self.load(targeturl)
            header_text = self.driver.find_element_by_css_selector(css_selectors.get('error_header')).text
            return text_content.get('error_header_text').lower() not in header_text.lower()
        except NoSuchElementException:
            return True

    def scrape(self, target):
        """Infer whether the target is an id, username, or a URL and scrape accordingly.
        Not guaranteed to be accurate since usernames could also be fully numbers (I think).
        """
        if not target:
            log.info('Invalid Facebook ID, Username, or URL!')
            return
        # check if target is a URL
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
        if self.settings['friends'] and not self.stop_request:
            self._scrape_friends(target, targeturl)
        if self.settings['photos'] and not self.stop_request:
            self._scrape_photos(target, targeturl)
        if self.settings['likes'] and not self.stop_request:
            self._scrape_likes(target, targeturl)
        if self.settings['about'] and not self.stop_request:
            self._scrape_about(target, targeturl)
        if self.settings['groups'] and not self.stop_request:
            self._scrape_groups(target, targeturl)
        log.info('Finished scraping user %s', target)
        self.stop_request = False

    def _scrape_posts(self, target, targeturl):
        rec = record.Record(self._output_file(target, 'posts'), ['date', 'post', 'translation', 'permalink'])
        log.info('Scraping posts into %s', rec.filename)

        def callback(p, i):
            # expand the see more links
            try:
                p.find_element_by_css_selector(css_selectors.get('see_more')).click()
            except (NoSuchElementException, ElementNotVisibleException):
                pass

            # get the text before we get the translation
            post_text = p.text
            # expand the see translations link if it exists
            translation = ''

            try:
                st = p.find_element_by_link_text(text_content.get('see_translation_text'))
                st_parent = st.find_element_by_xpath('../..')
                st.click()
                self._delay()
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

            # keep translation as a unicode string while merging
            if translation:
                translation = u'==== TRANSLATION ====\n{}\n'.format(translation)
            log.info(('Scraped post %d\n\n#### START POST ####\n%s\n%s'
                      '####  END POST  ####\n'), i, post_text, translation)

        posts_scraped = self.crawl_posts(targeturl, callback)
        log.info('Scraped %d posts into %s', posts_scraped, rec.filename)

    def _scrape_likes(self, target, targeturl):
        rec = record.Record(self._output_file(target, 'likes'), ['name', 'url'])
        log.info('Scraping likes into %s', rec.filename)

        def callback(like, i):
            name = like.text
            page_url = like.get_attribute('href')
            rec.add_record({'name': name, 'url': page_url})
            log.info('Scraped like %d: %s', i, name)

        likes_scraped = self.crawl_likes(targeturl, callback)
        log.info('Scraped %d likes into %s', likes_scraped, rec.filename)

    def _scrape_friends(self, target, targeturl):
        rec = record.Record(self._output_file(target, 'friends'), ['name', 'profile'])
        log.info('Scraping friends into %s', rec.filename)

        def callback(friend, i):
            name = friend.text
            friend_url = strip_query(friend.get_attribute('href'))
            rec.add_record({'name': name, 'profile': friend_url})
            log.info('Scraped friend %d: %s', i, name)

        friends_scraped = self.crawl_friends(targeturl, callback)
        log.info('Scraped %d friends into %s', friends_scraped, rec.filename)

    def _scrape_photos(self, target, targeturl):
        # scrape main photos
        photo_album = record.Album(self._output_file(target, 'photos'), True)

        def photo_cb(photo, _):
            self._save_to_album(photo, photo_album)

        photos_scraped = self.crawl_photos(targeturl, photo_cb)
        log.info('Scraped %d photos into %s', photos_scraped, photo_album.name)

        # scrape all albums
        def album_cb(name, url, _):
            """What to do for each album.
            """
            album_name = 'album-' + path_safe(name)
            album = record.Album(self._output_file(target, album_name), True)

            def album_download_cb(photo, _):
                self._save_to_album(photo, album)

            scraped = self.crawl_one_album(url, album_download_cb)
            log.info('Scraped %d photos into %s', scraped, album.name)

        self.crawl_albums(targeturl, album_cb)


    def _save_to_album(self, p, album):
        img_url = p.get_attribute('data-starred-src')
        try:
            # download the image
            album.add_image(img_url)
            # get the metadata and store that too
            link = p.find_element_by_css_selector('a')
            label = link.get_attribute('aria-label')
            href = link.get_attribute('href')
            album.add_description(img_url, label, href)
            log.info('Scraped photo: %s', img_url)
        except record.BrokenImageError:
            log.error('Failed to download image: %s', img_url)


    def _scrape_about(self, target, targeturl):
        rec = record.Record(self._output_file(target, 'about'), ['section', 'text'])

        def callback(section, content):
            rec.add_record({'section': section, 'text': content})
            log.info('Scraped section %s with the following text:\n#### START ####\n%s\n####  END  ####',
                     section, content)

        self.crawl_about(targeturl, callback)


    def _scrape_groups(self, target, targeturl):
        rec = record.Record(self._output_file(target, 'groups'), ['name', 'url'])

        def callback(g, i):
            name = g.text
            url = g.get_attribute('href')
            rec.add_record({'name': name, 'url': url})
            log.info('Scraped group %d: %s', i, name)

        scraped = self.crawl_groups(targeturl, callback)
        log.info('Scraped %d groups into %s', scraped, rec.filename)
