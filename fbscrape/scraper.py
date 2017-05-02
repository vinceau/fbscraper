
import logging as log
import os

# local imports
import record

from crawler import FBCrawler
from helpers import strip_query, timestring, path_safe, get_target, get_targeturl


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

    def autotarget(func):
        """This decorator converts the target into a target url and ensures it's a legit page.
        """
        def do_stuff(self, target):
            if self.stop_request:
                return None

            # make sure we're a proper url
            targeturl = get_targeturl(target)
            if not self.is_valid_target(targeturl):
                log.info('%s is not a valid target!', targeturl)
                return None

            return func(self, targeturl)

        return do_stuff

    def selective_scrape(self, settings):
        self.settings = settings

    @autotarget
    def scrape(self, targeturl):
        target = get_target(targeturl)
        log.info('Scraping user %s at URL: %s', target, targeturl)
        if self.settings['posts']:
            self.scrape_posts(targeturl)
        if self.settings['friends']:
            self.scrape_friends(targeturl)
        if self.settings['photos']:
            self.scrape_all_photos(targeturl)
        if self.settings['likes']:
            self.scrape_likes(targeturl)
        if self.settings['about']:
            self.scrape_about(targeturl)
        if self.settings['groups']:
            self.scrape_groups(targeturl)
        log.info('Finished scraping user %s', target)

    @autotarget
    def scrape_posts(self, targeturl):
        target = get_target(targeturl)
        rec = record.Record(self._output_file(target, 'posts'), ['date', 'post', 'translation', 'permalink'])
        log.info('Scraping posts into %s', rec.filename)

        def callback(p_time, post_text, p_link, translation, i):
            rec.add_record({
                'date': timestring(p_time),
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

    @autotarget
    def scrape_likes(self, targeturl):
        target = get_target(targeturl)
        rec = record.Record(self._output_file(target, 'likes'), ['name', 'url'])
        log.info('Scraping likes into %s', rec.filename)

        def callback(name, page_url, i):
            rec.add_record({'name': name, 'url': page_url})
            log.info('Scraped like %d: %s', i, name)

        likes_scraped = self.crawl_likes(targeturl, callback)
        log.info('Scraped %d likes into %s', likes_scraped, rec.filename)

    @autotarget
    def scrape_friends(self, targeturl):
        target = get_target(targeturl)
        rec = record.Record(self._output_file(target, 'friends'), ['name', 'profile'])
        log.info('Scraping friends into %s', rec.filename)

        def callback(name, url, imgurl, i):
            friend_url = strip_query(url)
            rec.add_record({'name': name, 'profile': friend_url})
            log.info('Scraped friend %d: %s', i, name)

        friends_scraped = self.crawl_friends(targeturl, callback)
        log.info('Scraped %d friends into %s', friends_scraped, rec.filename)

    @autotarget
    def scrape_all_photos(self, targeturl):
        self.scrape_photos(targeturl)
        self.scrape_all_albums(targeturl)

    @autotarget
    def scrape_photos(self, targeturl):
        """Scrapes the targets photos and only the photos on the target's photo page.
        Photos in albums are not scraped.
        """
        target = get_target(targeturl)
        # scrape main photos
        photo_album = record.Album(self._output_file(target, 'photos'), True)

        def photo_cb(photourl, description, perma, _):
            self._save_to_album(photourl, description, perma, photo_album)

        photos_scraped = self.crawl_photos(targeturl, photo_cb)
        log.info('Scraped %d photos into %s', photos_scraped, photo_album.name)

    @autotarget
    def scrape_all_albums(self, targeturl):
        target = get_target(targeturl)

        def album_cb(name, url, _):
            """What to do for each album.
            """
            album_name = 'album-' + path_safe(name)
            album = record.Album(self._output_file(target, album_name), True)

            def album_download_cb(photourl, description, perma, _):
                self._save_to_album(photourl, description, perma, album)

            scraped = self.crawl_one_album(url, album_download_cb)
            log.info('Scraped %d photos into %s', scraped, album.name)

        self.crawl_albums(targeturl, album_cb)


    def _save_to_album(self, photourl, description, perma, album):
        try:
            # download the image
            album.add_image(photourl)
            # save the descriptions
            album.add_description(photourl, description, perma)
            log.info('Scraped photo: %s', photourl)
        except record.BrokenImageError:
            log.error('Failed to download image: %s', photourl)


    @autotarget
    def scrape_about(self, targeturl):
        target = get_target(targeturl)
        rec = record.Record(self._output_file(target, 'about'), ['section', 'text'])

        def callback(section, content):
            rec.add_record({'section': section, 'text': content})
            log.info('Scraped section %s with the following text:\n#### START ####\n%s\n####  END  ####',
                     section, content)

        self.crawl_about(targeturl, callback)


    @autotarget
    def scrape_groups(self, targeturl):
        target = get_target(targeturl)
        rec = record.Record(self._output_file(target, 'groups'), ['name', 'url'])

        def callback(name, url, i):
            rec.add_record({'name': name, 'url': url})
            log.info('Scraped group %d: %s', i, name)

        scraped = self.crawl_groups(targeturl, callback)
        log.info('Scraped %d groups into %s', scraped, rec.filename)
