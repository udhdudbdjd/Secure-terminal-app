import os
import random
import threading
import subprocess
from datetime import datetime

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.properties import BooleanProperty, StringProperty

# ========== CONFIGURATION ==========
APP_PASSWORD = "Ideji2007@"
LOG_FILE = "terminal_log.txt"
SECRET_CODE = "Ideji2007"
KEYS_FILE = "allowed_keys.txt"
CREATOR_KEY = "IDEJI-ADMIN"

# Global state tracking
active_key = ""
connection_lost = False
waiting_secret = False

# Ensure log session creation right away
with open(LOG_FILE, "a", encoding="utf-8") as f:
    f.write(f"\n\n=== NEW SESSION {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")


def save_log(text):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")


def load_keys():
    if not os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, "w") as f:
            f.write("GUEST-001\n")
    with open(KEYS_FILE, "r") as f:
        keys = [k.strip().upper() for k in f.readlines() if k.strip()]
    if CREATOR_KEY not in keys:
        keys.append(CREATOR_KEY)
        save_keys(keys)
    return keys


def save_keys(key_list):
    with open(KEYS_FILE, "w") as f:
        for k in key_list:
            f.write(k + "\n")


# ========== KIVY INTERFACE LAYOUT (KV) ==========
Builder.load_string('''
<KeyScreen>:
    name: 'key_screen'
    canvas.before:
        Color:
            rgb: 0, 0, 0
        Rectangle:
            size: self.size
            pos: self.pos

    BoxLayout:
        orientation: 'vertical'
        padding: [20, 40, 20, 40]
        spacing: 15

        Label:
            text: "LICENSE KEY REQUIRED"
            font_name: "Courier"
            font_size: '20sp'
            bold: True
            color: 0, 1, 0, 1
            size_hint_y: None
            height: self.texture_size[1]

        Label:
            text: "Enter your key to proceed"
            font_name: "Courier"
            font_size: '14sp'
            color: 0, 0.66, 0, 1
            size_hint_y: None
            height: self.texture_size[1]

        TextInput:
            id: key_input
            multiline: False
            font_name: "Courier"
            font_size: '16sp'
            background_color: 0, 0, 0, 1
            foreground_color: 0, 1, 0, 1
            cursor_color: 0, 1, 0, 1
            size_hint_y: None
            height: '45sp'
            padding: [10, 12, 10, 10]
            on_text_validate: root.verify_key()

        Label:
            id: key_msg
            text: ""
            font_name: "Courier"
            font_size: '14sp'
            color: 1, 0, 0, 1
            size_hint_y: None
            height: '30sp'

        Widget: # Spacer

<PasswordScreen>:
    name: 'password_screen'
    canvas.before:
        Color:
            rgb: 0, 0, 0
        Rectangle:
            size: self.size
            pos: self.pos

    BoxLayout:
        orientation: 'vertical'
        padding: [20, 40, 20, 40]
        spacing: 15

        Label:
            text: "ENTER PASSWORD:"
            font_name: "Courier"
            font_size: '20sp'
            color: 0, 1, 0, 1
            size_hint_y: None
            height: self.texture_size[1]

        TextInput:
            id: pass_input
            password: True
            multiline: False
            font_name: "Courier"
            font_size: '16sp'
            background_color: 0, 0, 0, 1
            foreground_color: 0, 1, 0, 1
            cursor_color: 0, 1, 0, 1
            size_hint_y: None
            height: '45sp'
            padding: [10, 12, 10, 10]
            on_text_validate: root.check_pass()

        Label:
            id: status_msg
            text: ""
            font_name: "Courier"
            font_size: '14sp'
            color: 0, 1, 0, 1
            size_hint_y: None
            height: '40sp'

        Widget:

<TerminalScreen>:
    name: 'terminal_screen'
    canvas.before:
        Color:
            rgb: 0, 0, 0
        Rectangle:
            size: self.size
            pos: self.pos

    BoxLayout:
        orientation: 'vertical'
        padding: [15, 15, 15, 15]
        spacing: 8

        Label:
            text: "TYPE HERE:"
            font_name: "Courier"
            font_size: '14sp'
            color: 0, 1, 0, 1
            size_hint_y: None
            height: self.texture_size[1]
            alignment: ('left', 'center')
            text_size: self.size

        TextInput:
            id: input_box
            multiline: True
            font_name: "Courier"
            font_size: '16sp'
            background_color: 0, 0, 0, 1
            foreground_color: 0, 1, 0, 1
            cursor_color: 0, 1, 0, 1
            size_hint_y: 0.25
            on_text: root.live_update(self.text)

        Button:
            text: "RUN"
            font_name: "Courier"
            font_size: '16sp'
            bold: True
            background_normal: ''
            background_color: 0, 0.66, 0, 1
            color: 0, 0, 0, 1
            size_hint_y: None
            height: '45sp'
            on_release: root.run_command()

        Label:
            text: "OUTPUT:"
            font_name: "Courier"
            font_size: '14sp'
            color: 0, 1, 0, 1
            size_hint_y: None
            height: self.texture_size[1]
            text_size: self.size

        TextInput:
            id: output_box
            readonly: True
            multiline: True
            font_name: "Courier"
            font_size: '14sp'
            background_color: 0, 0, 0, 1
            foreground_color: 0, 1, 0, 1
            size_hint_y: 0.5
''')


