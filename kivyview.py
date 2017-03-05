
import logging
import os

from kivy.app import App

from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition

from threading import Thread

#local imports
from model import FBScraper


class Login(Screen):
    def do_login(self, fbemail, fbpass):
        Thread(target=self._login_worker, args=(fbemail, fbpass)).start()

    def _login_worker(self, fbemail, fbpass):
        if fbemail and fbpass:
            app = App.get_running_app()
            if app.controller.login(fbemail, fbpass):
                self.ids.fail.opacity = 0
                self.manager.transition = SlideTransition(direction='left')
                self.manager.current = 'settings'
                return
        self.ids.fail.opacity = 1


class Settings(Screen):

    def do_scrape(self, names):
        Thread(target=self._scrape_worker, args=(names, )).start()

    def _scrape_worker(self, names):
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'logging'
        app = App.get_running_app()
        for n in names.split(os.linesep):
            if n.strip():
                app.controller.scrape(n)


class Logging(Screen):

    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)
        self.max = 50  # the number of recent messages to show
        self.log = [''] * self.max
        self.current = 0

    def add_log(self, text):
        if not text.strip():
            return
        new_text = text.decode('utf-8').encode('ascii', errors='ignore')
        self.log[self.current % self.max] = new_text + os.linesep
        self.current += 1
        self._update()

    def _update(self):
        last = (self.current - 1) % self.max
        self.ids.logtext.text = ''.join(self.log[last::-1] + self.log[:last:-1])


class LogHandler(logging.Handler):

    def __init__(self, logscreen):
        logging.Handler.__init__(self)
        self.logscreen = logscreen

    def emit(self, record):
        log_entry = self.format(record)
        self.logscreen.add_log(log_entry)
        #print(log_entry.upper())


class FBScraperApp(App):

    def __init__(self):
        App.__init__(self)
        self.controller = FBScraper()

    def build(self):
        manager = ScreenManager()
        manager.add_widget(Login(name='login'))
        manager.add_widget(Settings(name='settings'))
        logscreen = Logging(name='logging')
        log = logging.getLogger()
        log.addHandler(LogHandler(logscreen))
        manager.add_widget(logscreen)

        return manager


if __name__ == '__main__':
    FBScraperApp().run()
