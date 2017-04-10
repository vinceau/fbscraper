from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from kivy.uix.behaviors.togglebutton import ToggleButtonBehavior
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen, SlideTransition

from threading import Thread

from fbscrape import search

Builder.load_file('searchview.kv')

max_limit = 150
def_limit = 20


class Filter(BoxLayout):
    label = ObjectProperty('')
    search_filter = ObjectProperty(None)
    callback = ObjectProperty(None)

    def remove(self):
        self.parent.remove_widget(self)
        self.callback()


class ResultItem(BoxLayout):
    source = ObjectProperty('')
    text = ObjectProperty('')
    url = ObjectProperty('')
    get_friends = ObjectProperty(None)

    def __init__(self, **kwargs):
        BoxLayout.__init__(self, **kwargs)
        self.working = False

    def show_profile(self):
        if not self.working:
            Thread(target=self._worker).start()

    def _worker(self):
        self.working = True
        App.get_running_app().controller.load(self.url)
        self.working = False

    def load_friends(self, url):
        Thread(target=self._friends_worker, args=(url,)).start()

    def _friends_worker(self, url):
        self.parent.clear_widgets()
        self.get_friends(url)


class SearchResults(FloatLayout):
    url = ObjectProperty('')
    cancel = ObjectProperty(None)
    manager = ObjectProperty(None)
    limit = ObjectProperty(def_limit)

    def __init__(self, **kwargs):
        FloatLayout.__init__(self, **kwargs)
        Thread(target=self._search_worker).start()

    def get_friends(self, url):
        res = App.get_running_app().controller.crawl_friends(url, self.cb)
        self.has_results(res)

    def cb(self, name, url, imageurl, count):
        """The callback for adding profiles to the search result pane
        """
        def clock(dt):
            i = ResultItem(source=imageurl, text=name, url=url, get_friends=self.get_friends)
            self.ids.grid.add_widget(i)
        Clock.schedule_once(clock)

    def _search_worker(self):
        limit = min(max_limit, self.limit)
        res = App.get_running_app().controller.crawl_search_results(self.url, self.cb, limit)
        self.has_results(res)

    def has_results(self, count):
        if count == 0:
            self.ids.no_results.opacity = 1
            self.ids.no_results.height = 100
            self.ids.no_results.size_hint_y = 1
        else:
            self.ids.no_results.opacity = 0
            self.ids.no_results.height = '0dp'
            self.ids.no_results.size_hint_y = None

    def toggle_all(self):
        tally = [x.ids.check.active for x in self.ids.grid.children]
        for x in self.ids.grid.children:
            x.ids.check.active = tally.count(True) / len(tally) < 0.5

    def add_to_queue(self):
        screen = self.manager.get_screen('settings')
        for x in self.ids.grid.children:
            if x.ids.check.active:
                screen.add_target(x.url)


class SearchScreen(Screen):

    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)
        self.fm = search.FilterManager()

    def _check(self):
        """Function to check the results limiting is correct
        """
        try:
            num = int(self.ids.res_lim.text)
            if num <= 0:
                self.ids.res_lim.text = str(def_limit)
            elif num > max_limit:
                self.ids.res_lim.text = str(max_limit)
        except ValueError:
            self.ids.res_lim.text = str(def_limit)

        return int(self.ids.res_lim.text)

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
        self.fm.add(f.search_filter)
        self.ids.search_btn.disabled = False

    def search(self, limit):
        url = self.fm.execute()
        content = SearchResults(cancel=self.dismiss_popup, url=url, manager=self.manager, limit=self._check())
        self._popup = Popup(title='Search Results', content=content, size_hint=(.9, .9))
        self._popup.open()

    def dismiss_popup(self):
        self._popup.dismiss()
