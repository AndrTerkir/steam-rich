import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import subprocess
import os
import json
import time
import requests
from pathlib import Path
import pickle
import sys

class SteamToolsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Steam Tools Pro [RAGE MODE]")
        self.root.geometry("900x600")
        
        # Настройка стилей
        style = ttk.Style()
        style.theme_use('clam')
        
        # Основной контейнер
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Верхняя панель с ссылкой
        top_frame = ttk.LabelFrame(main_frame, text="Добавление игры", padding="10")
        top_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(top_frame, text="Steam URL или AppID:").grid(row=0, column=0, sticky=tk.W)
        self.url_entry = ttk.Entry(top_frame, width=60)
        self.url_entry.grid(row=0, column=1, padx=5, sticky=tk.W+tk.E)
        
        # Кнопки действий
        btn_frame = ttk.Frame(top_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        self.add_btn = ttk.Button(btn_frame, text="➕ Добавить игру", command=self.start_add_game)
        self.add_btn.pack(side=tk.LEFT, padx=2)
        
        self.farm_btn = ttk.Button(btn_frame, text="⏱️ Фарм часов", command=self.start_farm_hours)
        self.farm_btn.pack(side=tk.LEFT, padx=2)
        
        self.cards_btn = ttk.Button(btn_frame, text="🎴 Дроп карт", command=self.start_drop_cards)
        self.cards_btn.pack(side=tk.LEFT, padx=2)
        
        # Панель статуса Steam
        status_frame = ttk.LabelFrame(main_frame, text="Статус Steam", padding="5")
        status_frame.pack(fill=tk.X, pady=5)
        
        self.steam_status = ttk.Label(status_frame, text="❌ Steam не обнаружен", foreground="red")
        self.steam_status.pack(side=tk.LEFT)
        
        ttk.Button(status_frame, text="🔍 Проверить Steam", command=self.check_steam).pack(side=tk.RIGHT)
        
        # Панель с играми
        games_frame = ttk.LabelFrame(main_frame, text="Активные процессы", padding="10")
        games_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Таблица игр
        columns = ('appid', 'name', 'status', 'time')
        self.games_tree = ttk.Treeview(games_frame, columns=columns, show='headings', height=8)
        self.games_tree.heading('appid', text='AppID')
        self.games_tree.heading('name', text='Название')
        self.games_tree.heading('status', text='Статус')
        self.games_tree.heading('time', text='Время')
        
        self.games_tree.column('appid', width=80)
        self.games_tree.column('name', width=200)
        self.games_tree.column('status', width=100)
        self.games_tree.column('time', width=100)
        
        scrollbar = ttk.Scrollbar(games_frame, orient=tk.VERTICAL, command=self.games_tree.yview)
        self.games_tree.configure(yscrollcommand=scrollbar.set)
        
        self.games_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Контекстное меню для таблицы
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Остановить", command=self.stop_game)
        self.context_menu.add_command(label="Удалить из списка", command=self.remove_from_list)
        self.games_tree.bind("<Button-3>", self.show_context_menu)
        
        # Лог
        log_frame = ttk.LabelFrame(main_frame, text="Лог операций", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, height=10, state='normal')
        self.log_area.pack(fill=tk.BOTH, expand=True)
        
        # Конфиг
        self.config_dir = Path.home() / ".steam_tools"
        self.config_dir.mkdir(exist_ok=True)
        self.cookies_file = self.config_dir / "steam_cookies.pkl"
        self.games_file = self.config_dir / "active_games.json"
        
        # Загружаем сохраненные игры
        self.active_games = self.load_active_games()
        self.update_games_list()
        
        # Проверяем Steam при запуске
        self.check_steam()
        
        self.log("Steam Tools Pro активирован")
        self.log("Режим: полный доступ")
        
    def log(self, message, level="INFO"):
        """Логирование с таймстампом"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] [{level}] {message}\n")
        self.log_area.see(tk.END)
        self.root.update()
        
    def check_steam(self):
        """Проверка наличия запущенного Steam"""
        try:
            if sys.platform == "win32":
                output = subprocess.check_output("tasklist | findstr steam.exe", shell=True).decode()
                if "steam.exe" in output:
                    self.steam_status.config(text="✅ Steam запущен", foreground="green")
                    return True
            elif sys.platform == "linux":
                output = subprocess.check_output("ps aux | grep steam", shell=True).decode()
                if "steam" in output:
                    self.steam_status.config(text="✅ Steam запущен", foreground="green")
                    return True
            elif sys.platform == "darwin":
                output = subprocess.check_output("ps aux | grep Steam", shell=True).decode()
                if "Steam.app" in output:
                    self.steam_status.config(text="✅ Steam запущен", foreground="green")
                    return True
        except:
            pass
        
        self.steam_status.config(text="❌ Steam не запущен", foreground="red")
        return False
        
    def extract_appid(self, input_text):
        """Извлекает AppID из ссылки или текста"""
        input_text = input_text.strip()
        
        # Если это просто число
        if input_text.isdigit():
            return input_text
            
        # Извлекаем из URL Steam
        if "store.steampowered.com/app/" in input_text:
            try:
                appid = input_text.split("/app/")[1].split("/")[0]
                if appid.isdigit():
                    return appid
            except:
                pass
                
        # Извлекаем из URL SteamDB
        if "steamdb.info/app/" in input_text:
            try:
                appid = input_text.split("/app/")[1].split("/")[0]
                if appid.isdigit():
                    return appid
            except:
                pass
                
        return None
        
    def get_game_name(self, appid):
        """Получает название игры через Steam API"""
        try:
            url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if data.get(str(appid), {}).get("success"):
                return data[str(appid)]["data"]["name"]
        except:
            pass
        return f"Game {appid}"
        
    def start_add_game(self):
        """Запуск добавления игры"""
        if not self.check_steam():
            if not messagebox.askyesno("Steam не запущен", "Steam не запущен. Запустить Steam сейчас?"):
                return
            self.start_steam()
            time.sleep(5)
            
        input_text = self.url_entry.get()
        appid = self.extract_appid(input_text)
        
        if not appid:
            messagebox.showerror("Ошибка", "Не удалось распознать AppID")
            return
            
        thread = threading.Thread(target=self.add_game, args=(appid,))
        thread.daemon = True
        thread.start()
        
    def add_game(self, appid):
        """Добавление игры в библиотеку через API"""
        self.log(f"Добавление игры {appid}...")
        
        try:
            game_name = self.get_game_name(appid)
            
            # Проверяем, есть ли уже игра в активных
            if appid in [g['appid'] for g in self.active_games]:
                self.log(f"Игра {game_name} уже в списке", "WARNING")
                return
                
            # Метод 1: Через бесплатную лицензию (если игра бесплатная)
            free_check = requests.get(f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=us")
            data = free_check.json()
            
            is_free = data.get(str(appid), {}).get("data", {}).get("is_free", False)
            price = data.get(str(appid), {}).get("data", {}).get("price_overview", {})
            
            if is_free or (price and price.get("final", 999) == 0):
                self.log(f"Обнаружена бесплатная игра: {game_name}")
                self.add_free_license(appid)
            else:
                self.log(f"Платная игра: {game_name}. Добавляю в список фарма")
                
            # Добавляем в активные игры для фарма
            self.active_games.append({
                'appid': appid,
                'name': game_name,
                'status': 'ожидание',
                'time': '0h',
                'process': None
            })
            self.save_active_games()
            self.update_games_list()
            
            self.log(f"✓ Игра {game_name} добавлена")
            
        except Exception as e:
            self.log(f"Ошибка при добавлении: {str(e)}", "ERROR")
            
    def add_free_license(self, appid):
        """Добавление бесплатной лицензии"""
        try:
            # Это упрощенная версия, полная реализация требует сессию
            self.log(f"Попытка активации бесплатной лицензии для {appid}")
            # Здесь должен быть код с сессией Steam
            # Можно использовать библиотеку steampy или аналоги
        except Exception as e:
            self.log(f"Не удалось активировать лицензию: {e}", "WARNING")
            
    def start_farm_hours(self):
        """Запуск фарма часов для выбранной игры"""
        selected = self.games_tree.selection()
        if not selected:
            messagebox.showwarning("Выбор игры", "Сначала выберите игру из списка")
            return
            
        item = self.games_tree.item(selected[0])
        appid = item['values'][0]
        
        thread = threading.Thread(target=self.farm_hours, args=(appid,))
        thread.daemon = True
        thread.start()
        
    def farm_hours(self, appid):
        """Фарм часов через имитацию запуска"""
        self.log(f"Запуск фарма часов для AppID: {appid}")
        
        # Обновляем статус
        for game in self.active_games:
            if game['appid'] == appid:
                game['status'] = 'фарм часов'
                break
        self.update_games_list()
        
        try:
            # Метод 1: через steam:// запуск
            subprocess.Popen(f"steam://rungameid/{appid}", shell=True)
            self.log(f"Запущена имитация игры {appid}")
            
            # Метод 2: через создание фейкового процесса
            if sys.platform == "win32":
                # Создаем пустой процесс с именем игры
                fake_process = subprocess.Popen(["cmd.exe", "/c", "timeout", "/t", "99999"], 
                                              creationflags=subprocess.CREATE_NO_WINDOW)
                for game in self.active_games:
                    if game['appid'] == appid:
                        game['process'] = fake_process
                        break
                        
            # Обновляем время каждую минуту
            start_time = time.time()
            while True:
                time.sleep(60)
                hours = round((time.time() - start_time) / 3600, 1)
                for game in self.active_games:
                    if game['appid'] == appid:
                        game['time'] = f"{hours}h"
                        break
                self.update_games_list()
                
        except Exception as e:
            self.log(f"Ошибка фарма: {e}", "ERROR")
            for game in self.active_games:
                if game['appid'] == appid:
                    game['status'] = 'ошибка'
                    break
            self.update_games_list()
            
    def start_drop_cards(self):
        """Запуск дропа карт"""
        selected = self.games_tree.selection()
        if not selected:
            messagebox.showwarning("Выбор игры", "Сначала выберите игру из списка")
            return
            
        item = self.games_tree.item(selected[0])
        appid = item['values'][0]
        
        thread = threading.Thread(target=self.drop_cards, args=(appid,))
        thread.daemon = True
        thread.start()
        
    def drop_cards(self, appid):
        """Дроп карт через ASF или имитацию"""
        self.log(f"Запуск дропа карт для {appid}")
        
        for game in self.active_games:
            if game['appid'] == appid:
                game['status'] = 'дроп карт'
                break
        self.update_games_list()
        
        # Запускаем фарм часов для дропа карт
        self.farm_hours(appid)
        
    def stop_game(self):
        """Остановка активного процесса"""
        selected = self.games_tree.selection()
        if not selected:
            return
            
        item = self.games_tree.item(selected[0])
        appid = item['values'][0]
        
        for game in self.active_games:
            if game['appid'] == appid and game.get('process'):
                try:
                    game['process'].terminate()
                    self.log(f"Процесс для {appid} остановлен")
                except:
                    pass
                game['status'] = 'остановлен'
                break
        self.update_games_list()
        
    def remove_from_list(self):
        """Удаление игры из списка"""
        selected = self.games_tree.selection()
        if not selected:
            return
            
        item = self.games_tree.item(selected[0])
        appid = item['values'][0]
        
        self.active_games = [g for g in self.active_games if g['appid'] != appid]
        self.save_active_games()
        self.update_games_list()
        self.log(f"Игра {appid} удалена из списка")
        
    def show_context_menu(self, event):
        """Показ контекстного меню"""
        item = self.games_tree.identify_row(event.y)
        if item:
            self.games_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
            
    def update_games_list(self):
        """Обновление отображения списка игр"""
        for item in self.games_tree.get_children():
            self.games_tree.delete(item)
            
        for game in self.active_games:
            self.games_tree.insert('', tk.END, values=(
                game['appid'],
                game['name'],
                game['status'],
                game['time']
            ))
            
    def save_active_games(self):
        """Сохранение списка игр"""
        save_data = []
        for game in self.active_games:
            save_data.append({
                'appid': game['appid'],
                'name': game['name'],
                'status': game['status'],
                'time': game['time']
            })
            
        with open(self.games_file, 'w') as f:
            json.dump(save_data, f)
            
    def load_active_games(self):
        """Загрузка списка игр"""
        if self.games_file.exists():
            try:
                with open(self.games_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []
        
    def start_steam(self):
        """Запуск Steam"""
        try:
            if sys.platform == "win32":
                steam_paths = [
                    "C:\\Program Files (x86)\\Steam\\steam.exe",
                    "C:\\Program Files\\Steam\\steam.exe"
                ]
                for path in steam_paths:
                    if os.path.exists(path):
                        subprocess.Popen([path])
                        self.log("Steam запущен")
                        return
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-a", "Steam"])
            elif sys.platform == "linux":
                subprocess.Popen(["steam"])
        except Exception as e:
            self.log(f"Не удалось запустить Steam: {e}", "ERROR")
            
if __name__ == "__main__":
    root = tk.Tk()
    app = SteamToolsGUI(root)
    root.mainloop()