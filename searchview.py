from kivy.app import App
from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.uix.behaviors.togglebutton import ToggleButtonBehavior

from threading import Thread

from fbscrape import search

Builder.load_file('searchview.kv')


class Filter(BoxLayout):
    label = ObjectProperty('')
    search_filter = ObjectProperty(None)
    callback = ObjectProperty(None)

    def remove(self):
        self.parent.height -= self.height
        self.parent.remove_widget(self)
        self.callback()


class SearchScreen(Screen):

    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)
        self.fm = search.FilterManager()

    def go_back(self):
        self.manager.transition = SlideTransition(direction='down')
        self.manager.current = 'settings'

    def set_option(self):
        selected = 'down' in [x.state for x in ToggleButtonBehavior.get_widgets('options')]
        self.ids.textinput.disabled = not selected
        if not selected:
            self.ids.textinput.text = ''

    def add_option(self):
        btns = [x for x in ToggleButtonBehavior.get_widgets('options') if x.state == 'down']
        if len(btns) > 0:
            self.add_filter(btns[0], self.ids.textinput.text)
            self.ids.textinput.text = ''

    def add_filter(self, btn, fopt=''):
        label = '{} {}'.format(btn.text, fopt)
        if btn.ident == 'male':
            s = search.male()
            self.ids.male.disabled = True
            self.ids.female.disabled = True
        elif btn.ident == 'female':
            s = search.female()
            self.ids.male.disabled = True
            self.ids.female.disabled = True
        elif btn.ident == 'named':
            s = search.people_named(fopt)
        elif btn.ident == 'friends':
            s = search.friends_with(fopt)
        elif btn.ident == 'lives':
            s = search.lives_in(fopt)
        elif btn.ident == 'likes':
            s = search.likes_page(fopt)

        def cb():
            # re-enable the male or female buttons
            if btn.ident == 'male' or btn.ident == 'female':
                self.ids.male.disabled = False
                self.ids.female.disabled = False
            # remove the filters
            self.fm.remove(s)
            # disable search button if we're out of filters
            self.ids.search_btn.disabled = len(self.fm.filters) == 0

        f = Filter(label=label, search_filter=s, callback=cb)
        self.ids.scrollview.add_widget(f)
        self.ids.scrollview.height += f.height
        self.fm.add(f.search_filter)
        self.ids.search_btn.disabled = False


    def _search_worker(self):
        self.ids.search_btn.disabled = True
        url = self.fm.execute()
        if url:
            #print(url)
            App.get_running_app().controller.load(url)
        self.ids.search_btn.disabled = False


    def search(self):
        Thread(target=self._search_worker).start()
