from __future__ import division

import logging
import os

from os.path import join, isdir, expanduser
from threading import Thread
from time import time

from kivy.app import App
from kivy.config import Config
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty

# local imports
from model import FBScraper


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


class CompleteDialog(FloatLayout):
    dismiss = ObjectProperty(None)
    notice = ObjectProperty(None)


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)

    def __init__(self, **kwargs):
        FloatLayout.__init__(self, **kwargs)
        # set the filechooser to start at the home directory by default
        self.ids.filechooser.path = expanduser('~')

    def is_dir(self, folder, filename):
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

    def do_scrape(self, names):
        Thread(target=self._scrape_worker, args=(names, )).start()

    def _scrape_worker(self, names):
        self.manager.transition = SlideTransition(direction='left')
        self.manager.current = 'logging'
        current_label = self.manager.get_screen('logging').ids.current_user
        count_label = self.manager.get_screen('logging').ids.count
        app = App.get_running_app()
        start = time()
        all_names = [x.strip() for x in names.split(os.linesep) if x.strip()]
        for index, n in enumerate(all_names):
            current_label.text = n
            count_label.text = 'Scraping {} of {}'.format(index + 1, len(all_names))
            app.controller.scrape(n.strip())
        self.scrape_complete(time() - start)

    def scrape_complete(self, elapsed):
        hours, rem = divmod(elapsed, 3600)
        mins, secs = divmod(rem, 60)
        notice = 'Time elapsed: {:d} hours, {:d} minutes and {:d} seconds'.format(int(hours), int(mins), int(secs))
        content = CompleteDialog(notice=notice, dismiss=self.go_back)
        self._popup = Popup(title='Scrape Complete', content=content, size_hint=(.4, .4))
        self._popup.open()

    def go_back(self):
        self.dismiss_popup()
        self.manager.transition = SlideTransition(direction='right')
        self.manager.current = 'settings'


    def choosedir(self):
        content = LoadDialog(load=self.dirsel, cancel=self.dismiss_popup)
        self._popup = Popup(title='Output Directory', content=content, size_hint=(.9, .9))
        self._popup.open()

    def adv_settings(self):
        content = AdvancedSettings(cancel=self.dismiss_popup)
        self._popup = Popup(title='Advanced Settings', content=content, size_hint=(.9, .9))
        self._popup.open()

    def dismiss_popup(self):
        self._popup.dismiss()

    def dirsel(self, path, filename):
        if len(filename) == 0:
            self.ids.pathbox.text = path
        else:
            self.ids.pathbox.text = filename[0]
        app = App.get_running_app()
        app.controller.set_output_dir(self.ids.pathbox.text)
        self.dismiss_popup()


class Logging(Screen):

    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)
        self.max = 30  # the number of recent messages to show
        self.log = [''] * self.max
        self.current = 0

    def add_log(self, text):
        if not text.strip():
            return
        new_text = text.encode('ascii', 'replace')
        self.log[self.current % self.max] = new_text + os.linesep
        self.current += 1
        self._update()

    def pause(self):
        fbs = App.get_running_app().controller
        if fbs.paused:
            fbs.unpause()
            self.ids.pause.text = 'Pause'
        else:
            fbs.pause()
            self.ids.pause.text = 'Unpause'

    def stop(self):
        self.ids.stop.disabled = True
        self.ids.pause.disabled = True
        App.get_running_app().controller.interrupt()


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

    def __init__(self, outputdir='', loginfile='login.txt', infile=''):
        App.__init__(self)
        self.controller = FBScraper(outputdir)
        self.loginfile = loginfile
        self.infile = infile

    def on_stop(self):
        self.controller.driver.quit()

    def build(self):
        manager = ScreenManager()
        manager.add_widget(Login(name='login', login_file=self.loginfile))
        manager.add_widget(Settings(name='settings', infile=self.infile))
        logscreen = Logging(name='logging')
        log = logging.getLogger()
        log.addHandler(LogHandler(logscreen))
        manager.add_widget(logscreen)

        return manager


def run_app(outputdir='', loginfile='login.txt', infile=''):
    Config.set('input', 'mouse', 'mouse,disable_multitouch')
    FBScraperApp(outputdir, loginfile, infile).run()


if __name__ == '__main__':
    run_app()
