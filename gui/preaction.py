from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.uix.popup import Popup
from kivy.properties import ObjectProperty


class CompleteDialog(FloatLayout):
    dismiss = ObjectProperty(None)
    notice = ObjectProperty(None)


class BaseAction(Screen):
    scrape_func = ObjectProperty(None)

    def scrape_complete(self, elapsed):
        hours, rem = divmod(elapsed, 3600)
        mins, secs = divmod(rem, 60)
        notice = 'Time elapsed: {:d} hours, {:d} minutes and {:d} seconds'.format(int(hours), int(mins), int(secs))

        def go_back():
            self.dismiss_popup()
            self.manager.transition = SlideTransition(direction='right')
            self.manager.current = self.name
            App.get_running_app().controller.restart()  # restart the scraper

        content = CompleteDialog(notice=notice, dismiss=go_back)
        self._popup = Popup(title='Scrape Complete', content=content, size_hint=(.4, .4), auto_dismiss=False)
        self._popup.open()

    def dismiss_popup(self):
        self._popup.dismiss()
