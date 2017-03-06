
import logging
import os

from os.path import join, isdir
from threading import Thread

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty

#local imports
from model import FBScraper


class Login(Screen):

    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)
        self.login_file = 'login.txt'

    """Populate the form with the credentials found in login.txt
    """
    def load_creds(self):
        try:
            with open(self.login_file, 'r') as f:
                lines = f.readlines()
                if len(lines) < 2:
                    return
                self.ids.login.text = lines[0].strip()
                self.ids.password.text = lines[1].strip()
                self.ids.storecreds.active = True
        except IOError:
            #no login saved
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


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)

    def is_dir(self, folder, filename):
        return isdir(join(folder, filename))



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

    def choosedir(self):
        content = LoadDialog(load=self.dirsel, cancel=self.dismiss_popup)
        self._popup = Popup(title='Output Directory', content=content, size_hint=(.9, .9))
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
        new_text = text.decode('utf-8').encode('ascii', errors='ignore')
        self.log[self.current % self.max] = new_text + os.linesep
        self.current += 1
        self._update()

    """This will print out the messages in the log in reverse order.
    Taking into account its cyclic nature.
    """
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
