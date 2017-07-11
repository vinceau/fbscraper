import logging as log

from contextlib import contextmanager

from selenium import webdriver
from selenium.common.exceptions import ElementNotVisibleException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait

from time import sleep, time


@contextmanager
def wait_for_page_load(driver, timeout=30.0):
    source = driver.page_source
    yield
    WebDriverWait(
        driver, timeout, ignored_exceptions=(WebDriverException,)
    ).until(lambda d: source != d.page_source)


class BaseCrawler(object):

    def __init__(self, min_delay=2, dynamic_delay=True):
        """By default the crawler will measure the average time a page takes to load and
        waits that amount of time (minimum of 2 seconds by default). If you want it to always
        wait a constant period of time, set dynamic_delay to False. It will then always
        wait <min_delay> number of seconds.
        """
        self.driver = webdriver.Firefox()
        self.min_delay = min_delay  # seconds to wait for infinite scroll items to populate
        self.loads = 0
        self.load_time = 0
        self.dynamic_delay = dynamic_delay

        # shorter funciton for executing javascript
        self.js = self.driver.execute_script

    def __del__(self):
        self.driver.quit()

    def _update_delay(self, seconds):
        self.load_time += seconds
        self.loads += 1

    def delay(self, multiplier=1):
        """Sleeps the average amount of time it has taken to load a page or at least self.min_delay seconds.
        Multiplier is how much more or less time you want to wait. e.g. multiplier=2 would wait 2 times
        as long as usual.
        """
        if self.loads == 0:
            secs = self.min_delay
        else:
            avg = self.load_time / self.loads
            secs = max(avg, self.min_delay) if self.dynamic_delay else self.min_delay
            secs *= multiplier
        log.info('Sleeping %f seconds', secs)
        sleep(secs)

    def load(self, url, force=False, scroll=True):
        """Load url in the browser if it's not already loaded. Use force=True to force a reload.
        Also keeps track of how long it has taken to load.
        If scroll is True (default) it will scroll to the bottom once load is complete (to trigger infinite scroll).
        """
        if url == self.driver.current_url and not force:
            return
        start = time()
        with wait_for_page_load(self.driver):
            self.driver.get(url)
        self._update_delay(time() - start)
        if scroll:
            self.scroll_to_bottom()

    def centre_on_element(self, el, wait=False):
        self.js('window.scrollTo(0, arguments[0].getBoundingClientRect().top + window.pageYOffset - window.innerHeight /2)', el)
        if wait:
            self.delay()

    def scroll_to_bottom(self, wait=False):
        """Scrolls to the bottom of the page. Useful for triggering infinite scroll.
        If wait is true (false by default), it will wait for potential items to populate before returning.
        """
        self.js("window.scrollTo(0, document.body.scrollHeight);")
        if wait:
            self.delay()


    def force_click(self, parent, clickable):
        """Will attempt to click on clickable 3 times. Assume you can tell if it was successful if the text
        of the parent changes.
        Waits 0.5 seconds after each click. On the last attempt, wait the full delay duration.
        Returns True if the text of the parent changed.
        """
        try:
            post_text = parent.text
            attempts = 3
            self.centre_on_element(clickable)
            while post_text == parent.text and attempts > 0:
                attempts -= 1
                clickable.click()
                sleep(0.5)
                if attempts == 1:
                    self.delay()
            return post_text != parent.text
        except (WebDriverException, ElementNotVisibleException):
            return False


    def get_bg_img_url(self, el):
        """Gets the image url of the element el with css style background-image
        """
        # get the img
        img = self.js("""var element = arguments[0],
        style = element.currentStyle || window.getComputedStyle(element, false);
        return style['background-image'];""", el)
        # strip the img part
        if img[:4] == 'url(':
            img = img[4:]
        if img[-1] == ')':
            img = img[:-1]
        return img.strip("'").strip('"')
