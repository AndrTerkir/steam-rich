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
import socket
import http.server
import socketserver
import urllib.parse
from pathlib import Path
import psutil
import winreg
import ctypes
import tempfile
import zipfile
import hashlib

class SteamToolsUltimate:
    def __init__(self, root):
        self.root = root
        self.root.title("SteamTools Ultimate [HARDCORE MODE]")
        self.root.geometry("1200x750")
        
        # Настройка стиля
        style = ttk.Style()
        style.theme_use('clam')
        
        # Основной контейнер
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Верхняя панель с элементами управления
        top_frame = ttk.LabelFrame(main_frame, text="Управление", padding="10")
        top_frame.pack(fill=tk.X, pady=5)
        
        # AppID
        ttk.Label(top_frame, text="AppID:").grid(row=0, column=0, sticky=tk.W)
        self.appid_entry = ttk.Entry(top_frame, width=15)
        self.appid_entry.grid(row=0, column=1, padx=5, sticky=tk.W)
        
        # Depot ID (опционально)
        ttk.Label(top_frame, text="Depot ID (если известно):").grid(row=0, column=2, sticky=tk.W, padx=(20,0))
        self.depot_entry = ttk.Entry(top_frame, width=15)
        self.depot_entry.grid(row=0, column=3, padx=5, sticky=tk.W)
        
        # Manifest ID (опционально)
        ttk.Label(top_frame, text="Manifest ID:").grid(row=0, column=4, sticky=tk.W, padx=(20,0))
        self.manifest_entry = ttk.Entry(top_frame, width=30)
        self.manifest_entry.grid(row=0, column=5, padx=5, sticky=tk.W)
        
        # Кнопки
        btn_frame = ttk.Frame(top_frame)
        btn_frame.grid(row=1, column=0, columnspan=6, pady=10)
        
        self.add_btn = ttk.Button(btn_frame, text="➕ Добавить в библиотеку", command=self.thread_add_game)
        self.add_btn.pack(side=tk.LEFT, padx=2)
        
        self.download_btn = ttk.Button(btn_frame, text="⬇ Скачать игру (DepotDownloader)", command=self.thread_download_game)
        self.download_btn.pack(side=tk.LEFT, padx=2)
        
        self.proxy_btn = ttk.Button(btn_frame, text="🔄 Запустить перехват трафика (MITM)", command=self.thread_start_proxy)
        self.proxy_btn.pack(side=tk.LEFT, padx=2)
        
        self.farm_btn = ttk.Button(btn_frame, text="⏱ Фарм часов", command=self.thread_farm_hours)
        self.farm_btn.pack(side=tk.LEFT, padx=2)
        
        self.inject_btn = ttk.Button(btn_frame, text="💉 Инжект DLL (хуки)", command=self.thread_inject_dll)
        self.inject_btn.pack(side=tk.LEFT, padx=2)
        
        # Статусная строка
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.steam_status = ttk.Label(status_frame, text="🔍 Steam: проверка...")
        self.steam_status.pack(side=tk.LEFT, padx=5)
        
        self.proxy_status = ttk.Label(status_frame, text="🔴 Прокси: выключен")
        self.proxy_status.pack(side=tk.LEFT, padx=5)
        
        self.hook_status = ttk.Label(status_frame, text="🔴 Хуки: не активны")
        self.hook_status.pack(side=tk.LEFT, padx=5)
        
        # Основное содержимое: вкладки
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Вкладка "Библиотека"
        lib_tab = ttk.Frame(notebook)
        notebook.add(lib_tab, text="Библиотека")
        
        # Таблица игр
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
        
        # Контекстное меню для таблицы
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="🚀 Запустить игру", command=self.launch_game)
        self.context_menu.add_command(label="⏹ Остановить фарм", command=self.stop_game)
        self.context_menu.add_command(label="🗑 Удалить из списка", command=self.remove_game)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📂 Открыть папку игры", command=self.open_game_folder)
        self.context_menu.add_command(label="🔑 Получить ключи депо", command=self.get_depot_keys)
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
        
        # Вкладка "Хардкор" (DLL инжектор)
        hack_tab = ttk.Frame(notebook)
        notebook.add(hack_tab, text="Хардкор (DLL инжектор)")
        
        ttk.Label(hack_tab, text="PID процесса Steam:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.pid_entry = ttk.Entry(hack_tab, width=10)
        self.pid_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Button(hack_tab, text="Найти PID", command=self.find_steam_pid).grid(row=0, column=2, padx=5)
        
        ttk.Label(hack_tab, text="Путь к DLL для инжекта:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.dll_entry = ttk.Entry(hack_tab, width=60)
        self.dll_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(hack_tab, text="Обзор...", command=self.browse_dll).grid(row=1, column=2, padx=5)
        
        ttk.Button(hack_tab, text="💉 Инжектировать DLL", command=self.thread_inject_dll).grid(row=2, column=0, columnspan=3, pady=10)
        
        ttk.Label(hack_tab, text="Пример DLL-хука (C++ с MinHook) будет создана автоматически", foreground="gray").grid(row=3, column=0, columnspan=3, pady=5)
        ttk.Button(hack_tab, text="Сгенерировать DLL-заглушку", command=self.generate_dll_stub).grid(row=4, column=0, columnspan=3, pady=5)
        
        # Конфигурация
        self.config_dir = Path.home() / ".steam_tools_ultimate"
        self.config_dir.mkdir(exist_ok=True)
        self.games_file = self.config_dir / "games.json"
        self.depotdownloader_path = self.config_dir / "DepotDownloader.exe"
        self.dll_stub_path = self.config_dir / "steam_hook.dll"
        
        # Загрузка сохранённых игр
        self.active_games = self.load_games()
        self.running_processes = {}
        self.proxy_server = None
        self.proxy_thread = None
        
        # Инициализация
        self.check_steam()
        self.check_depotdownloader()
        self.update_games_list()
        
        self.log("SteamTools Ultimate запущен. Режим: HARDCORE")
        self.log("ВНИМАНИЕ: Использование для нелегальных целей запрещено. Код предоставлен в образовательных целях.")
        
    # ---------- Вспомогательные функции ----------
    def log(self, msg, level="INFO"):
        timestamp = time.strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] [{level}] {msg}\n")
        self.log_area.see(tk.END)
        self.root.update()
        
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
            
    def find_steam_pid(self):
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] and 'steam' in proc.info['name'].lower():
                self.pid_entry.delete(0, tk.END)
                self.pid_entry.insert(0, str(proc.info['pid']))
                self.log(f"Найден Steam PID: {proc.info['pid']}")
                return
        self.log("Steam не найден", "ERROR")
        
    def check_depotdownloader(self):
        if not self.depotdownloader_path.exists():
            self.log("DepotDownloader не найден. Нажмите 'Обзор...' и укажите путь к DepotDownloader.exe", "WARNING")
        else:
            self.dd_path_entry.delete(0, tk.END)
            self.dd_path_entry.insert(0, str(self.depotdownloader_path))
            
    def browse_depotdownloader(self):
        filename = filedialog.askopenfilename(title="Выберите DepotDownloader.exe", filetypes=[("Executable", "*.exe")])
        if filename:
            self.depotdownloader_path = Path(filename)
            self.dd_path_entry.delete(0, tk.END)
            self.dd_path_entry.insert(0, filename)
            
    def browse_output_folder(self):
        folder = filedialog.askdirectory(title="Папка для сохранения")
        if folder:
            self.dd_out_entry.delete(0, tk.END)
            self.dd_out_entry.insert(0, folder)
            
    def browse_dll(self):
        filename = filedialog.askopenfilename(title="Выберите DLL", filetypes=[("DLL", "*.dll")])
        if filename:
            self.dll_entry.delete(0, tk.END)
            self.dll_entry.insert(0, filename)
            
    def find_steam_folder(self):
        if sys.platform == "win32":
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
                steam_path = winreg.QueryValueEx(key, "SteamPath")[0]
                return steam_path.replace('/', '\\')
            except:
                pass
            candidates = [
                "C:\\Program Files (x86)\\Steam",
                "C:\\Program Files\\Steam",
                os.path.expanduser("~\\AppData\\Local\\Steam")
            ]
            for path in candidates:
                if os.path.exists(os.path.join(path, "steam.exe")):
                    return path
        return None
        
    # ---------- Работа с манифестами (добавление в библиотеку) ----------
    def create_manifest(self, appid, name):
        steam_path = self.find_steam_folder()
        if not steam_path:
            self.log("Не удалось найти папку Steam", "ERROR")
            return False
            
        steamapps_path = os.path.join(steam_path, "steamapps")
        os.makedirs(steamapps_path, exist_ok=True)
        
        # Генерируем имя папки
        folder_name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        
        manifest = f'''"AppState"
{{
    "appid"		"{appid}"
    "Universe"		"1"
    "name"		"{name}"
    "installdir"		"{folder_name}"
    "StateFlags"		"4"
    "SizeOnDisk"		"1"
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
            
    def thread_add_game(self):
        threading.Thread(target=self.add_game, daemon=True).start()
        
    def add_game(self):
        appid = self.appid_entry.get().strip()
        if not appid or not appid.isdigit():
            self.log("Ошибка: введите корректный AppID", "ERROR")
            return
            
        # Получаем название игры через API
        name = self.name_entry.get().strip()
        if not name:
            try:
                url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l=russian"
                r = requests.get(url, timeout=5)
                data = r.json()
                if data.get(appid, {}).get("success"):
                    name = data[appid]["data"]["name"]
                else:
                    name = f"Game_{appid}"
            except:
                name = f"Game_{appid}"
                
        if self.create_manifest(appid, name):
            # Проверяем, есть ли уже в списке
            if not any(g['appid'] == appid for g in self.active_games):
                self.active_games.append({
                    'appid': appid,
                    'name': name,
                    'status': 'в библиотеке',
                    'size': '-',
                    'path': os.path.join(self.find_steam_folder(), "steamapps", "common", re.sub(r'[^a-zA-Z0-9_]', '_', name))
                })
                self.save_games()
                self.update_games_list()
                
            self.log(f"✓ Игра {name} (AppID: {appid}) добавлена в библиотеку")
            
            if messagebox.askyesno("Перезапуск", "Перезапустить Steam для применения?"):
                self.restart_steam()
                
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
            # Запускаем через Spacewar (ID 480) — есть у всех
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
            
    # ---------- DepotDownloader (скачивание) ----------
    def thread_download_game(self):
        appid = self.appid_entry.get().strip()
        if not appid or not appid.isdigit():
            self.log("Ошибка: введите корректный AppID", "ERROR")
            return
            
        name = self.name_entry.get().strip()
        if not name:
            name = f"Game_{appid}"
            
        # Заполняем поля вкладки DepotDownloader
        self.dd_appid_entry.delete(0, tk.END)
        self.dd_appid_entry.insert(0, appid)
        if self.depot_entry.get():
            self.dd_depot_entry.delete(0, tk.END)
            self.dd_depot_entry.insert(0, self.depot_entry.get())
        if self.manifest_entry.get():
            self.dd_manifest_entry.delete(0, tk.END)
            self.dd_manifest_entry.insert(0, self.manifest_entry.get())
            
        # Предлагаем выбрать папку для сохранения
        steam_path = self.find_steam_folder()
        default_out = os.path.join(steam_path, "steamapps", "common", re.sub(r'[^a-zA-Z0-9_]', '_', name)) if steam_path else ""
        self.dd_out_entry.delete(0, tk.END)
        self.dd_out_entry.insert(0, default_out)
        
        self.log("Перейдите на вкладку DepotDownloader и нажмите 'Скачать депо'")
        notebook.select(1)  # переключаем на вкладку DepotDownloader
        
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
        
        # Формируем команду для DepotDownloader
        # Пример: DepotDownloader.exe -app 730 -depot 731 -manifest 1234567890123456789 -dir "C:\out"
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
                # Обновляем статус игры, если она есть в списке
                for game in self.active_games:
                    if game['appid'] == appid:
                        game['status'] = 'скачано'
                        game['path'] = out_dir
                        # Попытаемся определить размер
                        try:
                            total_size = 0
                            for root, dirs, files in os.walk(out_dir):
                                for f in files:
                                    fp = os.path.join(root, f)
                                    total_size += os.path.getsize(fp)
                            game['size'] = self.format_bytes(total_size)
                        except:
                            pass
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
        
    # ---------- Перехват трафика (MITM) ----------
    class SteamProxyHandler(http.server.BaseHTTPRequestHandler):
        def __init__(self, *args, parent=None, **kwargs):
            self.parent = parent
            super().__init__(*args, **kwargs)
            
        def do_CONNECT(self):
            # Туннелирование для HTTPS
            self.send_response(200, "Connection Established")
            self.end_headers()
            
        def do_GET(self):
            self.parent.log(f"Перехвачен GET: {self.path}")
            # Проверяем, запрос на проверку владения
            if "ISteamUser/CheckAppOwnership" in self.path:
                match = re.search(r'appid=(\d+)', self.path)
                if match:
                    appid = match.group(1)
                    self.parent.log(f"🍔 Перехвачен запрос лицензии для AppID {appid}, подменяем ответ")
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = {
                        "appownership": {
                            "owned": True,
                            "permanent": True,
                            "result": "OK"
                        }
                    }
                    self.wfile.write(json.dumps(response).encode())
                    return
            # В противном случае просто проксируем (здесь нужно реализовать полноценный прокси)
            self.send_response(404)
            self.end_headers()
            
        def do_POST(self):
            self.parent.log(f"Перехвачен POST: {self.path}")
            self.send_response(200)
            self.end_headers()
            
        def log_message(self, format, *args):
            # Подавляем стандартный лог
            pass
            
    def start_proxy(self):
        try:
            port = 27060  # Стандартный порт Steam (или выберите любой)
            handler = lambda *args, **kwargs: self.SteamProxyHandler(*args, parent=self, **kwargs)
            self.proxy_server = socketserver.TCPServer(("", port), handler)
            self.proxy_status.config(text=f"🟢 Прокси запущен на порту {port}", foreground="green")
            self.log(f"Прокси-сервер запущен на порту {port}")
            self.log("Для использования настройте Steam на использование прокси (127.0.0.1:{port})")
            self.log("⚠ Из-за certificate pinning подмена HTTPS может не работать без патча Steam.")
            self.proxy_server.serve_forever()
        except Exception as e:
            self.log(f"Ошибка прокси: {e}", "ERROR")
            self.proxy_status.config(text="🔴 Ошибка прокси", foreground="red")
            
    def thread_start_proxy(self):
        if self.proxy_server:
            self.log("Прокси уже запущен")
            return
        threading.Thread(target=self.start_proxy, daemon=True).start()
        
    # ---------- Инжект DLL (хардкор) ----------
    def thread_inject_dll(self):
        threading.Thread(target=self.inject_dll, daemon=True).start()
        
    def inject_dll(self):
        pid_str = self.pid_entry.get().strip()
        dll_path = self.dll_entry.get().strip()
        
        if not pid_str or not pid_str.isdigit():
            self.log("Введите корректный PID процесса Steam", "ERROR")
            return
        if not dll_path or not os.path.exists(dll_path):
            self.log("Укажите существующий путь к DLL", "ERROR")
            return
            
        pid = int(pid_str)
        
        # Используем Windows API для инжекта
        try:
            import ctypes
            from ctypes import wintypes
            
            # Открываем процесс
            PROCESS_ALL_ACCESS = 0x1F0FFF
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            
            hProcess = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
            if not hProcess:
                self.log(f"Не удалось открыть процесс (код ошибки: {ctypes.get_last_error()})", "ERROR")
                return
                
            # Выделяем память в целевом процессе
            dll_path_bytes = dll_path.encode('utf-8')
            alloc_size = len(dll_path_bytes) + 1
            alloc_addr = kernel32.VirtualAllocEx(hProcess, None, alloc_size, 0x3000, 0x40)  # MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE
            
            if not alloc_addr:
                self.log("VirtualAllocEx не удался", "ERROR")
                kernel32.CloseHandle(hProcess)
                return
                
            # Записываем путь к DLL
            written = ctypes.c_size_t(0)
            if not kernel32.WriteProcessMemory(hProcess, alloc_addr, dll_path_bytes, alloc_size, ctypes.byref(written)):
                self.log("WriteProcessMemory не удался", "ERROR")
                kernel32.VirtualFreeEx(hProcess, alloc_addr, 0, 0x8000)  # MEM_RELEASE
                kernel32.CloseHandle(hProcess)
                return
                
            # Создаём удалённый поток для загрузки DLL
            kernel32_getpid = kernel32.GetProcAddress(kernel32._handle, b"LoadLibraryA")
            if not kernel32_getpid:
                self.log("Не удалось найти адрес LoadLibraryA", "ERROR")
                kernel32.VirtualFreeEx(hProcess, alloc_addr, 0, 0x8000)
                kernel32.CloseHandle(hProcess)
                return
                
            hThread = kernel32.CreateRemoteThread(hProcess, None, 0, kernel32_getpid, alloc_addr, 0, None)
            if not hThread:
                self.log("CreateRemoteThread не удался", "ERROR")
                kernel32.VirtualFreeEx(hProcess, alloc_addr, 0, 0x8000)
                kernel32.CloseHandle(hProcess)
                return
                
            self.log(f"✓ DLL инжектирована в процесс {pid}. Поток создан.")
            self.hook_status.config(text="🟢 Хуки активны (инжект выполнен)", foreground="green")
            
            # Ждём завершения потока (опционально)
            kernel32.WaitForSingleObject(hThread, 30000)
            
            kernel32.CloseHandle(hThread)
            kernel32.CloseHandle(hProcess)
            
        except Exception as e:
            self.log(f"Ошибка при инжекте: {e}", "ERROR")
            
    def generate_dll_stub(self):
        """Генерирует простую DLL-заглушку с MinHook для перехвата функции BIsSubscribedApp"""
        dll_source = '''#include <Windows.h>
