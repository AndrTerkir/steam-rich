import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import subprocess
import os
import json
import time
import requests
import re
import sys
import shutil
from pathlib import Path
import psutil
import winreg
import ctypes

class SteamToolsUltimate:
    def __init__(self, root):
        self.root = root
        self.root.title("SteamTools Ultimate [FINAL]")
        self.root.geometry("1200x750")
        
        style = ttk.Style()
        style.theme_use('clam')
        
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Верхняя панель
        top_frame = ttk.LabelFrame(main_frame, text="Управление", padding="10")
        top_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(top_frame, text="AppID:").grid(row=0, column=0, sticky=tk.W)
        self.appid_entry = ttk.Entry(top_frame, width=15)
        self.appid_entry.grid(row=0, column=1, padx=5, sticky=tk.W)
        
        ttk.Label(top_frame, text="Depot ID:").grid(row=0, column=2, sticky=tk.W, padx=(20,0))
        self.depot_entry = ttk.Entry(top_frame, width=15)
        self.depot_entry.grid(row=0, column=3, padx=5, sticky=tk.W)
        
        ttk.Label(top_frame, text="Manifest ID:").grid(row=0, column=4, sticky=tk.W, padx=(20,0))
        self.manifest_entry = ttk.Entry(top_frame, width=30)
        self.manifest_entry.grid(row=0, column=5, padx=5, sticky=tk.W)
        
        btn_frame = ttk.Frame(top_frame)
        btn_frame.grid(row=1, column=0, columnspan=6, pady=10)
        
        self.add_btn = ttk.Button(btn_frame, text="➕ Добавить в библиотеку", command=self.thread_add_game)
        self.add_btn.pack(side=tk.LEFT, padx=2)
        
        self.download_btn = ttk.Button(btn_frame, text="⬇ Скачать игру (DepotDownloader)", command=self.thread_download_game)
        self.download_btn.pack(side=tk.LEFT, padx=2)
        
        self.farm_btn = ttk.Button(btn_frame, text="⏱ Фарм часов", command=self.thread_farm_hours)
        self.farm_btn.pack(side=tk.LEFT, padx=2)
        
        self.greenluma_btn = ttk.Button(btn_frame, text="🟢 Запустить с GreenLuma", command=self.thread_greenluma)
        self.greenluma_btn.pack(side=tk.LEFT, padx=2)
        
        # Статусная строка
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.steam_status = ttk.Label(status_frame, text="🔍 Steam: проверка...")
        self.steam_status.pack(side=tk.LEFT, padx=5)
        
        self.add_status = ttk.Label(status_frame, text="")
        self.add_status.pack(side=tk.LEFT, padx=5)
        
        # Основное содержимое: вкладки
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Вкладка "Библиотека"
        lib_tab = ttk.Frame(notebook)
        notebook.add(lib_tab, text="Библиотека")
        
        columns = ('appid', 'name', 'status', 'size', 'path')
        self.games_tree = ttk.Treeview(lib_tab, columns=columns, show='headings', height=12)
        self.games_tree.heading('appid', text='AppID')
        self.games_tree.heading('name', text='Название')
        self.games_tree.heading('status', text='Статус')
        self.games_tree.heading('size', text='Размер')
        self.games_tree.heading('path', text='Путь')
        
        self.games_tree.column('appid', width=80)
        self.games_tree.column('name', width=250)
        self.games_tree.column('status', width=120)
        self.games_tree.column('size', width=100)
        self.games_tree.column('path', width=300)
        
        scrollbar = ttk.Scrollbar(lib_tab, orient=tk.VERTICAL, command=self.games_tree.yview)
        self.games_tree.configure(yscrollcommand=scrollbar.set)
        
        self.games_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Контекстное меню
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="🚀 Запустить игру", command=self.launch_game)
        self.context_menu.add_command(label="⏹ Остановить фарм", command=self.stop_game)
        self.context_menu.add_command(label="🗑 Удалить из списка", command=self.remove_game)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📂 Открыть папку игры", command=self.open_game_folder)
        self.games_tree.bind("<Button-3>", self.show_context_menu)
        
        # Вкладка "DepotDownloader"
        depot_tab = ttk.Frame(notebook)
        notebook.add(depot_tab, text="DepotDownloader")
        
        ttk.Label(depot_tab, text="Путь к DepotDownloader.exe:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.dd_path_entry = ttk.Entry(depot_tab, width=60)
        self.dd_path_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(depot_tab, text="Обзор...", command=self.browse_depotdownloader).grid(row=0, column=2, padx=5)
        
        ttk.Label(depot_tab, text="AppID:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.dd_appid_entry = ttk.Entry(depot_tab, width=15)
        self.dd_appid_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(depot_tab, text="Depot ID:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.dd_depot_entry = ttk.Entry(depot_tab, width=15)
        self.dd_depot_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(depot_tab, text="Manifest ID:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.dd_manifest_entry = ttk.Entry(depot_tab, width=40)
        self.dd_manifest_entry.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(depot_tab, text="Папка для сохранения:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.dd_out_entry = ttk.Entry(depot_tab, width=60)
        self.dd_out_entry.grid(row=4, column=1, padx=5, pady=5)
        ttk.Button(depot_tab, text="Обзор...", command=self.browse_output_folder).grid(row=4, column=2, padx=5)
        
        ttk.Button(depot_tab, text="Скачать депо", command=self.thread_download_depot).grid(row=5, column=0, columnspan=3, pady=10)
        
        # Вкладка "Лог"
        log_tab = ttk.Frame(notebook)
        notebook.add(log_tab, text="Лог")
        
        self.log_area = scrolledtext.ScrolledText(log_tab, height=20, state='normal')
        self.log_area.pack(fill=tk.BOTH, expand=True)
        
        # Конфигурация
        self.config_dir = Path.home() / ".steam_tools_ultimate"
        self.config_dir.mkdir(exist_ok=True)
        self.games_file = self.config_dir / "games.json"
        
        # Загрузка данных
        self.active_games = self.load_games()
        self.running_processes = {}
        
        # Поиск Steam
        self.steam_path = self.find_steam_folder()
        if self.steam_path:
            self.log(f"Найдена папка Steam: {self.steam_path}")
        else:
            self.log("Не удалось найти папку Steam. Укажите путь вручную.", "ERROR")
            
        self.check_steam()
        self.update_games_list()
        
        self.log("SteamTools Ultimate FINAL запущен.")
        self.log("ВАЖНО: Для скачивания требуется DepotDownloader и наличие манифестов/ключей.")
        self.log("Добавление в библиотеку работает через создание appmanifest. Запускайте от администратора.")
        
    # ---------- Логи ----------
    def log(self, msg, level="INFO"):
        timestamp = time.strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] [{level}] {msg}\n")
        self.log_area.see(tk.END)
        self.root.update()
        
    # ---------- Проверка Steam ----------
    def check_steam(self):
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and 'steam' in proc.info['name'].lower():
                    self.steam_status.config(text=f"✅ Steam запущен (PID: {proc.pid})", foreground="green")
                    return True
            self.steam_status.config(text="❌ Steam не запущен", foreground="red")
            return False
        except:
            self.steam_status.config(text="❌ Ошибка проверки", foreground="orange")
            return False
            
    # ---------- Поиск папки Steam ----------
    def find_steam_folder(self):
        # Поиск через реестр
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
            steam_path = winreg.QueryValueEx(key, "SteamPath")[0]
            if steam_path and os.path.exists(steam_path):
                return steam_path.replace('/', '\\')
        except:
            pass
            
        # Стандартные пути
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
                
        # Если не нашли, предлагаем выбрать вручную
        path = filedialog.askdirectory(title="Укажите папку с Steam (где находится steam.exe)")
        if path and os.path.exists(os.path.join(path, "steam.exe")):
            return path
        return None
        
    # ---------- Получение названия игры ----------
    def get_game_name(self, appid):
        try:
            url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l=russian"
            r = requests.get(url, timeout=5)
            data = r.json()
            if data.get(appid, {}).get("success"):
                return data[appid]["data"]["name"]
        except:
            pass
        return f"Game_{appid}"
        
    # ---------- Создание манифеста ----------
    def create_manifest(self, appid, name):
        if not self.steam_path:
            self.log("Папка Steam не найдена. Добавление невозможно.", "ERROR")
            return False
            
        steamapps_path = os.path.join(self.steam_path, "steamapps")
        if not os.path.exists(steamapps_path):
            try:
                os.makedirs(steamapps_path)
            except Exception as e:
                self.log(f"Не удалось создать папку steamapps: {e}", "ERROR")
                return False
                
        # Проверка прав записи
        test_file = os.path.join(steamapps_path, "test_write.tmp")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except Exception as e:
            self.log(f"Нет прав на запись в {steamapps_path}. Запустите программу от администратора.", "ERROR")
            return False
            
        folder_name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        
        manifest = f'''"AppState"
{{
    "appid"		"{appid}"
    "Universe"		"1"
    "name"		"{name}"
    "installdir"		"{folder_name}"
    "StateFlags"		"4"
    "SizeOnDisk"		"0"
    "StagingSize"		"0"
    "buildid"		"0"
    "LastUpdated"		"{int(time.time())}"
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
                f.write(manifest)
            self.log(f"✓ Манифест создан: {manifest_path}")
            return True
        except Exception as e:
            self.log(f"Ошибка создания манифеста: {e}", "ERROR")
            return False
            
    # ---------- Добавление игры ----------
    def thread_add_game(self):
        threading.Thread(target=self.add_game, daemon=True).start()
        
    def add_game(self):
        appid = self.appid_entry.get().strip()
        if not appid or not appid.isdigit():
            self.log("Ошибка: введите корректный AppID", "ERROR")
            return
            
        name = self.get_game_name(appid)
        
        if self.create_manifest(appid, name):
            if not any(g['appid'] == appid for g in self.active_games):
                game_path = os.path.join(self.steam_path, "steamapps", "common", re.sub(r'[^a-zA-Z0-9_]', '_', name)) if self.steam_path else "-"
                self.active_games.append({
                    'appid': appid,
                    'name': name,
                    'status': 'в библиотеке',
                    'size': '-',
                    'path': game_path
                })
                self.save_games()
                self.update_games_list()
                
            self.log(f"✓ Игра {name} (AppID: {appid}) добавлена в библиотеку")
            self.add_status.config(text="✅ Игра добавлена, перезапустите Steam", foreground="green")
            
            if messagebox.askyesno("Перезапуск", "Перезапустить Steam сейчас? (рекомендуется)"):
                self.restart_steam()
        else:
            self.add_status.config(text="❌ Ошибка добавления", foreground="red")
            
    # ---------- Фарм часов ----------
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
            # Запускаем через Spacewar (ID 480)
            subprocess.Popen(f"steam://rungameid/480", shell=True)
            
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
                game['size'] = f"{hours}h (фарм)"
                self.update_games_list()
                
        except Exception as e:
            self.log(f"Ошибка фарма: {e}", "ERROR")
            game['status'] = 'ошибка'
            self.update_games_list()
            
    # ---------- DepotDownloader ----------
    def browse_depotdownloader(self):
        filename = filedialog.askopenfilename(title="Выберите DepotDownloader.exe", filetypes=[("Executable", "*.exe")])
        if filename:
            self.dd_path_entry.delete(0, tk.END)
            self.dd_path_entry.insert(0, filename)
            
    def browse_output_folder(self):
        folder = filedialog.askdirectory(title="Папка для сохранения")
        if folder:
            self.dd_out_entry.delete(0, tk.END)
            self.dd_out_entry.insert(0, folder)
            
    def thread_download_game(self):
        appid = self.appid_entry.get().strip()
        if not appid or not appid.isdigit():
            self.log("Ошибка: введите корректный AppID", "ERROR")
            return
            
        self.dd_appid_entry.delete(0, tk.END)
        self.dd_appid_entry.insert(0, appid)
        if self.depot_entry.get():
            self.dd_depot_entry.delete(0, tk.END)
            self.dd_depot_entry.insert(0, self.depot_entry.get())
        if self.manifest_entry.get():
            self.dd_manifest_entry.delete(0, tk.END)
            self.dd_manifest_entry.insert(0, self.manifest_entry.get())
            
        # Папка по умолчанию
        if self.steam_path:
            name = self.get_game_name(appid)
            default_out = os.path.join(self.steam_path, "steamapps", "common", re.sub(r'[^a-zA-Z0-9_]', '_', name))
            self.dd_out_entry.delete(0, tk.END)
            self.dd_out_entry.insert(0, default_out)
            
        self.log("Перейдите на вкладку DepotDownloader и укажите параметры.")
        # Переключение на вкладку (не реализовано, можно вручную)
        
    def thread_download_depot(self):
        threading.Thread(target=self.download_depot, daemon=True).start()
        
    def download_depot(self):
        depotdownloader = self.dd_path_entry.get().strip()
        if not depotdownloader or not os.path.exists(depotdownloader):
            self.log("Укажите корректный путь к DepotDownloader.exe", "ERROR")
            return
            
        appid = self.dd_appid_entry.get().strip()
        depot = self.dd_depot_entry.get().strip()
        manifest = self.dd_manifest_entry.get().strip()
        out_dir = self.dd_out_entry.get().strip()
        
        if not appid or not depot or not manifest:
            self.log("Необходимо указать AppID, Depot ID и Manifest ID", "ERROR")
            return
            
        if not out_dir:
            self.log("Укажите папку для сохранения", "ERROR")
            return
            
        os.makedirs(out_dir, exist_ok=True)
        
        cmd = [
            depotdownloader,
            "-app", appid,
            "-depot", depot,
            "-manifest", manifest,
            "-dir", out_dir
        ]
        
        self.log(f"Запуск DepotDownloader: {' '.join(cmd)}")
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            for line in process.stdout:
                self.log(line.strip())
            process.wait()
            if process.returncode == 0:
                self.log(f"✓ Депо {depot} успешно скачано в {out_dir}")
                # Обновляем игру в списке
                for game in self.active_games:
                    if game['appid'] == appid:
                        game['status'] = 'скачано'
                        game['path'] = out_dir
                        # Размер
                        total = 0
                        for root, dirs, files in os.walk(out_dir):
                            for f in files:
                                fp = os.path.join(root, f)
                                total += os.path.getsize(fp)
                        game['size'] = self.format_bytes(total)
                        break
                self.save_games()
                self.update_games_list()
            else:
                self.log(f"Ошибка DepotDownloader (код {process.returncode})", "ERROR")
        except Exception as e:
            self.log(f"Исключение при запуске DepotDownloader: {e}", "ERROR")
            
    def format_bytes(self, bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} TB"
        
    # ---------- GreenLuma (эмуляция запуска) ----------
    def thread_greenluma(self):
        selected = self.games_tree.selection()
        if not selected:
            messagebox.showwarning("Выбор игры", "Выберите игру в списке")
            return
        item = self.games_tree.item(selected[0])
        appid = item['values'][0]
        threading.Thread(target=self.run_greenluma, args=(appid,), daemon=True).start()
        
    def run_greenluma(self, appid):
        # Проверяем наличие GreenLuma
        greenluma_path = os.path.join(self.steam_path, "GreenLuma_2024", "GreenLuma.exe") if self.steam_path else None
        if not greenluma_path or not os.path.exists(greenluma_path):
            self.log("GreenLuma не найден. Скачайте и распакуйте в папку Steam/GreenLuma_2024/", "ERROR")
            return
            
        self.log(f"Запуск GreenLuma для AppID {appid}...")
        try:
            # GreenLuma обычно требует списка AppID в файле AppList.txt
            applist_path = os.path.join(os.path.dirname(greenluma_path), "AppList.txt")
            with open(applist_path, 'w') as f:
                f.write(appid)
                
            subprocess.Popen([greenluma_path], cwd=os.path.dirname(greenluma_path))
            self.log(f"GreenLuma запущен. Steam перезапустится с эмуляцией игры {appid}.")
        except Exception as e:
            self.log(f"Ошибка запуска GreenLuma: {e}", "ERROR")
            
    # ---------- Управление списком игр ----------
    def launch_game(self):
        selected = self.games_tree.selection()
        if not selected:
            return
        item = self.games_tree.item(selected[0])
        appid = item['values'][0]
        subprocess.Popen(f"steam://rungameid/{appid}", shell=True)
        self.log(f"Запуск игры {appid}")
        
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
                g['size'] = '-'
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
        
    def open_game_folder(self):
        selected = self.games_tree.selection()
        if not selected:
            return
        item = self.games_tree.item(selected[0])
        path = item['values'][4]
        
        if path and path != '-' and os.path.exists(path):
            os.startfile(path)
        else:
            self.log("Папка игры не найдена", "WARNING")
            
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
                g['appid'], g['name'], g['status'], g['size'], g['path']
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
        
    def restart_steam(self):
        try:
            os.system("taskkill /f /im steam.exe")
            time.sleep(3)
            if self.steam_path:
                exe = os.path.join(self.steam_path, "steam.exe")
                subprocess.Popen([exe])
                self.log("Steam перезапущен")
        except Exception as e:
            self.log(f"Ошибка перезапуска Steam: {e}", "ERROR")

if __name__ == "__main__":
    if sys.platform != "win32":
        print("Эта программа предназначена для Windows.")
        sys.exit(1)
        
    try:
        import psutil
    except ImportError:
        print("Установите psutil: pip install psutil")
        sys.exit(1)
        
    # Проверка прав администратора
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False
        
    if not is_admin:
        print("Рекомендуется запустить программу от имени администратора для доступа к папке Steam.")
        # Можно продолжить, но предупредим
        
    root = tk.Tk()
    app = SteamToolsUltimate(root)
    root.mainloop()
