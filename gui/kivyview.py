from __future__ import division

import pickle
import logging
import os

from os.path import join, isdir, expanduser, isfile
from time import time
from tempfile import gettempdir

from kivy.app import App
from kivy.config import Config
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty

# local imports
from searchview import SearchScreen, background
from preaction import BaseAction
from eventview import EventSettings

version = '1.7'
last_updated = '10 July 2017'

Config.set('input', 'mouse', 'mouse,disable_multitouch')

UPLOAD_DIR = gettempdir()
SETTINGS_FILE = join(UPLOAD_DIR, 'fbscraper.bin')


class Login(Screen):
    login_file = ObjectProperty(None)

    def load_creds(self):
        """Populate the form with the credentials found in login.txt
        """
        try:
            with open(self.login_file, 'r') as f:
                lines = f.readlines()
                if len(lines) < 2:
                    return
                self.ids.login.text = lines[0].strip()
                self.ids.password.text = lines[1].strip()
                self.ids.storecreds.active = True
        except IOError:
            # no login saved
            pass

    def save_creds(self):
        try:
            with open(self.login_file, 'w+') as f:
                if not self.ids.storecreds.active:
                    return
                fbemail = self.ids.login.text
                fbpass = self.ids.password.text
                f.write('{}{}{}'.format(fbemail, os.linesep, fbpass))
        except IOError:
            pass

    @background
    def do_login(self, fbemail, fbpass):
        if fbemail and fbpass:
            self.ids.loginbutton.disabled = True
            app = App.get_running_app()
            if app.controller.login(fbemail, fbpass):
                self.ids.fail.opacity = 0
                self.manager.transition = SlideTransition(direction='left')
                self.manager.current = 'settings'
            else:
                self.ids.fail.opacity = 1
            self.ids.loginbutton.disabled = False


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    hide_files = ObjectProperty(False)  # will only show directories if True

    def __init__(self, **kwargs):
        FloatLayout.__init__(self, **kwargs)
        # set the filechooser to start at the home directory by default
        self.ids.filechooser.path = expanduser('~')

    def is_dir(self, folder, filename):
        """Will be used as a selection filter if hide_files is True
        """
        return isdir(join(folder, filename))


class AdvancedSettings(FloatLayout):
    cancel = ObjectProperty(None)

    def __init__(self, **kwargs):
        FloatLayout.__init__(self, **kwargs)
        self.all_boxes = [self.ids.posts, self.ids.friends, self.ids.photos,
                          self.ids.albums, self.ids.checkins,
                          self.ids.likes, self.ids.about, self.ids.groups]
        self.load_settings()

    def load_settings(self):
        """Load the settings from app settings.
        """
        app = App.get_running_app()
        self.ids.foldername.text = app.settings['foldername']
        self.ids.filename.text = app.settings['filename']
        self.ids.scraperange.active = app.settings['scraperange']
        self.ids.startyear.text = app.settings['startyear']
        self.ids.endyear.text = app.settings['endyear']

        s = app.settings['controller_settings']
        for b in self.all_boxes:
            b.active = s[b.ref]

    def activate_settings(self):
        """Push the current settings onto the controller.
        """
        fbs = App.get_running_app().controller
        fbs.foldernaming = self.ids.foldername.text
        fbs.filenaming = self.ids.filename.text

        fbs.post_range = []
        if self.ids.scraperange.active:
            try:
                sy = int(self.ids.startyear.text)
                ey = int(self.ids.endyear.text) + 1
                fbs.post_range = range(sy, ey)
            except ValueError:
                pass

        for b in self.all_boxes:
            fbs.settings[b.ref] = b.active

    def save_settings(self):
        """Save the settings back to app settings
        """
        app = App.get_running_app()
        app.settings['foldername'] = self.ids.foldername.text
        app.settings['filename'] = self.ids.filename.text
        app.settings['scraperange'] = self.ids.scraperange.active
        app.settings['startyear'] = self.ids.startyear.text
        app.settings['endyear'] = self.ids.endyear.text

        for b in self.all_boxes:
            app.settings['controller_settings'][b.ref] = b.active

        app.save_settings()

        self.activate_settings()
        self.cancel()

    def toggle(self):
        tally = [x.active for x in self.all_boxes]
        for x in self.all_boxes:
            x.active = tally.count(True) / len(tally) < 0.5


