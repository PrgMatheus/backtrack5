import os
import sys
import ast
import math
import platform
from datetime import datetime

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.metrics import dp


class BackTrackTerminal(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.name = "terminal"
        self.history = []

        root = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(8)
        )

        root.canvas.before.clear()

        header = Label(
            text="[b][color=ff2929]BACKTRACK 5 TERMINAL[/color][/b]\n"
                 "[color=aaaaaa]MOBILE SHELL v1.0[/color]",
            markup=True,
            size_hint_y=None,
            height=dp(65)
        )

        self.output = TextInput(
            text=(
                "BACKTRACK 5 MOBILE\n"
                "Terminal inicializado.\n"
                "Digite help para consultar os comandos.\n\n"
                "root@backtrack5:~# "
            ),
            readonly=True,
            multiline=True,
            background_color=(0.02, 0.02, 0.02, 1),
            foreground_color=(0.2, 1, 0.4, 1),
            font_size="13sp"
        )

        self.command = TextInput(
            hint_text="root@backtrack5:~# digite um comando",
            multiline=False,
            size_hint_y=None,
            height=dp(48),
            font_size="14sp"
        )

        self.command.bind(on_text_validate=self.execute)

        run_button = Button(
            text="EXECUTAR",
            size_hint_y=None,
            height=dp(48),
            background_normal="",
            background_color=(0.65, 0.04, 0.04, 1)
        )
        run_button.bind(on_release=self.execute)

        back_button = Button(
            text="VOLTAR AO PAINEL",
            size_hint_y=None,
            height=dp(45),
            background_normal="",
            background_color=(0.17, 0.17, 0.17, 1)
        )
        back_button.bind(
            on_release=lambda *_: self.manager.__setattr__(
                "current", "home"
            )
        )

        root.add_widget(header)
        root.add_widget(self.output)
        root.add_widget(self.command)
        root.add_widget(run_button)
        root.add_widget(back_button)

        self.add_widget(root)

    def write(self, message):
        self.output.text += str(message) + "\n"
        self.output.cursor = (0, len(self.output.text.splitlines()))

    def safe_math(self, expression):
        tree = ast.parse(expression, mode="eval")

        allowed = (
            ast.Expression, ast.BinOp, ast.UnaryOp,
            ast.Constant, ast.Add, ast.Sub, ast.Mult,
            ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
            ast.USub, ast.UAdd, ast.Call, ast.Name
        )

        for node in ast.walk(tree):
            if not isinstance(node, allowed):
                raise ValueError("Operação não permitida")

            if isinstance(node, ast.Name):
                if node.id not in ("sqrt", "sin", "cos", "pi"):
                    raise ValueError("Nome não permitido")

            if isinstance(node, ast.Call):
                if not isinstance(node.func, ast.Name):
                    raise ValueError("Chamada não permitida")
                if node.func.id not in ("sqrt", "sin", "cos"):
                    raise ValueError("Função não permitida")

        return eval(
            compile(tree, "<backtrack5>", "eval"),
            {"__builtins__": {}},
            {
                "sqrt": math.sqrt,
                "sin": math.sin,
                "cos": math.cos,
                "pi": math.pi
            }
        )

    def execute(self, *_):
        command = self.command.text.strip()
        self.command.text = ""

        if not command:
            return

        self.history.append(command)
        self.write("root@backtrack5:~# " + command)

        parts = command.split()
        cmd = parts[0].lower()

        try:
            if cmd == "help":
                self.write("""
COMANDOS BACKTRACK 5

help                 Ajuda
clear                Limpar terminal
about                Sobre o sistema
whoami               Usuário visual
pwd                  Diretório do aplicativo
date                 Data e hora
uname                Informações do sistema
python --version     Versão Python
py EXPRESSAO         Calculadora Python segura
history              Histórico de comandos
ls                   Arquivos do aplicativo

PACOTES LINUX

apt update
apt upgrade
apt install pacote

Os comandos apt precisam de um ambiente
Linux compatível conectado ao aplicativo.
""")

            elif cmd == "clear":
                self.output.text = ""

            elif cmd == "about":
                self.write("BACKTRACK 5 MOBILE TERMINAL v1.0")

            elif cmd == "whoami":
                self.write("root (identidade visual do terminal)")

            elif cmd == "pwd":
                self.write(os.getcwd())

            elif cmd == "date":
                self.write(datetime.now().astimezone().isoformat())

            elif cmd == "uname":
                self.write(platform.platform())

            elif cmd in ("python", "python3") and (
                len(parts) > 1 and parts[1] == "--version"
            ):
                self.write(sys.version)

            elif cmd == "py":
                expression = command[3:].strip()
                self.write(str(self.safe_math(expression)))

            elif cmd == "history":
                for i, item in enumerate(self.history, 1):
                    self.write(f"{i}  {item}")

            elif cmd == "ls":
                self.write("\n".join(os.listdir(".")) or "(vazio)")

            elif cmd in ("apt", "apt-get", "sudo", "pkg"):
                self.write(
                    "AMBIENTE LINUX NAO CONECTADO.\n"
                    "Este APK ainda nao possui um gerenciador "
                    "de pacotes Linux."
                )

            else:
                self.write(
                    "Comando indisponível nesta versão.\n"
                    "Digite help para ver os comandos suportados."
                )

        except Exception as error:
            self.write("ERRO: " + str(error))
