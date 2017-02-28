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
            controller = app.controller
            if controller.login(fbemail, fbpass):
                self.ids.fail.opacity = 0
                self.manager.transition = SlideTransition(direction='left')
                self.manager.current = 'settings'
                return
        self.ids.fail.opacity = 1


class Settings(Screen):
    pass


class FBScraperApp(App):

    def __init__(self):
        App.__init__(self)
        self.controller = FBScraper()

    def build(self):
        manager = ScreenManager()
        manager.add_widget(Login(name='login'))
        manager.add_widget(Settings(name='settings'))

        return manager


if __name__ == '__main__':
    FBScraperApp().run()