#include "MinHook.h"

typedef bool (*IsSubscribedApp_t)(uint32_t appID);
IsSubscribedApp_t original_IsSubscribedApp = nullptr;

bool Hooked_IsSubscribedApp(uint32_t appID) {
    // Всегда возвращаем true для любого AppID
    return true;
}

void HookSteamAPI() {
    // Получаем адрес функции из steam_api.dll
    HMODULE hSteamAPI = GetModuleHandleA("steam_api.dll");
    if (!hSteamAPI) {
        hSteamAPI = GetModuleHandleA("steam_api64.dll");
    }
    if (!hSteamAPI) return;
    
    // Адрес функции BIsSubscribedApp (нужно найти точный сдвиг)
    // В разных версиях адрес может отличаться. Для примера используем сигнатуру.
    // Реальный адрес нужно определить через дизассемблер.
    uintptr_t targetAddr = (uintptr_t)hSteamAPI + 0x12345; // Замените на реальный оффсет
    
    if (MH_Initialize() != MH_OK) return;
    MH_CreateHook((void*)targetAddr, &Hooked_IsSubscribedApp, (void**)&original_IsSubscribedApp);
    MH_EnableHook((void*)targetAddr);
}

BOOL APIENTRY DllMain(HMODULE hModule, DWORD ul_reason_for_call, LPVOID lpReserved) {
    if (ul_reason_for_call == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(hModule);
        CreateThread(NULL, 0, [](LPVOID) -> DWORD {
            Sleep(1000); // Ждём загрузки steam_api.dll
            HookSteamAPI();
            return 0;
        }, NULL, 0, NULL);
    }
    return TRUE;
}
'''
        # Создаём временную папку и компилируем (если есть компилятор)
        self.log("Генерация DLL-заглушки...")
        stub_dir = self.config_dir / "dll_stub"
        stub_dir.mkdir(exist_ok=True)
        
        source_file = stub_dir / "hook.cpp"
        with open(source_file, 'w') as f:
            f.write(dll_source)
            
        # Попытка скомпилировать с помощью MSVC (если cl.exe доступен)
        cl_path = shutil.which("cl.exe")
        if cl_path:
            cmd = [cl_path, "/LD", "/Fe" + str(self.dll_stub_path), str(source_file)]
            try:
                subprocess.run(cmd, cwd=stub_dir, check=True, capture_output=True)
                self.log(f"✓ DLL скомпилирована: {self.dll_stub_path}")
                self.dll_entry.delete(0, tk.END)
                self.dll_entry.insert(0, str(self.dll_stub_path))
            except subprocess.CalledProcessError as e:
                self.log(f"Ошибка компиляции: {e.stderr.decode() if e.stderr else ''}", "ERROR")
        else:
            self.log("Компилятор MSVC не найден. Скомпилируйте DLL вручную из исходника:\n" + str(source_file), "WARNING")
            
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
            
    def get_depot_keys(self):
        selected = self.games_tree.selection()
        if not selected:
            return
        item = self.games_tree.item(selected[0])
        appid = item['values'][0]
        self.log(f"Поиск ключей депо для AppID {appid}... (функция в разработке)")
        
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
            steam_path = self.find_steam_folder()
            if steam_path:
                exe = os.path.join(steam_path, "steam.exe")
                subprocess.Popen([exe])
                self.log("Steam перезапущен")
        except Exception as e:
            self.log(f"Ошибка перезапуска Steam: {e}", "ERROR")

if __name__ == "__main__":
    if sys.platform != "win32":
        print("Эта программа предназначена для Windows.")
        sys.exit(1)
        
    # Проверка наличия необходимых библиотек
    try:
        import psutil
    except ImportError:
        print("Установите psutil: pip install psutil")
        sys.exit(1)
        
    root = tk.Tk()
    app = SteamToolsUltimate(root)
    root.mainloop()
