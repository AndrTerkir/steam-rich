import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import subprocess
import os
import json
import time
import requests
import re
import sys
from pathlib import Path
import psutil

class SteamToolsPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Steam Tools Pro [RAGE MODE]")
        self.root.geometry("950x650")
        
        style = ttk.Style()
        style.theme_use('clam')
        
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ---- Верхняя панель ----
        url_frame = ttk.LabelFrame(main_frame, text="Добавить игру", padding="10")
        url_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(url_frame, text="Ссылка на игру или AppID:").grid(row=0, column=0, sticky=tk.W)
        self.url_entry = ttk.Entry(url_frame, width=70)
        self.url_entry.grid(row=0, column=1, padx=5, sticky=tk.W+tk.E)
        
        btn_frame = ttk.Frame(url_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        self.add_btn = ttk.Button(btn_frame, text="➕ Добавить в библиотеку", command=self.thread_add_game)
        self.add_btn.pack(side=tk.LEFT, padx=2)
        
        self.farm_btn = ttk.Button(btn_frame, text="⏱ Фарм часов", command=self.thread_farm_hours)
        self.farm_btn.pack(side=tk.LEFT, padx=2)
        
        # Статус Steam
        status_frame = ttk.LabelFrame(main_frame, text="Статус Steam", padding="5")
        status_frame.pack(fill=tk.X, pady=5)
        
        self.steam_status = ttk.Label(status_frame, text="🔍 Проверка...")
        self.steam_status.pack(side=tk.LEFT)
        
        ttk.Button(status_frame, text="🔄 Обновить", command=self.check_steam).pack(side=tk.RIGHT)
        
        # Таблица игр
        games_frame = ttk.LabelFrame(main_frame, text="Активные игры", padding="10")
        games_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        columns = ('appid', 'name', 'status', 'time')
        self.games_tree = ttk.Treeview(games_frame, columns=columns, show='headings', height=10)
        self.games_tree.heading('appid', text='AppID')
        self.games_tree.heading('name', text='Название')
        self.games_tree.heading('status', text='Статус')
        self.games_tree.heading('time', text='Наиграно')
        
        self.games_tree.column('appid', width=80)
        self.games_tree.column('name', width=300)
        self.games_tree.column('status', width=120)
        self.games_tree.column('time', width=80)
        
        scrollbar = ttk.Scrollbar(games_frame, orient=tk.VERTICAL, command=self.games_tree.yview)
        self.games_tree.configure(yscrollcommand=scrollbar.set)
        
        self.games_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Контекстное меню
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Остановить фарм", command=self.stop_game)
        self.context_menu.add_command(label="Удалить из списка", command=self.remove_game)
        self.games_tree.bind("<Button-3>", self.show_context_menu)
        
        # Лог
        log_frame = ttk.LabelFrame(main_frame, text="Лог операций", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, height=8, state='normal')
        self.log_area.pack(fill=tk.BOTH, expand=True)
        
        # Конфиг
        self.config_dir = Path.home() / ".steam_tools_pro"
        self.config_dir.mkdir(exist_ok=True)
        self.games_file = self.config_dir / "games.json"
        
        self.active_games = self.load_games()
        self.running_processes = {}
        
        self.check_steam()
        self.update_games_list()
        self.log("Steam Tools Pro запущен")
        
    def log(self, msg, level="INFO"):
        timestamp = time.strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] [{level}] {msg}\n")
        self.log_area.see(tk.END)
        self.root.update()
        
    def check_steam(self):
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and 'steam' in proc.info['name'].lower():
                    self.steam_status.config(text="✅ Steam запущен", foreground="green")
                    return True
            self.steam_status.config(text="❌ Steam не запущен", foreground="red")
            return False
        except Exception as e:
            self.log(f"Ошибка проверки Steam: {e}", "ERROR")
            self.steam_status.config(text="❌ Ошибка проверки", foreground="orange")
            return False
            
    def extract_appid(self, text):
        text = text.strip()
        if text.isdigit():
            return text
        match = re.search(r'/app/(\d+)', text)
        if match:
            return match.group(1)
        match = re.search(r'[?&]appid=(\d+)', text)
        if match:
            return match.group(1)
        if '.' in text and '/' in text:
            numbers = re.findall(r'\b\d{2,6}\b', text)
            if numbers:
                return numbers[0]
        return None
        
    def get_game_name(self, appid):
        try:
            url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l=russian"
            r = requests.get(url, timeout=5)
            data = r.json()
            if data.get(str(appid), {}).get("success"):
                return data[str(appid)]["data"]["name"]
        except:
            pass
        return f"Game {appid}"
        
    def find_steam_folder(self):
        if sys.platform == "win32":
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
                steam_path = winreg.QueryValueEx(key, "SteamPath")[0]
                if steam_path and os.path.exists(steam_path):
                    return steam_path.replace('/', '\\')
            except:
                pass
            candidates = [
                "C:\\Program Files (x86)\\Steam",
                "C:\\Program Files\\Steam",
                os.path.expanduser("~\\AppData\\Local\\Steam"),
                "D:\\Steam",
                "E:\\Steam"
            ]
            for path in candidates:
                if os.path.exists(os.path.join(path, "steam.exe")):
                    return path
        elif sys.platform == "darwin":
            return os.path.expanduser("~/Library/Application Support/Steam")
        else:
            return os.path.expanduser("~/.steam/steam")
        return None
        
    def create_manifest_template(self, appid):
        """Создаёт шаблон манифеста, если нет установленных игр"""
        steam_path = self.find_steam_folder()
        if not steam_path:
            return False
            
        steamapps_path = os.path.join(steam_path, "steamapps")
        if not os.path.exists(steamapps_path):
            os.makedirs(steamapps_path, exist_ok=True)
        
        # Шаблон манифеста
        template_content = f'''"AppState"
{{
    "appid"		"{appid}"
    "Universe"		"1"
    "name"		"{self.get_game_name(appid)}"
    "installdir"		"dummy_{appid}"
    "StateFlags"		"4"
    "SizeOnDisk"		"0"
    "StagingSize"		"0"
    "buildid"		"0"
    "LastUpdated"		"0"
    "UpdateResult"		"0"
    "BytesToDownload"		"0"
    "BytesDownloaded"		"0"
    "BytesToStage"		"0"
    "BytesStaged"		"0"
    "UserConfig"
    {{
    }}
}}'''
        
        manifest_path = os.path.join(steamapps_path, f"appmanifest_{appid}.acf")
        try:
            with open(manifest_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            self.log(f"✓ Создан шаблон манифеста для AppID {appid}")
            return True
        except Exception as e:
            self.log(f"Ошибка создания шаблона: {e}", "ERROR")
            return False
            
    def add_game_via_manifest(self, appid):
        steam_path = self.find_steam_folder()
        if not steam_path:
            self.log("Не удалось найти папку Steam", "ERROR")
            return False
            
        steamapps_path = os.path.join(steam_path, "steamapps")
        if not os.path.exists(steamapps_path):
            self.log("Папка steamapps не найдена", "ERROR")
            return False
            
        manifests = list(Path(steamapps_path).glob("appmanifest_*.acf"))
        
        # Если нет манифестов - используем шаблон
        if not manifests:
            return self.create_manifest_template(appid)
            
        template_path = str(manifests[0])
        new_manifest_path = os.path.join(steamapps_path, f"appmanifest_{appid}.acf")
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            old_appid_match = re.search(r'"appid"\s+"(\d+)"', content)
            if old_appid_match:
                old_appid = old_appid_match.group(1)
                content = content.replace(f'"{old_appid}"', f'"{appid}"')
                
            game_name = self.get_game_name(appid)
            content = re.sub(r'"name"\s+"[^"]+"', f'"name" "{game_name}"', content)
            content = re.sub(r'"installdir"\s+"[^"]+"', f'"installdir" "dummy_{appid}"', content)
            content = re.sub(r'"SizeOnDisk"\s+"\d+"', '"SizeOnDisk" "0"', content)
            
            with open(new_manifest_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            self.log(f"✓ Манифест для {game_name} (AppID: {appid}) создан")
            return True
        except Exception as e:
            self.log(f"Ошибка создания манифеста: {e}", "ERROR")
            return False
            
    def restart_steam(self):
        try:
            if sys.platform == "win32":
                os.system("taskkill /f /im steam.exe")
            else:
                os.system("pkill steam")
            time.sleep(3)
            self.start_steam()
            self.log("Steam перезапущен")
        except Exception as e:
            self.log(f"Ошибка перезапуска Steam: {e}")
            
    def start_steam(self):
        try:
            steam_path = self.find_steam_folder()
            if not steam_path:
                self.log("Steam не найден, запустите вручную", "ERROR")
                return
                
            if sys.platform == "win32":
                exe = os.path.join(steam_path, "steam.exe")
                if os.path.exists(exe):
                    subprocess.Popen([exe])
                    self.log("Steam запущен")
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-a", "Steam"])
            else:
                subprocess.Popen(["steam"])
        except Exception as e:
            self.log(f"Не удалось запустить Steam: {e}", "ERROR")
            
    def thread_add_game(self):
        threading.Thread(target=self.add_game, daemon=True).start()
        
    def add_game(self):
        input_text = self.url_entry.get()
        appid = self.extract_appid(input_text)
        
        if not appid:
            self.log("Не удалось распознать AppID", "ERROR")
            return
            
        if not self.check_steam():
            if not messagebox.askyesno("Steam не запущен", "Запустить Steam сейчас?"):
                return
            self.start_steam()
            time.sleep(5)
        
        if self.add_game_via_manifest(appid):
            name = self.get_game_name(appid)
            
            if not any(g['appid'] == appid for g in self.active_games):
                self.active_games.append({
                    'appid': appid,
                    'name': name,
                    'status': 'в библиотеке',
                    'time': '-'
                })
                self.save_games()
                self.update_games_list()
            
            self.log(f"✓ Игра {name} добавлена в библиотеку Steam")
            
            if messagebox.askyesno("Перезапуск", "Перезапустить Steam для применения?"):
                self.restart_steam()
                
    def thread_farm_hours(self):
        selected = self.games_tree.selection()
        if not selected:
            messagebox.showwarning("Выбор игры", "Выберите игру в списке")
            return
        item = self.games_tree.item(selected[0])
        appid = item['values'][0]
        threading.Thread(target=self.farm_hours, args=(appid,), daemon=True).start()
        
    def farm_hours(self, appid):
        game = next((g for g in self.active_games if g['appid'] == appid), None)
        if not game:
            return
            
        game['status'] = 'фарм часов'
        self.update_games_list()
        self.log(f"Запуск фарма часов для {game['name']}")
        
        try:
            # Используем Spacewar (AppID 480) для фарма - это тестовая игра Steam
            # которая есть у всех
            subprocess.Popen(f"steam://rungameid/480", shell=True)
            
            # Создаём фейковый процесс для отслеживания времени
            if sys.platform == "win32":
                proc = subprocess.Popen(
                    ["cmd.exe", "/c", "timeout", "/t", "99999"],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                self.running_processes[appid] = proc
            
            start_time = time.time()
            while appid in self.running_processes:
                time.sleep(60)
                hours = round((time.time() - start_time) / 3600, 1)
                game['time'] = f"{hours}h"
                self.update_games_list()
                
        except Exception as e:
            self.log(f"Ошибка фарма: {e}", "ERROR")
            game['status'] = 'ошибка'
            self.update_games_list()
            
    def stop_game(self):
        selected = self.games_tree.selection()
        if not selected:
            return
        item = self.games_tree.item(selected[0])
        appid = item['values'][0]
        
        if appid in self.running_processes:
            try:
                self.running_processes[appid].terminate()
                del self.running_processes[appid]
            except:
                pass
                
        for g in self.active_games:
            if g['appid'] == appid:
                g['status'] = 'остановлен'
                break
        self.update_games_list()
        self.log(f"Фарм для AppID {appid} остановлен")
        
    def remove_game(self):
        selected = self.games_tree.selection()
        if not selected:
            return
        item = self.games_tree.item(selected[0])
        appid = item['values'][0]
        
        if appid in self.running_processes:
            self.stop_game()
            
        self.active_games = [g for g in self.active_games if g['appid'] != appid]
        self.save_games()
        self.update_games_list()
        self.log(f"Игра {appid} удалена из списка")
        
    def show_context_menu(self, event):
        item = self.games_tree.identify_row(event.y)
        if item:
            self.games_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
            
    def update_games_list(self):
        for row in self.games_tree.get_children():
            self.games_tree.delete(row)
        for g in self.active_games:
            self.games_tree.insert('', tk.END, values=(
                g['appid'], g['name'], g['status'], g['time']
            ))
            
    def save_games(self):
        with open(self.games_file, 'w', encoding='utf-8') as f:
            json.dump(self.active_games, f, ensure_ascii=False, indent=2)
            
    def load_games(self):
        if self.games_file.exists():
            try:
                with open(self.games_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return []

if __name__ == "__main__":
    try:
        import psutil
    except ImportError:
        print("Установите psutil: pip install psutil")
        sys.exit(1)
        
    root = tk.Tk()
    app = SteamToolsPro(root)
    root.mainloop()