# ========== SCREEN CONTROLLERS ==========
class KeyScreen(Screen):
    def verify_key(self):
        global active_key
        key = self.ids.key_input.text.strip().upper()
        active_key = key

        keys = load_keys()
        if key in keys:
            self.ids.key_msg.color = [0, 1, 0, 1]
            self.ids.key_msg.text = "KEY ACCEPTED"
            save_log(f"[{datetime.now().strftime('%H:%M:%S')}] KEY ACCEPTED: {key}")
            Clock.schedule_once(lambda dt: self.change_screen(), 0.8)
        else:
            self.ids.key_msg.color = [1, 0, 0, 1]
            self.ids.key_msg.text = "INVALID OR BANNED KEY"
            save_log(f"[{datetime.now().strftime('%H:%M:%S')}] KEY REJECTED: {key}")
            self.ids.key_input.text = ""

    def change_screen(self):
        self.manager.current = 'password_screen'


class PasswordScreen(Screen):
    def check_pass(self):
        typed = self.ids.pass_input.text
        save_log(f"[{datetime.now().strftime('%H:%M:%S')}] PASSWORD TRY - {active_key}")
        
        if typed == APP_PASSWORD:
            self.ids.status_msg.color = [0, 1, 0, 1]
            self.scan_anim(0)
        else:
            self.ids.status_msg.color = [1, 0, 0, 1]
            self.ids.status_msg.text = "ACCESS DENIED [XXXXXXXX] 100%"
            save_log(f"[{datetime.now().strftime('%H:%M:%S')}] ACCESS DENIED - {active_key}")
            self.ids.pass_input.text = ""
            Clock.schedule_once(lambda dt: setattr(self.ids.status_msg, 'text', ''), 1.5)

    def scan_anim(self, step):
        steps = ["SCANNING [░░░░░░] 0%", "SCANNING [██░░░░] 25%",
                 "SCANNING [████░░] 50%", "SCANNING [██████░] 75%",
                 "SCANNING [████████] 100%"]
        if step < len(steps):
            self.ids.status_msg.text = steps[step]
            Clock.schedule_once(lambda dt: self.scan_anim(step + 1), 0.4)
        else:
            self.ids.status_msg.text = "ACCESS GRANTED"
            save_log(f"[{datetime.now().strftime('%H:%M:%S')}] ACCESS GRANTED - {active_key}")
            Clock.schedule_once(lambda dt: self.change_screen(), 0.6)

    def change_screen(self):
        self.manager.current = 'terminal_screen'


