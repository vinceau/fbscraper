from kivy.uix.screenmanager import Screen, SlideTransition

from kivy.lang import Builder

Builder.load_file('searchview.kv')


class SearchScreen(Screen):

    def go_back(self):
        self.manager.transition = SlideTransition(direction='down')
        self.manager.current = 'settings'
