from kivy.app import App

from kivy.uix.boxlayout import BoxLayout


class LoginBox(BoxLayout):
    pass


class MainForm(BoxLayout):
    pass


class FBScraperApp(App):
    def build(self):
        return MainForm()


if __name__ == '__main__':
    FBScraperApp().run()
