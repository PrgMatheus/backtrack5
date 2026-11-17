from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button


class BackTrackTerminal(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.name = "terminal"
        self.history = []
        self.next_execution_id = 1000

        root = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(8)
        )

        header = Label(
            text="[b][color=ff2929]BASHBT5[/color][/b]\n"
                 "[color=aaaaaa]BACKTRACK 5 LINUX SHELL[/color]",
            markup=True,
            size_hint_y=None,
            height=dp(65)
        )

        self.output = TextInput(
            text=(
                "BASHBT5 MOBILE\n"
                "Interface inicializada.\n"
                "Ambiente: Termux ARM64\n"
                "Digite help para consultar os comandos.\n\n"
            ),
            readonly=True,
            multiline=True,
            background_color=(0.02, 0.02, 0.02, 1),
            foreground_color=(0.2, 1, 0.4, 1),
            font_size="13sp"
        )

        self.command = TextInput(
            hint_text="bashbt5 $ digite um comando",
            multiline=False,
            size_hint_y=None,
            height=dp(48),
            font_size="14sp"
        )
        self.command.bind(on_text_validate=self.execute)

        run_button = Button(
            text="EXECUTAR NO TERMUX",
            size_hint_y=None,
            height=dp(48),
            background_normal="",
            background_color=(0.65, 0.04, 0.04, 1)
        )
        run_button.bind(on_release=self.execute)

        shell_button = Button(
            text="ABRIR BASH INTERATIVO NO TERMUX",
            size_hint_y=None,
            height=dp(48),
            background_normal="",
            background_color=(0.12, 0.35, 0.18, 1)
        )
        shell_button.bind(
            on_release=lambda *_:
                self.run_in_termux("exec bash -i", background=False)
        )

        back_button = Button(
            text="VOLTAR AO PAINEL",
            size_hint_y=None,
            height=dp(45),
            background_normal="",
            background_color=(0.17, 0.17, 0.17, 1)
        )
        back_button.bind(
            on_release=lambda *_:
                setattr(self.manager, "current", "home")
        )

        root.add_widget(header)
        root.add_widget(self.output)
        root.add_widget(self.command)
        root.add_widget(run_button)
        root.add_widget(shell_button)
        root.add_widget(back_button)

        self.add_widget(root)

        self.result_poll = Clock.schedule_interval(
            self.check_termux_results, 0.4
        )

    def write(self, message):
        self.output.text += str(message) + "\n"
        self.output.cursor = (0, len(self.output.text.splitlines()))

    def run_in_termux(self, command, background=True):
        try:
            from jnius import autoclass, cast

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )
            Intent = autoclass("android.content.Intent")
            PendingIntent = autoclass("android.app.PendingIntent")
            Build = autoclass("android.os.Build")
            JavaString = autoclass("java.lang.String")

            activity = PythonActivity.mActivity

            intent = Intent()
            intent.setClassName(
                "com.termux",
                "com.termux.app.RunCommandService"
            )
            intent.setAction("com.termux.RUN_COMMAND")

            arguments = cast(
                "java.lang.String[]",
                [
                    JavaString("-lc"),
                    JavaString(command)
                ]
            )

            intent.putExtra(
                "com.termux.RUN_COMMAND_PATH",
                "/data/data/com.termux/files/usr/bin/bash"
            )
            intent.putExtra(
                "com.termux.RUN_COMMAND_ARGUMENTS",
                arguments
            )
            intent.putExtra(
                "com.termux.RUN_COMMAND_WORKDIR",
                "/data/data/com.termux/files/home"
            )
            intent.putExtra(
                "com.termux.RUN_COMMAND_BACKGROUND",
                background
            )

            if background:
                execution_id = self.next_execution_id
                self.next_execution_id += 1

                callback = Intent()
                callback.setClassName(
                    activity.getPackageName(),
                    "org.backtrack5.bactrack5.BashBT5ResultService"
                )
                callback.putExtra("execution_id", execution_id)

                flags = PendingIntent.FLAG_ONE_SHOT

                if Build.VERSION.SDK_INT >= 31:
                    flags |= PendingIntent.FLAG_MUTABLE

                pending = PendingIntent.getService(
                    activity,
                    execution_id,
                    callback,
                    flags
                )

                intent.putExtra(
                    "com.termux.RUN_COMMAND_PENDING_INTENT",
                    pending
                )

                self.write(
                    "[BASHBT5] Comando enviado. ID: "
                    + str(execution_id)
                )

            else:
                intent.putExtra(
                    "com.termux.RUN_COMMAND_SESSION_ACTION",
                    "0"
                )
                self.write(
                    "[BASHBT5] Abrindo sessão interativa no Termux."
                )

            activity.startService(intent)

        except Exception as error:
            self.write(
                "[ERRO DE INTEGRACAO] " + str(error)
            )

    def check_termux_results(self, dt):
        try:
            from jnius import autoclass

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            activity = PythonActivity.mActivity
            preferences = activity.getSharedPreferences(
                "bashbt5_termux", 0
            )

            if not preferences.getBoolean("result_ready", False):
                return

            stdout = preferences.getString("stdout", "")
            stderr = preferences.getString("stderr", "")
            errmsg = preferences.getString("errmsg", "")
            exit_code = preferences.getInt("exitCode", -1)
            error_code = preferences.getInt("err", 0)
            execution_id = preferences.getInt("execution_id", -1)

            preferences.edit().putBoolean(
                "result_ready", False
            ).apply()

            self.write("[RESULTADO ID: " + str(execution_id) + "]")

            if stdout:
                self.write(stdout)

            if stderr:
                self.write("[STDERR]")
                self.write(stderr)

            if errmsg:
                self.write("[ERRO TERMUX]")
                self.write(errmsg)

            self.write("Código de saída: " + str(exit_code))
            self.write("Código interno: " + str(error_code))
            self.write("--------------------------------")

        except Exception as error:
            self.write("[ERRO AO LER RESULTADO] " + str(error))

    def execute(self, *_):
        command = self.command.text.strip()
        self.command.text = ""

        if not command:
            return

        self.history.append(command)
        self.write("bashbt5 $ " + command)

        cmd = command.lower()

        parts = command.split(None, 2)
        if (
            len(parts) >= 2
            and parts[0].lower() == "sudo"
            and parts[1].lower() == "apt"
        ):
            self.write(
                "[AVISO] sudo apt será executado como apt no Termux. "
                "Isso não concede acesso root."
            )
            command = "apt" + (f" {parts[2]}" if len(parts) == 3 else "")
            cmd = command.lower()

        if cmd == "help":
            self.write(
                "BASHBT5 - COMANDOS LOCAIS\n"
                "help       Ajuda\n"
                "clear      Limpar tela\n"
                "about      Sobre o BashBT5\n"
                "history    Histórico local\n\n"
                "COMANDOS TERMUX\n"
                "pwd, date, uname -a, whoami, id\n"
                "ls, df -h, free -h\n"
                "python --version\n"
                "apt update / apt upgrade\n"
                "apt install NOME_DO_PACOTE\n"
                "pkg update / pkg upgrade\n"
                "pkg install NOME_DO_PACOTE\n"
                "sudo apt install NOME_DO_PACOTE\n"
                "pkg list-installed"
            )
            return

        if cmd == "clear":
            self.output.text = ""
            return

        if cmd == "about":
            self.write("BASHBT5 - TERMINAL DO BACKTRACK5")
            self.write("Interface Kivy + integração Termux")
            return

        if cmd == "history":
            for index, item in enumerate(self.history, 1):
                self.write(f"{index}  {item}")
            return

        self.run_in_termux(command, background=True)
