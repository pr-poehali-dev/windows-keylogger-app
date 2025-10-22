import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import csv
from datetime import datetime
from pynput import keyboard
import threading
import os


class KeyboardLoggerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Keyboard Logger")
        self.root.geometry("900x700")
        self.root.configure(bg="#2c3e50")
        
        self.is_recording = False
        self.current_session = None
        self.sessions = []
        self.key_stats = {}
        self.session_keys = []
        self.listener = None
        self.session_time = 0
        self.timer_thread = None
        self.stop_timer = False
        
        self.setup_ui()
        self.load_sessions()
        
    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Dark.TFrame', background='#34495e')
        style.configure('Card.TFrame', background='#2c3e50', relief='raised', borderwidth=2)
        style.configure('Title.TLabel', background='#2c3e50', foreground='#ecf0f1', 
                       font=('Montserrat', 24, 'bold'))
        style.configure('Subtitle.TLabel', background='#2c3e50', foreground='#95a5a6', 
                       font=('Open Sans', 10))
        style.configure('Timer.TLabel', background='#34495e', foreground='#3498db', 
                       font=('Consolas', 32, 'bold'))
        style.configure('Status.TLabel', background='#34495e', foreground='#ecf0f1', 
                       font=('Open Sans', 14, 'bold'))
        
        main_frame = ttk.Frame(self.root, style='Dark.TFrame', padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        header_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(header_frame, text="⌨️ Keyboard Logger", style='Title.TLabel')
        title_label.pack(anchor=tk.W)
        
        subtitle_label = ttk.Label(header_frame, text="Отслеживайте активность клавиатуры", 
                                   style='Subtitle.TLabel')
        subtitle_label.pack(anchor=tk.W)
        
        control_frame = ttk.Frame(main_frame, style='Card.TFrame', padding="20")
        control_frame.pack(fill=tk.X, pady=(0, 20))
        
        status_frame = ttk.Frame(control_frame, style='Card.TFrame')
        status_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.status_label = ttk.Label(status_frame, text="Готов к записи", style='Status.TLabel')
        self.status_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.status_desc = ttk.Label(status_frame, text="Нажмите кнопку для начала", 
                                     style='Subtitle.TLabel')
        self.status_desc.pack(anchor=tk.W)
        
        self.timer_label = ttk.Label(status_frame, text="00:00:00", style='Timer.TLabel')
        
        button_frame = ttk.Frame(control_frame, style='Card.TFrame')
        button_frame.pack(side=tk.RIGHT, padx=20)
        
        self.start_button = tk.Button(button_frame, text="▶ Начать запись", 
                                      command=self.toggle_recording,
                                      bg="#3498db", fg="white", font=('Open Sans', 12, 'bold'),
                                      padx=20, pady=10, relief=tk.FLAT, cursor="hand2")
        self.start_button.pack()
        
        content_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        stats_frame = ttk.Frame(content_frame, style='Card.TFrame', padding="15")
        stats_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        stats_header = ttk.Label(stats_frame, text="📊 Статистика клавиш", 
                                style='Status.TLabel', font=('Open Sans', 14, 'bold'))
        stats_header.pack(anchor=tk.W, pady=(0, 10))
        
        self.stats_text = tk.Text(stats_frame, bg="#34495e", fg="#ecf0f1", 
                                 font=('Consolas', 10), relief=tk.FLAT, height=20)
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
        history_frame = ttk.Frame(content_frame, style='Card.TFrame', padding="15")
        history_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        history_header_frame = ttk.Frame(history_frame, style='Card.TFrame')
        history_header_frame.pack(fill=tk.X, pady=(0, 10))
        
        history_label = ttk.Label(history_header_frame, text="📜 История сессий", 
                                 style='Status.TLabel', font=('Open Sans', 14, 'bold'))
        history_label.pack(side=tk.LEFT)
        
        export_button = tk.Button(history_header_frame, text="💾 CSV", 
                                 command=self.export_csv,
                                 bg="#27ae60", fg="white", font=('Open Sans', 9, 'bold'),
                                 padx=10, pady=5, relief=tk.FLAT, cursor="hand2")
        export_button.pack(side=tk.RIGHT, padx=5)
        
        self.history_listbox = tk.Listbox(history_frame, bg="#34495e", fg="#ecf0f1", 
                                         font=('Open Sans', 9), relief=tk.FLAT,
                                         selectbackground="#3498db")
        self.history_listbox.pack(fill=tk.BOTH, expand=True)
        
        self.update_stats_display()
        self.update_history_display()
    
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        self.is_recording = True
        self.current_session = {
            'id': str(int(datetime.now().timestamp())),
            'start_time': datetime.now().isoformat(),
            'keys': []
        }
        self.session_keys = []
        self.session_time = 0
        
        self.status_label.config(text="🔴 Запись активна")
        self.status_desc.config(text="Все нажатия регистрируются")
        self.start_button.config(text="■ Остановить", bg="#e74c3c")
        self.timer_label.pack(pady=(10, 0))
        
        self.stop_timer = False
        self.timer_thread = threading.Thread(target=self.update_timer, daemon=True)
        self.timer_thread.start()
        
        self.listener = keyboard.Listener(on_press=self.on_key_press)
        self.listener.start()
    
    def stop_recording(self):
        self.is_recording = False
        self.stop_timer = True
        
        if self.listener:
            self.listener.stop()
        
        if self.current_session:
            self.current_session['end_time'] = datetime.now().isoformat()
            self.current_session['duration'] = self.session_time
            self.current_session['key_count'] = len(self.session_keys)
            self.current_session['keys'] = self.session_keys
            
            self.sessions.insert(0, self.current_session)
            self.save_sessions()
            self.update_history_display()
            
            for key in self.session_keys:
                self.key_stats[key] = self.key_stats.get(key, 0) + 1
            self.update_stats_display()
        
        self.status_label.config(text="✅ Готов к записи")
        self.status_desc.config(text="Нажмите кнопку для начала")
        self.start_button.config(text="▶ Начать запись", bg="#3498db")
        self.timer_label.pack_forget()
    
    def on_key_press(self, key):
        if not self.is_recording:
            return
        
        try:
            key_name = key.char if hasattr(key, 'char') and key.char else str(key).replace('Key.', '')
        except:
            key_name = str(key).replace('Key.', '')
        
        self.session_keys.append(key_name)
    
    def update_timer(self):
        while not self.stop_timer:
            self.session_time += 1
            hours = self.session_time // 3600
            minutes = (self.session_time % 3600) // 60
            seconds = self.session_time % 60
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.timer_label.config(text=time_str)
            threading.Event().wait(1)
    
    def update_stats_display(self):
        self.stats_text.delete(1.0, tk.END)
        
        if not self.key_stats:
            self.stats_text.insert(tk.END, "Нет данных\n\nНачните запись для сбора статистики")
            return
        
        sorted_stats = sorted(self.key_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        max_count = sorted_stats[0][1] if sorted_stats else 1
        
        for idx, (key, count) in enumerate(sorted_stats, 1):
            bar_length = int((count / max_count) * 20)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            self.stats_text.insert(tk.END, f"#{idx:2d} [{key:10s}] {bar} {count:4d}\n")
    
    def update_history_display(self):
        self.history_listbox.delete(0, tk.END)
        
        if not self.sessions:
            self.history_listbox.insert(tk.END, "Нет записанных сессий")
            return
        
        for session in self.sessions:
            start_dt = datetime.fromisoformat(session['start_time'])
            duration = session.get('duration', 0)
            key_count = session.get('key_count', 0)
            
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            seconds = duration % 60
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            entry = f"{start_dt.strftime('%d.%m.%Y %H:%M')} | {time_str} | {key_count} клавиш"
            self.history_listbox.insert(tk.END, entry)
    
    def export_csv(self):
        if not self.sessions:
            messagebox.showwarning("Нет данных", "Создайте хотя бы одну сессию для экспорта")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"keyboard-logger-{datetime.now().strftime('%Y-%m-%d')}.csv"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['ID', 'Начало', 'Окончание', 'Длительность (сек)', 'Количество клавиш'])
                
                for session in self.sessions:
                    writer.writerow([
                        session['id'],
                        session['start_time'],
                        session.get('end_time', 'В процессе'),
                        session.get('duration', 0),
                        session.get('key_count', 0)
                    ])
            
            messagebox.showinfo("Экспорт завершен", f"CSV файл сохранен:\n{filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{str(e)}")
    
    def save_sessions(self):
        try:
            with open('sessions.json', 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving sessions: {e}")
    
    def load_sessions(self):
        try:
            if os.path.exists('sessions.json'):
                with open('sessions.json', 'r', encoding='utf-8') as f:
                    self.sessions = json.load(f)
                
                for session in self.sessions:
                    for key in session.get('keys', []):
                        self.key_stats[key] = self.key_stats.get(key, 0) + 1
                
                self.update_stats_display()
                self.update_history_display()
        except Exception as e:
            print(f"Error loading sessions: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = KeyboardLoggerApp(root)
    root.mainloop()
