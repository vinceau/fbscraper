from __future__ import division

import logging
import os

from os.path import join, isdir, expanduser
from time import time

from kivy.app import App
from kivy.config import Config
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty

# local imports
from searchview import SearchScreen, background

version = '1.5'
last_updated = '22 May 2017'

Config.set('input', 'mouse', 'mouse,disable_multitouch')


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


class CompleteDialog(FloatLayout):
    dismiss = ObjectProperty(None)
    notice = ObjectProperty(None)


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
        self.load_settings()

    def load_settings(self):
        fbs = App.get_running_app().controller
        self.ids.foldername.text = fbs.foldernaming
        self.ids.filename.text = fbs.filenaming

        s = fbs.settings
        self.ids.posts.active = s['posts']
        self.ids.friends.active = s['friends']
        self.ids.photos.active = s['photos']
        self.ids.likes.active = s['likes']
        self.ids.about.active = s['about']
        self.ids.groups.active = s['groups']


    def save_settings(self):
        fbs = App.get_running_app().controller
        fbs.foldernaming = self.ids.foldername.text
        fbs.filenaming = self.ids.filename.text

        s = fbs.settings
        s['posts'] = self.ids.posts.active
        s['friends'] = self.ids.friends.active
        s['photos'] = self.ids.photos.active
        s['likes'] = self.ids.likes.active
        s['about'] = self.ids.about.active
        s['groups'] = self.ids.groups.active
        # close popup
        self.cancel()

    def toggle(self):
        all_boxes = [self.ids.posts, self.ids.friends, self.ids.photos,
                     self.ids.likes, self.ids.about, self.ids.groups]
        tally = [x.active for x in all_boxes]
        for x in all_boxes:
            x.active = tally.count(True) / len(tally) < 0.5


class Settings(Screen):
    infile = ObjectProperty(None)

    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)
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

    def scrape_complete(self, elapsed):
        hours, rem = divmod(elapsed, 3600)
        mins, secs = divmod(rem, 60)
        notice = 'Time elapsed: {:d} hours, {:d} minutes and {:d} seconds'.format(int(hours), int(mins), int(secs))

        def go_back():
            self.dismiss_popup()
            self.manager.transition = SlideTransition(direction='right')
            self.manager.current = 'settings'
            App.get_running_app().controller.restart()  # restart the scraper

        content = CompleteDialog(notice=notice, dismiss=go_back)
        self._popup = Popup(title='Scrape Complete', content=content, size_hint=(.4, .4), auto_dismiss=False)
        self._popup.open()

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

    def dismiss_popup(self):
        self._popup.dismiss()


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

    def on_stop(self):
        self.controller.interrupt()
        self.controller.driver.quit()

    def build(self):
        manager = ScreenManager()
        manager.add_widget(Login(name='login', login_file=self.loginfile))
        manager.add_widget(Settings(name='settings', infile=self.infile))
        manager.add_widget(SearchScreen(name='search'))
        logscreen = Logging(name='logging')
        log = logging.getLogger()
        log.addHandler(LogHandler(logscreen))
        manager.add_widget(logscreen)

        return manager
