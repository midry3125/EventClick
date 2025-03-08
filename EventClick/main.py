import json
import glob
import os
import sys
from threading import Thread
from multiprocessing import Process

import pyautogui
from pynput import keyboard, mouse

class Setting:
    def __init__(self):
        self.target = ""
        self.pos  = tuple()

    def bind_on_press(self, key):
        if key == keyboard.Key.enter:
            return self.target == ""
        else:
            if hasattr(key, "name"):
                self.target = key.name
            else:
                self.target = key.char
            sys.stdout.write(f"\r\033[2K> {self.target}")

    def bind_on_click(self, x, y, button, pressed):
        self.target = button.name
        sys.stdout.write(f"\r\033[2K> {self.target}")
    
    def fin_click_on_press(self, key):
        return key != keyboard.Key.enter or len(self.pos) == 0

    def pos_on_click(self, x, y, button, pressed):
        if pressed and button == mouse.Button.right:
            self.pos = (x, y)
            sys.stdout.write(f"\r\033[2K> ({x}, {y})")

class Binding:
    def __init__(self, b):
        self.bindings = b
        self.released = False

    def on_press(self, key):
        if self.released:
            self.released = False
            if key == keyboard.Key.enter:
                return False
            else:
                if hasattr(key, "name"):
                    target = key.name
                else:
                    target = key.char        
                if target in self.bindings:
                    click(self.bindings[target])

    def on_release(self, key):
        self.released = True

    def on_click(self, x, y, button, pressed):
        target = button.name
        if pressed and target in self.bindings:
            click(self.bindings[target])

class Profile:
    def __init__(self):
        self.root = "profiles"
        if not os.path.isdir(self.root):
            os.mkdir(self.root)
        self.profiles = sorted(os.listdir(self.root))

    def new(self, name):
        path = self.join(name)
        if os.path.isdir(path):
            return False
        else:
            os.mkdir(path)
            return True

    def join(self, *names):
        return os.path.join(self.root, *names)

def click(pos):
    pos0 = pyautogui.position()
    pyautogui.click(*pos, button="left")
    pyautogui.moveTo(*pos0)

def ask_continue(text):
    print(text)
    while True:
        answer = input("[y/yes or n/no]> ").lower()
        if answer == "y" or answer == "yes":
            return True
        elif answer == "n" or answer == "no":
            return False

def show_help():
    print("""
使い方
$ ec [options] [profile name]

[options]
- new   指定されたプロファイルを作成します
- set   指定されたプロファイルのバインド設定をします
- bind  バインディングを開始します

[profile name]
setとbindについては省略可能です
        """)

def main():
    profile = Profile()
    if len(sys.argv) > 1:
        if len(sys.argv) > 2:
            target_profile = sys.argv[2]
        else:
            target_profile = ""
            bindings_path = profile.join("bindings.json")
        if sys.argv[1] == "new":
            if not target_profile:
                print("プロファイル名を第二引数に指定してください")
            elif not profile.new(target_profile):
                print(f"プロファイル名\"{target_profile}\"は既に存在しています")
            return
        if target_profile:
            if target_profile in profile.profiles:
                bindings_path = profile.join(target_profile, "bindings.json")
            else:
                print(f"プロファイル名\"{target_profile}\"は存在しません")
                return
        if os.path.isfile(bindings_path):
            with open(bindings_path, "r") as f:
                bindings = json.load(f)
        else:
            bindings = dict()
        if sys.argv[1] == "set":
            setting = Setting()
            print("1. 対応させるキー、またはマウスを押してください(Enterキーで次へ進みます)")
            sys.stdout.write("> ")
            with mouse.Listener(on_click=setting.bind_on_click) as mlistener:
                with keyboard.Listener(on_press=setting.bind_on_press, suppress=True) as klistener:
                    klistener.join()
            print()
            if setting.target in bindings:
                if not ask_continue(f"{setting.target}は既に割り当てられています\n上書きしますか？"):
                    return
            print("\n左クリックする位置を \"右クリック\" してください(Enterキーで設定完了)")
            sys.stdout.write("> ")
            with mouse.Listener(on_click=setting.pos_on_click) as mlistener:
                with keyboard.Listener(on_press=setting.fin_click_on_press, suppress=True) as klistener:
                    klistener.join()
            bindings[setting.target] = setting.pos
            with open(bindings_path, "w") as f:
                json.dump(bindings, f)
        elif sys.argv[1] == "bind":
            binding = Binding(bindings)
            print("バインド中...(Enterキーで終了)")
            with mouse.Listener(on_click=binding.on_click) as mlistener:
                with keyboard.Listener(on_press=binding.on_press, on_release=binding.on_release, suppress=True) as klistener:
                    klistener.join()
        else:
            show_help()
    else:
        show_help()

if __name__ == "__main__":
    main()