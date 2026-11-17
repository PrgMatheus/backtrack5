from kivy.app import App
from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from terminal import BackTrackTerminal

KV = """
#:import dp kivy.metrics.dp

<MainButton@Button>:
    background_normal: ''
    background_color: (0.17, 0.17, 0.17, 1)
    color: (1, 1, 1, 1)
    font_size: '15sp'
    size_hint_y: None
    height: dp(65)

<BackButton@Button>:
    background_normal: ''
    background_color: (0.65, 0.04, 0.04, 1)
    size_hint_y: None
    height: dp(48)

ScreenManager:
    Screen:
        name: 'home'
        BoxLayout:
            orientation: 'vertical'
            padding: dp(15)
            spacing: dp(12)

            canvas.before:
                Color:
                    rgba: (0.035, 0.035, 0.045, 1)
                Rectangle:
                    pos: self.pos
                    size: self.size

            Label:
                text: '[b][color=ff2929]BACKTRACK[/color] [color=ffffff]5[/color][/b]'
                markup: True
                font_size: '32sp'
                size_hint_y: None
                height: dp(75)

            Label:
                text: '[color=ff3333]MOBILE // ULTIMATE SUITE[/color]'
                markup: True
                size_hint_y: None
                height: dp(35)

            Label:
                text: 'PAINEL DE CONTROLE'
                color: (0.7,0.7,0.7,1)
                size_hint_y: None
                height: dp(35)

            ScrollView:
                GridLayout:
                    cols: 1
                    spacing: dp(10)
                    size_hint_y: None
                    height: self.minimum_height

                    MainButton:
                        text: '⌨   BASHBT5 TERMINAL'
                        on_release: app.show_screen('terminal')

                    MainButton:
                        text: '◉   WI-FI E WIRELESS'
                        on_release: app.show_screen('wifi')

                    MainButton:
                        text: '◎   REDE E CONECTIVIDADE'
                        on_release: app.show_screen('network')

                    MainButton:
                        text: '⌘   ANÁLISE WEB'
                        on_release: app.show_screen('web')

                    MainButton:
                        text: '▤   RELATÓRIOS E RESULTADOS'
                        on_release: app.show_screen('reports')

                    MainButton:
                        text: '⚙   CONFIGURAÇÕES'
                        on_release: app.show_screen('settings')

            Label:
                text: '[color=00cc66]● INTERFACE INICIAL[/color]'
                markup: True
                size_hint_y: None
                height: dp(35)

    Screen:
        name: 'wifi'
        BoxLayout:
            orientation: 'vertical'
            padding: dp(15)
            spacing: dp(12)
            Label:
                text: '[b][color=ff2929]WI-FI & WIRELESS[/color][/b]'
                markup: True
                font_size: '23sp'
                size_hint_y: None
                height: dp(65)
            MainButton:
                text: 'Scanner de redes Wi-Fi'
                on_release: app.show_message('Wi-Fi', 'Integração Android em preparação.')
            MainButton:
                text: 'Informações da conexão'
                on_release: app.show_message('Conexão', 'Integração Android em preparação.')
            MainButton:
                text: 'Diagnóstico do adaptador'
                on_release: app.show_message('Diagnóstico', 'Módulo em preparação.')
            BackButton:
                text: 'VOLTAR'
                on_release: app.show_screen('home')

    Screen:
        name: 'network'
        BoxLayout:
            orientation: 'vertical'
            padding: dp(15)
            spacing: dp(12)
            Label:
                text: '[b][color=ff2929]REDE E CONECTIVIDADE[/color][/b]'
                markup: True
                font_size: '23sp'
                size_hint_y: None
                height: dp(65)
            MainButton:
                text: 'Diagnóstico de conexão'
                on_release: app.show_message('Rede', 'Módulo em preparação.')
            MainButton:
                text: 'Consulta DNS'
                on_release: app.show_message('DNS', 'Módulo em preparação.')
            MainButton:
                text: 'Análise de serviços autorizados'
                on_release: app.show_message('Serviços', 'Módulo em preparação.')
            BackButton:
                text: 'VOLTAR'
                on_release: app.show_screen('home')

    Screen:
        name: 'web'
        BoxLayout:
            orientation: 'vertical'
            padding: dp(15)
            spacing: dp(12)
            Label:
                text: '[b][color=ff2929]ANÁLISE WEB[/color][/b]'
                markup: True
                font_size: '23sp'
                size_hint_y: None
                height: dp(65)
            MainButton:
                text: 'Headers HTTP'
                on_release: app.show_message('HTTP', 'Módulo em preparação.')
            MainButton:
                text: 'Inspeção HTML'
                on_release: app.show_message('HTML', 'Módulo em preparação.')
            MainButton:
                text: 'Diagnóstico de segurança Web'
                on_release: app.show_message('Web', 'Módulo em preparação.')
            BackButton:
                text: 'VOLTAR'
                on_release: app.show_screen('home')

    Screen:
        name: 'reports'
        BoxLayout:
            orientation: 'vertical'
            padding: dp(15)
            spacing: dp(12)
            Label:
                text: '[b][color=ff2929]RELATÓRIOS[/color][/b]'
                markup: True
                font_size: '23sp'
            MainButton:
                text: 'Histórico de operações'
            MainButton:
                text: 'Relatórios salvos'
            BackButton:
                text: 'VOLTAR'
                on_release: app.show_screen('home')

    Screen:
        name: 'settings'
        BoxLayout:
            orientation: 'vertical'
            padding: dp(15)
            spacing: dp(12)
            Label:
                text: '[b][color=ff2929]CONFIGURAÇÕES[/color][/b]'
                markup: True
                font_size: '23sp'
            MainButton:
                text: 'Sobre o BackTrack 5'
                on_release: app.show_message('BackTrack 5', 'Mobile Ultimate Suite')
            BackButton:
                text: 'VOLTAR'
                on_release: app.show_screen('home')
"""

class BackTrackApp(App):

    def build(self):
        self.title = "BackTrack5"
        manager = Builder.load_string(KV)
        manager.add_widget(BackTrackTerminal())
        return manager

    def show_screen(self, screen):
        self.root.current = screen

    def show_message(self, title, message):
        Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.85, 0.35)
        ).open()

if __name__ == "__main__":
    BackTrackApp().run()