class TerminalScreen(Screen):
    hacking = BooleanProperty(False)

    def on_enter(self):
        self.ids.input_box.text = ""
        self.ids.output_box.text = "Output will appear here"
        Clock.schedule_interval(self.glitch_effect, 1.2)

    def timestamp(self):
        return datetime.now().strftime("[%H:%M:%S] > ")

    def show_disconnect(self):
        global connection_lost, waiting_secret
        connection_lost = True
        waiting_secret = False

        self.ids.output_box.foreground_color = [1, 0, 0, 1]
        self.ids.output_box.text = (
            "!!! CONNECTION LOST!!!\n\n"
            "Signal interrupted\n"
            "All systems offline\n"
            "[ERROR CODE: 0x404]\n\n"
            ">> Enter secret code to restore connection\n"
            "Type 'reconnect' then tap RUN"
        )
        save_log(f"[{datetime.now().strftime('%H:%M:%S')}] CONNECTION LOST - {active_key}")

    def restore_connection(self):
        global connection_lost, waiting_secret
        connection_lost = False
        waiting_secret = False
        self.ids.output_box.foreground_color = [0, 1, 0, 1]
        self.ids.output_box.text = self.timestamp() + "CONNECTION RESTORED\nSignal stable\nAll systems online"
        save_log(f"[{datetime.now().strftime('%H:%M:%S')}] CONNECTION RESTORED - {active_key}")

    def view_logs(self):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = f.read()
            if not logs.strip():
                return "\nLOG FILE EMPTY"
            return "\n--- TERMINAL LOGS ---\n" + logs[-2000:]
        except:
            return "\nERROR: Cannot read log file"

    def execute_cmd(self, cmd):
        global waiting_secret, connection_lost
        if connection_lost:
            if cmd.lower() == "reconnect":
                waiting_secret = True
                return "SECRET_PROMPT"
            elif waiting_secret and cmd == SECRET_CODE:
                self.restore_connection()
                return None
            else:
                return None

        cmd_lower = cmd.lower().strip()
        parts = cmd.split(" ", 1)

        # ADMIN COMMANDS
        if cmd_lower.startswith("addkey "):
            if active_key == CREATOR_KEY:
                new_key = parts[1].strip().upper()
                keys = load_keys()
                if new_key not in keys:
                    keys.append(new_key)
                    save_keys(keys)
                    return f"\nKEY ADDED: {new_key}"
                else:
                    return "\nKEY ALREADY EXISTS"
            else:
                return "\nACCESS DENIED: Creator only"

        elif cmd_lower == "listkey":
            if active_key == CREATOR_KEY:
                keys = load_keys()
                return "\nLICENSE KEYS:\n" + "\n".join([f" {k}" for k in keys])
            else:
                return "\nACCESS DENIED: Creator only"

        elif cmd_lower == "resetkey":
            if active_key == CREATOR_KEY:
                save_keys([CREATOR_KEY])
                return "\nALL KEYS DELETED\nOnly CREATOR key remains"
            else:
                return "\nACCESS DENIED: Creator only"

        elif cmd_lower.startswith("removekey "):
            if active_key == CREATOR_KEY:
                target_key = parts[1].strip().upper()
                if target_key == CREATOR_KEY:
                    return "\nCANNOT REMOVE CREATOR KEY"
                keys = load_keys()
                if target_key in keys:
                    keys.remove(target_key)
                    save_keys(keys)
                    return f"\nKEY REMOVED: {target_key}\nThat user is banned now"
                else:
                    return "\nKEY NOT FOUND"
            else:
                return "\nACCESS DENIED: Creator only"

        elif cmd_lower == "logs":
            return self.view_logs()

        # NORMAL SYSTEM COMMANDS
        if cmd_lower in ["scan.exe", "ls"]:
            try:
                result = subprocess.check_output(["ls", "-la"], text=True, stderr=subprocess.STDOUT)
                return "\n" + result
            except:
                return "\nError reading files"
        elif cmd_lower == "pwd":
            return "\nCurrent dir: " + os.getcwd()
        elif cmd_lower == "date":
            return "\n" + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif cmd_lower == "clear":
            return ""
        elif cmd_lower == "log":
            return f"\nLog saved at: {os.getcwd()}/{LOG_FILE}"
        elif cmd_lower == "disconnect":
            self.show_disconnect()
            return None
        elif cmd_lower == "hack.exe":
            return "HACK_START"
        else:
            return None

    def hack_animation_thread(self):
        self.hacking = True
        progress = 0
        save_log(f"[{datetime.now().strftime('%H:%M:%S')}] hack.exe started - {active_key}")
        
        while progress <= 100 and self.hacking:
            bar = "█" * (progress // 5) + "░" * (20 - progress // 5)
            text = f"{self.timestamp()}hack.exe\nHACKING STARTED...\n[{bar}] {progress}%"
            if progress == 100:
                text += "\n\nACCESS GRANTED\nFirewall bypassed"
                self.hacking = False
                save_log(f"[{datetime.now().strftime('%H:%M:%S')}] hack.exe finished - {active_key}")

            # Push the text change back to Kivy main thread safely
            Clock.schedule_once(lambda dt, t=text: self.update_output_safe(t), 0)
            progress += 5
            import time
            time.sleep(0.2)

    def update_output_safe(self, text):
        self.ids.output_box.text = text

    def live_update(self, text):
        if self.hacking or connection_lost:
            return
        if text.strip() == "":
            self.ids.output_box.text = "Output will appear here"
        else:
            self.ids.output_box.text = self.timestamp() + text

    def run_command(self):
        global connection_lost, waiting_secret
        text = self.ids.input_box.text.strip()
        self.ids.input_box.text = ""

        if text == "":
            return

        cmd_result = self.execute_cmd(text)
        if cmd_result == "HACK_START":
            threading.Thread(target=self.hack_animation_thread, daemon=True).start()
            return
        elif cmd_result == "SECRET_PROMPT":
            return
        elif cmd_result is None:
            display_text = self.timestamp() + text
        else:
            display_text = self.timestamp() + text + cmd_result

        save_log(f"[{datetime.now().strftime('%H:%M:%S')}] > {text} - {active_key}")

        if not self.hacking and not connection_lost:
            self.ids.output_box.text = display_text

    def glitch_effect(self, dt):
        if not self.hacking and not connection_lost:
            colors = [[0, 1, 0, 1], [0, 0.8, 0, 1], [0, 0.6, 0, 1]]
            self.ids.output_box.foreground_color = random.choice(colors)
            Clock.schedule_once(lambda d: setattr(self.ids.output_box, 'foreground_color', [0, 1, 0, 1]), 0.2)


class SecureTerminalApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(KeyScreen())
        sm.add_widget(PasswordScreen())
        sm.add_widget(TerminalScreen())
        return sm


if __name__ == '__main__':
    SecureTerminalApp().run()
