from time import time

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import SlideTransition

import os
import sys

from preaction import BaseAction
from searchview import background

file_path = os.path.dirname(os.path.abspath(__file__))
# add the parent directory to the path to import fbscrape
sys.path.append(os.path.dirname(file_path))

KIVY_FILE = 'eventview.kv'
kivy_file_path = os.path.join(file_path, KIVY_FILE)
Builder.load_file(kivy_file_path)


class EventSettings(BaseAction):

    def which_guests(self):
        res = []
        if self.ids.interested.active:
            res.append('interested')
        if self.ids.going.active:
            res.append('going')
        if self.ids.invited.active:
            res.append('invited')
        return res

    @background
    def do_scrape(self, names):
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'logging'
        log_screen = self.manager.get_screen('logging')
        log_screen.reset()
        app = App.get_running_app()
        app.controller.restart()  # restart the scraper
        start = time()
        all_names = [x.strip() for x in names.split(os.linesep) if x.strip()]
        for index, n in enumerate(all_names):
            if app.stop_request:
                break
            log_screen.ids.current_user.text = n
            log_screen.ids.count.text = 'Scraping {} of {}'.format(index + 1, len(all_names))
            app.controller.scrape_event_guests(n, self.which_guests())
        self.scrape_complete(time() - start)
        app.stop_request = False

    @background
    def go_back(self):
        self.ids.back_btn.disabled = True

        def callback():
            self.ids.back_btn.disabled = False
            self.manager.transition = SlideTransition(direction='down')
            self.manager.current = 'settings'

        # interrupt running threads, restart, and then transition back
        App.get_running_app().controller.interrupt(callback, True)