class Settings(BaseAction):
    infile = ObjectProperty(None)

    def __init__(self, **kwargs):
        BaseAction.__init__(self, **kwargs)
        if self.infile:
            self._load_file(self.infile)

    def _load_file(self, filename):
        with open(filename, 'r') as f:
            self.ids.names.text = ''.join(f.readlines())

    def add_target(self, url):
        self.ids.names.text += url + os.linesep

    def load_file(self):
        def select(path, filename):
            self._load_file(filename[0])
            self.dismiss_popup()

        content = LoadDialog(load=select, cancel=self.dismiss_popup)
        self._popup = Popup(title='Load from file', content=content, size_hint=(.9, .9))
        self._popup.open()

    def search_view(self):
        self.manager.transition = SlideTransition(direction='up')
        self.manager.current = 'search'

    def event_view(self):
        self.manager.transition = SlideTransition(direction='up')
        self.manager.current = 'events'

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
            app.controller.scrape(n)
        self.scrape_complete(time() - start)
        app.stop_request = False

    def choosedir(self):
        def dirsel(path, filename):
            if len(filename) == 0:
                self.ids.pathbox.text = path
            else:
                self.ids.pathbox.text = filename[0]
            app = App.get_running_app()
            app.controller.set_output_dir(self.ids.pathbox.text)
            self.dismiss_popup()

        content = LoadDialog(load=dirsel, cancel=self.dismiss_popup, hide_files=True)
        self._popup = Popup(title='Output Directory', content=content, size_hint=(.9, .9))
        self._popup.open()

    def adv_settings(self):
        content = AdvancedSettings(cancel=self.dismiss_popup)
        self._popup = Popup(title='Advanced Settings', content=content, size_hint=(.9, .9))
        self._popup.open()


class Logging(Screen):

    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)
        self.max = 30  # the number of recent messages to show
        self.reset()

    def reset(self):
        self.log = [''] * self.max
        self.current = 0
        self.ids.pause.disabled = False
        self.ids.stop.disabled = False
        self.ids.logtext.text = ''

    def add_log(self, text):
        if not text.strip():
            return
        new_text = text.encode('ascii', 'replace')
        self.log[self.current % self.max] = new_text + os.linesep
        self.current += 1
        self._update()

    def pause(self):
        fbs = App.get_running_app().controller
        if fbs.pause_request:
            # we are currently paused, request to unpause
            fbs.unpause()
            self.ids.pause.text = 'Pause'
        else:
            # we are not currently paused, request to pause
            self._pause_worker()

    @background
    def _pause_worker(self):
        self.ids.pause.disabled = True
        fbs = App.get_running_app().controller
        fbs.pause()  # send in a pause request
        while not fbs.status == 'paused':
            pass
        # we are paused now
        self.ids.pause.text = 'Unpause'
        self.ids.pause.disabled = False

    @background
    def stop(self):
        self.ids.stop.disabled = True
        self.ids.pause.disabled = True
        app = App.get_running_app()
        app.stop_request = True
        app.controller.interrupt()


    def _update(self):
        """This will print out the messages in the log in reverse order.
        Taking into account its cyclic nature.
        """
        last = (self.current - 1) % self.max
        self.ids.logtext.text = ''.join(self.log[last::-1] + self.log[:last:-1])


class LogHandler(logging.Handler):

    def __init__(self, logscreen):
        logging.Handler.__init__(self)
        self.logscreen = logscreen

    def emit(self, record):
        log_entry = self.format(record)
        self.logscreen.add_log(log_entry)


class FBScraperApp(App):
    version = version
    last_updated = last_updated

    def __init__(self, controller, loginfile='login.txt', infile=''):
        """<controller> is an instance of fbscrape.FBScraper
        <loginfile> is the default file to store credentials in
        <infile> is the file to read targets into the target list
        """
        App.__init__(self)
        self.stop_request = False
        self.controller = controller
        self.loginfile = loginfile
        self.infile = infile
        self.default_settings = {
            'scraperange': False,
            'startyear': '',
            'endyear': '',
            'foldername': controller.foldernaming,
            'filename': controller.filenaming,
            'controller_settings': controller.settings,
        }
        self.settings = self.get_settings()


    def get_settings(self):
        if isfile(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                return pickle.load(f)
        return self.default_settings

    def save_settings(self):
        with open(SETTINGS_FILE, 'wb') as f:
            pickle.dump(self.settings, f)

    def on_stop(self):
        self.save_settings()
        self.controller.interrupt()
        self.controller.driver.quit()

    def build(self):
        manager = ScreenManager()
        manager.add_widget(Login(name='login', login_file=self.loginfile))
        manager.add_widget(Settings(name='settings', infile=self.infile))
        manager.add_widget(SearchScreen(name='search'))
        manager.add_widget(EventSettings(name='events'))
        logscreen = Logging(name='logging')
        log = logging.getLogger()
        log.addHandler(LogHandler(logscreen))
        manager.add_widget(logscreen)

        return manager
