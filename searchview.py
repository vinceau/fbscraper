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


def background(func):
    """This is a decorator in order to set the status as running when running
    and the status as ready when action is complete
    """
    def do_stuff(*args, **kwargs):
        Thread(target=func, args=(args), kwargs=(kwargs)).start()
        return
    return do_stuff


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
    load_friends = ObjectProperty(None)

    def __init__(self, **kwargs):
        BoxLayout.__init__(self, **kwargs)
        self.working = False
        self.ids.check.bind(active=self.on_checkbox_active)

    @background
    def show_profile(self):
        fbs = App.get_running_app().controller
        if fbs.status == 'running' or fbs.status == 'paused':
            fbs.interrupt()
        fbs.load(self.url)

    def on_checkbox_active(self, checkbox, value):
        """Keep track of how many check boxes have been checked
        """
        if value:
            self.parent.count += 1
        else:
            self.parent.count -= 1


class SearchResults(FloatLayout):
    url = ObjectProperty('')
    cancel = ObjectProperty(None)
    manager = ObjectProperty(None)
    limit = ObjectProperty(def_limit)

    def __init__(self, **kwargs):
        FloatLayout.__init__(self, **kwargs)
        self._search_worker()

    @background
    def load_friends(self, url):
        """Stop whatever we're doing and load the friends of the target at url
        """
        fbs = App.get_running_app().controller
        # stop and restart the controller
        fbs.interrupt()
        fbs.restart()

        # reset the search results screen
        #self.has_results(1)  # hide the "no results" if currently shown
        if self.event:
            self.event.cancel()
        self.ids.grid.count = 0
        self.ids.grid.clear_widgets()
        self.ids.pause.disabled = False
        self.ids.stop.disabled = False

        # get the new list of friends
        res = fbs.crawl_friends(url, self.cb)
        self.has_results(res)

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
        while fbs.status != 'paused':
            pass
        # we are paused now
        self.ids.pause.text = 'Unpause'
        self.ids.pause.disabled = False

    @background
    def stop(self):
        self.ids.stop.disabled = True
        self.ids.pause.disabled = True
        App.get_running_app().controller.interrupt()

    def cb(self, name, url, imageurl, count):
        """The callback for adding profiles to the search result pane
        """
        def clock(dt):
            i = ResultItem(source=imageurl, text=name, url=url, load_friends=self.load_friends)
            self.ids.grid.add_widget(i)
        self.event = Clock.schedule_once(clock)

    @background
    def _search_worker(self):
        fbs = App.get_running_app().controller
        fbs.restart()
        limit = min(max_limit, self.limit)
        res = fbs.crawl_search_results(self.url, self.cb, limit)
        self.has_results(res)

    def has_results(self, count):
        """Executed once the results have finished loading.
        """
        if count == 0:
            self.ids.no_results.opacity = 1
            self.ids.no_results.height = 100
            self.ids.no_results.size_hint_y = 1
        else:
            self.ids.no_results.opacity = 0
            self.ids.no_results.height = '0dp'
            self.ids.no_results.size_hint_y = None

        # disable interrupt buttons
        self.ids.pause.disabled = True
        self.ids.stop.disabled = True

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

        @background
        def stop_search(instance):
            fbs = App.get_running_app().controller
            if fbs.status != 'ready' or fbs.status != 'stopped':
                fbs.interrupt()

        self._popup.bind(on_dismiss=stop_search)
        self._popup.open()

    def dismiss_popup(self):
        self._popup.dismiss()
