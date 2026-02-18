import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import subprocess
import os
import json
import time
import requests
import re
from pathlib import Path
import sys
import psutil  # для надёжного поиска процессов

class SteamToolsPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Steam Tools Pro [RAGE]")
        self.root.geometry("950x650")
        
        # Стиль
        style = ttk.Style()
        style.theme_use('clam')
        
        # Основной фрейм
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ---- Верхняя панель с URL ----
        url_frame = ttk.LabelFrame(main_frame, text="Добавить игру / Активировать ключ", padding="10")
        url_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(url_frame, text="Ссылка на игру или AppID:").grid(row=0, column=0, sticky=tk.W)
        self.url_entry = ttk.Entry(url_frame, width=70)
        self.url_entry.grid(row=0, column=1, padx=5, sticky=tk.W+tk.E)
        
        # Кнопки действий
        btn_frame = ttk.Frame(url_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        self.add_btn = ttk.Button(btn_frame, text="➕ Добавить игру", command=self.thread_add_game)
        self.add_btn.pack(side=tk.LEFT, padx=2)
        
        self.activate_btn = ttk.Button(btn_frame, text="🔑 Активировать ключ", command=self.thread_activate_key)
        self.activate_btn.pack(side=tk.LEFT, padx=2)
        
        self.farm_btn = ttk.Button(btn_frame, text="⏱ Фарм часов", command=self.thread_farm_hours)
        self.farm_btn.pack(side=tk.LEFT, padx=2)
        
        self.cards_btn = ttk.Button(btn_frame, text="🎴 Дроп карт", command=self.thread_drop_cards)
        self.cards_btn.pack(side=tk.LEFT, padx=2)
        
        # Панель статуса Steam
        status_frame = ttk.LabelFrame(main_frame, text="Статус Steam", padding="5")
        status_frame.pack(fill=tk.X, pady=5)
        
        self.steam_status = ttk.Label(status_frame, text="🔍 Проверка...")
        self.steam_status.pack(side=tk.LEFT)
        
        ttk.Button(status_frame, text="🔄 Обновить", command=self.check_steam).pack(side=tk.RIGHT)
        
        # ---- Таблица игр ----
        games_frame = ttk.LabelFrame(main_frame, text="Активные игры", padding="10")
        games_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        columns = ('appid', 'name', 'status', 'time', 'action')
        self.games_tree = ttk.Treeview(games_frame, columns=columns, show='headings', height=10)
        self.games_tree.heading('appid', text='AppID')
        self.games_tree.heading('name', text='Название')
        self.games_tree.heading('status', text='Статус')
        self.games_tree.heading('time', text='Наиграно')
        self.games_tree.heading('action', text='Действие')
        
        self.games_tree.column('appid', width=80)
        self.games_tree.column('name', width=250)
        self.games_tree.column('status', width=120)
        self.games_tree.column('time', width=80)
        self.games_tree.column('action', width=100)
        
        scrollbar = ttk.Scrollbar(games_frame, orient=tk.VERTICAL, command=self.games_tree.yview)
        self.games_tree.configure(yscrollcommand=scrollbar.set)
        
        self.games_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Контекстное меню
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Остановить", command=self.stop_game)
        self.context_menu.add_command(label="Удалить", command=self.remove_game)
        self.games_tree.bind("<Button-3>", self.show_context_menu)
        
        # Лог
        log_frame = ttk.LabelFrame(main_frame, text="Лог", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, height=8, state='normal')
        self.log_area.pack(fill=tk.BOTH, expand=True)
        
        # Конфиг
        self.config_dir = Path.home() / ".steam_tools_pro"
        self.config_dir.mkdir(exist_ok=True)
        self.games_file = self.config_dir / "games.json"
        
        self.active_games = self.load_games()
        self.running_processes = {}  # appid -> process
        
        self.check_steam()
        self.update_games_list()
        self.log("Steam Tools Pro запущен. Режим: unrestricted")
        
    # ========== Логи ==========
    def log(self, msg, level="INFO"):
        timestamp = time.strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] [{level}] {msg}\n")
        self.log_area.see(tk.END)
        self.root.update()
        
    # ========== Проверка Steam ==========
    def check_steam(self):
        """Ищет процесс Steam с помощью psutil (кросс-платформенно)"""
        try:
            for proc in psutil.process_iter(['name', 'exe', 'pid']):
                name = proc.info['name'] or ''
                if 'steam' in name.lower():
                    self.steam_status.config(text="✅ Steam запущен", foreground="green")
                    return True
            self.steam_status.config(text="❌ Steam не запущен", foreground="red")
            return False
        except Exception as e:
            self.log(f"Ошибка проверки Steam: {e}", "ERROR")
            self.steam_status.config(text="❌ Ошибка проверки", foreground="orange")
            return False
            
    # ========== Распознавание AppID ==========
    def extract_appid(self, text):
        """Извлекает AppID из ссылки или текста. Поддерживает:
        - store.steampowered.com/app/730
        - steamcommunity.com/app/730
        - steamdb.info/app/730
        - ru.store.steampowered.com/app/730
        - просто число 730
        - /app/730/ или ?appid=730
        """
        text = text.strip()
        
        # Прямое число
        if text.isdigit():
            return text
            
        # Поиск паттерна /app/ЧИСЛО
        match = re.search(r'/app/(\d+)', text)
        if match:
            return match.group(1)
            
        # Поиск appid=ЧИСЛО
        match = re.search(r'[?&]appid=(\d+)', text)
        if match:
            return match.group(1)
            
        # Поиск любого числа, если строка похожа на URL (содержит точки и слэши)
        if '.' in text and '/' in text:
            numbers = re.findall(r'\b\d{2,6}\b', text)  # числа от 2 до 6 цифр
            if numbers:
                # берём первое, часто это и есть appid
                return numbers[0]
                
        return None
        
    # ========== Получение названия игры ==========
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
        
    # ========== Добавление игры ==========
    def thread_add_game(self):
        threading.Thread(target=self.add_game, daemon=True).start()
        
    def add_game(self):
        input_text = self.url_entry.get()
        appid = self.extract_appid(input_text)
        
        if not appid:
            self.log("Не удалось распознать AppID. Пример ссылки: https://store.steampowered.com/app/730/", "ERROR")
            messagebox.showerror("Ошибка", "Не удалось распознать AppID")
            return
            
        # Проверяем, не запущен ли Steam
        if not self.check_steam():
            if not messagebox.askyesno("Steam не запущен", "Запустить Steam сейчас?"):
                return
            self.start_steam()
            time.sleep(5)
            
        name = self.get_game_name(appid)
        
        # Проверка на дубликат
        for g in self.active_games:
            if g['appid'] == appid:
                self.log(f"Игра {name} уже в списке", "WARNING")
                return
                
        self.active_games.append({
            'appid': appid,
            'name': name,
            'status': 'ожидание',
            'time': '0h'
        })
        self.save_games()
        self.update_games_list()
        self.log(f"✓ Игра {name} (AppID: {appid}) добавлена")
        
    # ========== Активация ключа (заглушка) ==========
    def thread_activate_key(self):
        threading.Thread(target=self.activate_key, daemon=True).start()
        
    def activate_key(self):
        key = self.url_entry.get().strip()
        if not key:
            self.log("Введите ключ в поле ввода", "ERROR")
            return
        self.log(f"Попытка активации ключа {key}...")
        # Здесь реальная активация через steampy или selenium
        self.log("Функция активации временно отключена (требуется библиотека steampy)")
        
    # ========== Фарм часов ==========
    def thread_farm_hours(self):
        selected = self.games_tree.selection()
        if not selected:
            messagebox.showwarning("Выбор игры", "Выберите игру в списке")
            return
        item = self.games_tree.item(selected[0])
        appid = item['values'][0]
        threading.Thread(target=self.farm_hours, args=(appid,), daemon=True).start()
        
    def farm_hours(self, appid):
        # Находим игру
        game = None
        for g in self.active_games:
            if g['appid'] == appid:
                game = g
                break
        if not game:
            return
            
        game['status'] = 'фарм часов'
        self.update_games_list()
        self.log(f"Запуск фарма часов для {game['name']} (AppID: {appid})")
        
        try:
            # Запускаем через steam://rungameid/
            if sys.platform == "win32":
                subprocess.Popen(f"steam://rungameid/{appid}", shell=True)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", f"steam://rungameid/{appid}"])
            else:
                subprocess.Popen(["xdg-open", f"steam://rungameid/{appid}"])
                
            # Для учёта времени создаём фейковый процесс
            if sys.platform == "win32":
                proc = subprocess.Popen(["cmd.exe", "/c", "timeout", "/t", "99999"], 
                                      creationflags=subprocess.CREATE_NO_WINDOW)
                self.running_processes[appid] = proc
                
            # Обновляем время
            start = time.time()
            while appid in self.running_processes:
                time.sleep(60)
                hours = round((time.time() - start) / 3600, 1)
                game['time'] = f"{hours}h"
                self.update_games_list()
                
        except Exception as e:
            self.log(f"Ошибка фарма: {e}", "ERROR")
            game['status'] = 'ошибка'
            self.update_games_list()
            
    # ========== Дроп карт (аналогично фарму) ==========
    def thread_drop_cards(self):
        selected = self.games_tree.selection()
        if not selected:
            messagebox.showwarning("Выбор игры", "Выберите игру в списке")
            return
        item = self.games_tree.item(selected[0])
        appid = item['values'][0]
        threading.Thread(target=self.drop_cards, args=(appid,), daemon=True).start()
        
    def drop_cards(self, appid):
        # Для дропа карт нужен именно запуск игры, поэтому используем тот же фарм
        self.farm_hours(appid)
        
    # ========== Управление процессами ==========
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
        
        # Останавливаем процесс, если запущен
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
            
    # ========== Обновление таблицы ==========
    def update_games_list(self):
        for row in self.games_tree.get_children():
            self.games_tree.delete(row)
        for g in self.active_games:
            status = g['status']
            # Определяем действие в зависимости от статуса
            if status == 'фарм часов':
                action = '⏸ Стоп'
            else:
                action = '▶ Фарм'
            self.games_tree.insert('', tk.END, values=(
                g['appid'], g['name'], status, g['time'], action
            ))
            
    # ========== Сохранение/загрузка ==========
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
        
    # ========== Запуск Steam ==========
    def start_steam(self):
        try:
            if sys.platform == "win32":
                # Поиск steam.exe в стандартных местах
                paths = [
                    os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)") + "\\Steam\\steam.exe",
                    os.environ.get("ProgramFiles", "C:\\Program Files") + "\\Steam\\steam.exe",
                ]
                for path in paths:
                    if os.path.exists(path):
                        subprocess.Popen([path])
                        self.log("Steam запущен")
                        return
                self.log("Steam не найден, запустите вручную", "ERROR")
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-a", "Steam"])
            else:
                subprocess.Popen(["steam"])
        except Exception as e:
            self.log(f"Не удалось запустить Steam: {e}", "ERROR")

if __name__ == "__main__":
    # Убедимся, что psutil установлен
    try:
        import psutil
    except ImportError:
        print("Установите psutil: pip install psutil")
        sys.exit(1)
        
    root = tk.Tk()
    app = SteamToolsPro(root)
    root.mainloop()
