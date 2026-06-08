import tkinter as tk
from tkinter import messagebox, ttk, simpledialog, font
import os
import time
# Импортируем функции шифрования из crypto_core.py
from crypto_core import encrypt_data, decrypt_data, save_lock_time, get_lock_time, save_failed_attempts, get_failed_attempts
# Импортируем функции "общения с облаком" из cloud_service.py
from cloud_service import upload_to_cloud, download_from_cloud


class LoginWindow:
    def __init__(self, root, force_create=False, hide_cloud=False, target_file=None, show_back_button=False):
        self.target_file = target_file  # Сохраняем целевой файл, если он передан (для кнопки "Войти в аккаунт")

        # --- ЛОГИКА ЗАЩИТЫ ОТ ПЕРЕБОРА ---
        self.failed_attempts = get_failed_attempts()
        self.lock_timer_id = None
        self.lock_remaining_time = 0 # Оставшееся время блокировки в секундах

        # Проверяем, не была ли программа закрыта в момент блокировки
        lock_until = get_lock_time()
        current_time = time.time()
        
        if lock_until > current_time:
            # Вычисляем, сколько секунд блокировки ОСТАЛОСЬ отбыть
            self.lock_remaining_time = int(lock_until - current_time)
        # ---------------------------------

        self.root = root
        self.root.title("CryptoVault — Вход") 
        self.root.geometry("400x335")

        self.root.resizable(False, False)
        self.center_window()

        # Если блокировка активна, «на лету» замораживаем интерфейс при старте
        if self.lock_remaining_time > 0:
            self.root.after(10, self.lock_interface_on_start)
        
        # --- УМНАЯ ПРОВЕРКА НА ПЕРВЫЙ ЗАПУСК ---
        # Ищем вообще все файлы с расширением .dat в папке приложения
        self.dat_files = [f for f in os.listdir(".") if f.endswith(".dat")]
        if force_create:
            self.is_first_run = True
        else:
            self.is_first_run = len(self.dat_files) == 0
        

        # --- КНОПКА НАЗАД (ОТ СЛУЧАЙНОГО ТЫКА) ---
        if show_back_button:
            # Создаем фрейм для верхней панели
            top_frame = tk.Frame(root)
            
            
            self.btn_back = tk.Button(
                top_frame, 
                text="⬅ Назад", 
                font=("Arial", 9), 
                bd=0, 
                relief="flat", 
                cursor="hand2",
                activebackground=root.cget("bg"),
                bg=root.cget("bg"),
                fg="#3498db",
                command=self.go_back_to_login
            )
            self.btn_back.pack(side="left")


        self.label_title = tk.Label(root, text="Добро пожаловать в CryptoVault", font=("WDXL Lubrifont JP N", 20))
        self.label_title.pack(pady=10)

        if self.is_first_run: 
            hide_cloud=True
            self.root.geometry("400x365")
            tk.Label(root, text="Придумайте имя для вашего сейфа:", font=("WDXL Lubrifont JP N", 14)).pack(pady=(5, 2))
            
            # Фрейм-контейнер для выравнивания по центру
            name_frame = tk.Frame(root)
            name_frame.pack(pady=2)
            
            self.entry_vault_name = tk.Entry(name_frame, width=30, font=("Arial", 12))
            self.entry_vault_name.grid(row=0, column=0, padx=(24, 21)) # Смещаем так же, как и пароль
            self.entry_vault_name.insert(0, "my_vault") # Дефолтная подсказка внутри поля
            
            # заглушка справа, чтобы поле имени стояло ровно по центру над полем пароля (которое с глазом)
            tk.Label(name_frame, text="  ").grid(row=0, column=1) 
            

        # Меняем надпись в зависимости от режима, чтобы не путать пользователя
        hint_text = "Придумайте Мастер-пароль:" if self.is_first_run else "Введите Мастер-пароль:"
        self.label_hint = tk.Label(root, text=hint_text, font=("WDXL Lubrifont JP N", 14))
        self.label_hint.pack(pady=2)

        
        # 1. Создаем контейнер и размещаем его по центру главного окна 
        pass_frame = tk.Frame(root)
        pass_frame.pack(pady=5)

        # 2. Поле ввода кладем в нулевую ячейку сетки фрейма с отступом для компенсации "глаза"
        self.entry_password = tk.Entry(pass_frame, show="*", width=30, font=("Arial", 12))
        self.entry_password.grid(row=0, column=0, padx=(40, 5)) 

        # 3. Значок глаза кладем в первую ячейку (справа от поля)
        btn_eye = tk.Label(pass_frame, text="👁️", font=("Arial", 12), cursor="hand2")
        btn_eye.grid(row=0, column=1)

        # --- ЛОГИКА ДЛЯ КНОПКИ-ГЛАЗА ---
        def show_password(event):
            self.entry_password.config(show="")

        def hide_password(event):
            self.entry_password.config(show="*")

        btn_eye.bind("<ButtonPress-1>", show_password)
        btn_eye.bind("<ButtonRelease-1>", hide_password)

        self.entry_password.focus()

        # Текст кнопки зависит от глобального наличия сейфов в системе
        btn_text = "Создать новую базу" if self.is_first_run else "Войти в сейф"
        self.btn_submit = tk.Button(root, text=btn_text, width=20, bg="#3498db", fg="white", relief="ridge", font=("Arial", 10, "bold"), command=self.handle_auth)
        self.btn_submit.pack(pady=10)

        # --- БЛОК ВОССТАНОВЛЕНИЯ ИЗ ОБЛАКА ---
        if not hide_cloud: 
            self.separator = ttk.Separator(root, orient='horizontal')
            self.separator.pack(fill='x', padx=20, pady=10)

            self.label_cloud = tk.Label(root, text="Или восстановите существующий сейф из облака:", font=("Arial", 9, "italic"))
            self.label_cloud.pack(pady=2)

            self.cloud_frame = tk.Frame(root)
            self.cloud_frame.pack(pady=5)

            self.entry_link = tk.Entry(self.cloud_frame, width=40, font=("Arial", 10)) 
            self.entry_link.grid(row=0, column=0, padx=(10, 10)) 
            self.entry_link.insert(0, "Вставьте ссылку https://file.io/...")
            self.entry_link.bind("<Control-KeyPress>", lambda event: self.custom_paste(event))

            self.btn_download = tk.Button(root, text="Скачать и войти", width=20, bg="#9b59b6", fg="white", relief="ridge", font=("Arial", 10, "bold"), command=self.handle_cloud_recovery)
            self.btn_download.pack(pady=5)

            # --- ДОБАВЛЯЕМ КНОПКУ СОЗДАНИЯ НОВОГО СЕЙФА ---
            self.btn_create_new = tk.Button(
                root, 
                text="Создать новый сейф", 
                width=20, 
                bg="#1db709", 
                fg="white", 
                relief="ridge",
                font=("Arial", 10, "bold"), 
                command=self.restart_for_registration # Привязываем вызов создания аккаунта
            )
            self.btn_create_new.pack(pady=5)

            self.entry_link.bind("<Button-1>", lambda event: self.entry_link.delete(0, tk.END) if "Вставьте ссылку" in self.entry_link.get() else None)

        else: self.root.geometry("400x260")
        
 
        # --- ЛОГИКА БЛОКИРОВКИ КНОПКИ ЛОКАЛЬНОГО ВХОДА ---
        def toggle_submit_button(event=None):
            current_link = self.entry_link.get().strip()
            
            # Если в поле пусто или там дефолтная подсказка — локальная кнопка активна
            if not current_link or "Вставьте ссылку" in current_link:
                self.btn_submit.config(state="normal", bg="#3498db") # Возвращаем исходный синий цвет
            else:
                # Если пользователь ввёл что-то похожее на ссылку — блокируем кнопку локального входа и созданиия аккаунта
                self.btn_submit.config(state="disabled", bg="#7f8c8d") # Делаем её серой и неактивной
                self.btn_create_new.config(state="disabled", bg="#7f8c8d")

        # Привязываем отслеживание ввода текста (когда клавиша отпущена)
        if not hide_cloud:  
            self.entry_link.bind("<KeyRelease>", toggle_submit_button)
        
        # Очищать поле при клике мышкой
        if not hide_cloud:
            self.entry_link.bind("<Button-1>", lambda event: [
                self.entry_link.delete(0, tk.END) if "Вставьте ссылку" in self.entry_link.get() else None,
                toggle_submit_button() # Вызываем проверку сразу после клика
            ])

    def restart_for_registration(self):
        """Закрывает текущее окно входа и перезапускает LoginWindow в режиме регистрации."""
        # Закрываем текущее окно авторизации
        self.root.destroy()
        
        # Создаем новый чистый Tk-контекст
        new_login_root = tk.Tk()
        
        # Запускаем LoginWindow
        LoginWindow(new_login_root, force_create=True, hide_cloud=True, show_back_button=True)
        new_login_root.mainloop()
    
    def go_back_to_login(self):
        """Возвращает пользователя из режима регистрации обратно на экран авторизации."""
        self.root.destroy()
        
        normal_login_root = tk.Tk()
        # Запускаем в стандартном режиме
        LoginWindow(normal_login_root, force_create=False, hide_cloud=False)
        normal_login_root.mainloop()


    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def handle_auth(self): # Обработка авторизации в локальное хранилище
        global CURRENT_FILE
        password = self.entry_password.get().strip()
        if not password:
            messagebox.showwarning("Ошибка", "Введите пароль!")
            return

        # =====================================================================
        # ВЕТКА СОЗДАНИЯ НОВОЙ БАЗЫ (При первом запуске)
        # =====================================================================
        if self.is_first_run:
            # 1. Получаем и нормализуем имя сейфа
            vault_name_input = self.entry_vault_name.get().strip()
            if not vault_name_input:
                messagebox.showwarning("Ошибка", "Имя сейфа не может быть пустым!")
                return
            
            # Автоматически добавляем .dat, если пользователь его не написал
            if not vault_name_input.endswith(".dat"):
                vault_name_input += ".dat"
                
            # ПРОВЕРКА №1: Существует ли уже файл с таким именем?
            if os.path.exists(vault_name_input):
                messagebox.showerror("Ошибка", f"Аккаунт с именем '{vault_name_input}' уже существует!")
                return
            
            # #Защита от кириллицы
            try:
                # Пробуем перевести строку в байты ASCII. Если там кириллица, Python сразу выкинет UnicodeEncodeError
                password.encode('ascii') 
            except UnicodeEncodeError:
                messagebox.showerror("Ошибка", "Пароль должен содержать только латиницу, цифры и спецсимволы!")
                return # Прерываем регистрацию

            # Проверяем длину пароля
            if len(password) < 4:
                messagebox.showwarning("Ошибка", "Пароль должен быть не менее 4 символов!")
                return
                
            #  ПРОВЕРКА №2: Используется ли этот пароль в других сейфах?
            # Собираем актуальный список всех файлов .dat в папке
            existing_dat_files = [f for f in os.listdir(".") if f.endswith(".dat")]
            
            for existing_file in existing_dat_files:
                try:
                    # Пробуем расшифровать каждый существующий файл новым паролем
                    decrypt_data(password, existing_file)
                    
                    # Если ValueError НЕ вызвался, значит пароль подошел к какому-то старому файлу!
                    messagebox.showerror("Ошибка", "Аккаунт с таким паролем уже существует!")
                    return # Прерываем создание, так как пароль не уникален
                except ValueError:
                    # Пароль не подошел к этому файлу, идем проверять следующий
                    continue

            # Если обе проверки пройдены — создаем сейф
            CURRENT_FILE = vault_name_input
            empty_vault = {
                "vault_name": CURRENT_FILE, 
                "credentials": [], 
                "notes": []
            }
            
            encrypt_data(empty_vault, password, CURRENT_FILE)
            messagebox.showinfo("Успех", f"Новое хранилище '{CURRENT_FILE}' успешно создано!")
            self.is_first_run = False
            self.open_main_app(password) 
            
        # =====================================================================
        # ВЕТКА ОБЫЧНОЙ АВТОРИЗАЦИИ (Вход в существующий сейф)
        # =====================================================================
        else:
            # ТОЧЕЧНЫЙ ВХОД В ВЫБРАННЫЙ АККАУНТ (Если входим через внутренний интерфейс) 
            if self.target_file:
                try:
                    decrypt_data(password, self.target_file)
                    CURRENT_FILE = self.target_file
                    self.failed_attempts = 0 # Сбрасываем при успешном входе!
                    save_failed_attempts(0)
                    self.open_main_app(password)
                except ValueError:
                    # Увеличиваем счётчик неудачных попыток входа при провале
                    self.failed_attempts += 1
                    save_failed_attempts(self.failed_attempts) # ФИКСИРУЕМ НА ДИСК КАЖДЫЙ ПРОМАХ
                    
                    if self.failed_attempts >= 5:
                        messagebox.showerror("Защита от перебора", "Превышено количество попыток ввода! Вход заблокирован на 3 минуты.")
                        self.lock_interface()
                    else:
                        remains = 5 - self.failed_attempts
                        messagebox.showerror("Ошибка доступа", f"Неверный Мастер-пароль для аккаунта '{self.target_file}'!\nОсталось попыток: {remains}")
            
            # АВТОМАТИЧЕСКИЙ ПЕРЕБОР ВСЕХ СКРЫТЫХ ФАЙЛОВ (Если входим через окно авторизации)
            else:
                self.dat_files = [f for f in os.listdir(".") if f.endswith(".dat")]
                success_auth = False
                
                for dat_file in self.dat_files:
                    try:
                        decrypt_data(password, dat_file)
                        CURRENT_FILE = dat_file
                        success_auth = True
                        break
                    except ValueError:
                        continue
                
                if success_auth:
                    self.failed_attempts = 0 # Сбрасываем при успешном входе!
                    save_failed_attempts(0)
                    self.open_main_app(password)
                else:
                    # Пароль не подошел вообще ни к одной локальной базе!
                    self.failed_attempts += 1
                    save_failed_attempts(self.failed_attempts) # ЖЕСТКО ФИКСИРУЕМ НА ДИСК КАЖДЫЙ ПРОМАХ
                    
                    if self.failed_attempts >= 5:
                        messagebox.showerror("Защита от перебора", "Превышено количество попыток ввода! Вход заблокирован на 3 минуты.")
                        self.lock_interface()
                    else:
                        remains = 5 - self.failed_attempts
                        messagebox.showerror("Ошибка доступа", f"Неверный Мастер-пароль!\nНи один существующий сейф не подошел.\nОсталось попыток: {remains}")

    def handle_cloud_recovery(self): #Авторизация с облака
        global CURRENT_FILE
        password = self.entry_password.get()
        url = self.entry_link.get().strip()

        if not password:
            messagebox.showwarning("Ошибка", "Сначала введите Мастер-пароль под которым был бэкап!")
            return
        if not url or "https://" not in url:
            messagebox.showwarning("Ошибка", "Введите корректную HTTPS-ссылку!")
            return

        messagebox.showinfo("Синхронизация", "Скачиваем резервную копию из облака...")
        
        temp_file = "temp_download.dat"
        success = download_from_cloud(url, temp_file)
        
        if success:
            try:
                # Шаг 1: Расшифровываем временный файл текущим паролем
                decrypted_vault = decrypt_data(password, temp_file)
                original_name = decrypted_vault.get("vault_name", "restored_passwords.dat")
                
                # Собираем список всех локальных .dat файлов
                local_files = [f for f in os.listdir(".") if f.endswith(".dat") and f != temp_file]
                
                # Флаги детекции конфликтов
                name_conflicts = os.path.exists(original_name)
                password_conflicts = False
                
                for local_file in local_files:
                    try:
                        decrypt_data(password, local_file)
                        password_conflicts = True # Пароль подошел к какому-то локальному файлу
                        break
                    except ValueError:
                        continue

                final_name = original_name
                final_password = password

                # =====================================================================
                # СЦЕНАРИЙ №1: Совпадают И ИМЯ, И ПАРОЛЬ
                # =====================================================================
                if name_conflicts and password_conflicts:
                    msg = f"Критический конфликт! Сейф '{original_name}' и его пароль уже существуют локально."
    
                    # Передаем local_files и функцию дешифрования
                    dialog = DoubleInputDialog(self.root, "Критический конфликт", msg, local_files=local_files, decrypt_func=decrypt_data)
    
                    if dialog.result is None: # Нажал "Отмена" или закрыл крестиком
                        if os.path.exists(temp_file): os.remove(temp_file)
                        return
        
                    # Сюда мы гарантированно доберемся ТОЛЬКО с уникальным именем и уникальным паролем
                    final_name, final_password = dialog.result

                # =====================================================================
                # СЦЕНАРИЙ №2: Совпадает ТОЛЬКО ПАРОЛЬ (Имя уникально)
                # =====================================================================
                elif password_conflicts and not name_conflicts:
                    messagebox.showinfo("Конфликт паролей", "Пароль от этого облачного сейфа уже используется в другом локальном аккаунте.\n\nПожалуйста, задайте НОВЫЙ уникальный пароль.")
                    
                    while True:
                        new_pass = simpledialog.askstring("Новый пароль", "Введите новый Мастер-пароль (не менее 4 символов):", show="*", parent=self.root)
                        if new_pass is None: # Отмена
                            if os.path.exists(temp_file): os.remove(temp_file)
                            return
                        
                        new_pass = new_pass.strip()
                        if len(new_pass) < 4:
                            messagebox.showwarning("Ошибка", "Пароль слишком короткий!", parent=self.root)
                            continue
                            
                        # Проверяем уникальность нового пароля
                        conflict_again = False
                        for local_file in local_files:
                            try:
                                decrypt_data(new_pass, local_file)
                                conflict_again = True
                                break
                            except ValueError:
                                continue
                        
                        if conflict_again:
                            messagebox.showerror("Ошибка", "Этот пароль тоже занят! Придумайте другой.", parent=self.root)
                            continue
                            
                        final_password = new_pass
                        break

                # =====================================================================
                # СЦЕНАРИЙ №3: Совпадает ТОЛЬКО ИМЯ (Пароль уникален)
                # =====================================================================
                elif name_conflicts and not password_conflicts:
                    messagebox.showinfo("Конфликт имён", f"Сейф с именем '{original_name}' уже существует локально.\n\nПожалуйста, придумайте уникальное имя для скачиваемого аккаунта.")
                    
                    while True:
                        new_name = simpledialog.askstring("Новое имя", "Введите новое имя сейфа:", parent=self.root)
                        if new_name is None: # Отмена
                            if os.path.exists(temp_file): os.remove(temp_file)
                            return
                        
                        new_name = new_name.strip()
                        if not new_name:
                            messagebox.showwarning("Ошибка", "Имя не может быть пустым!", parent=self.root)
                            continue
                        
                        if not new_name.endswith(".dat"): 
                            new_name += ".dat"
                            
                        if os.path.exists(new_name):
                            messagebox.showerror("Ошибка", f"Сейф с именем '{new_name}' тоже уже существует!", parent=self.root)
                            continue
                            
                        final_name = new_name
                        break

                # ЗАВЕРШЕНИЕ ОПЕРАЦИИ (Применяем изменения)
                # Обновляем имя внутри JSON-структуры
                decrypted_vault["vault_name"] = final_name
                
                # Перезашифровываем временный файл под утвержденными финальными данными
                encrypt_data(decrypted_vault, final_password, temp_file)

                # Переносим из временного файла в постоянный
                if os.path.exists(final_name):
                    os.remove(final_name)
                os.rename(temp_file, final_name)
                
                CURRENT_FILE = final_name
                messagebox.showinfo("Успех", f"Сейф успешно интегрирован как '{final_name}'!")
                self.open_main_app(final_password)
                
            except ValueError:
                if os.path.exists(temp_file): os.remove(temp_file)
                messagebox.showerror("Ошибка доступа", "Неверный Мастер-пароль к зашифрованному файлу из облака!")
            except Exception as e:
                if os.path.exists(temp_file): os.remove(temp_file)
                messagebox.showerror("Ошибка", f"Произошла ошибка при обработке файла: {e}")
        else:
            messagebox.showerror("Ошибка сети", "Не удалось скачать файл. Проверьте ссылку или соединение.")
            

    def open_main_app(self, master_password):
        self.root.destroy()
        main_root = tk.Tk()
        AppMainWindow(main_root, master_password)
        main_root.mainloop()
    
    def custom_paste(self, event): # Чтобы вставка по комбинации клавишь работала с любой раскладкой.
        if event.keysym.lower() == 'v' or event.char.lower() in ['v', 'м']:
            try:
                text = self.root.clipboard_get()
                if "Вставьте ссылку" in self.entry_link.get():
                    self.entry_link.delete(0, tk.END)
                self.entry_link.insert(tk.INSERT, text)
                # Если вставили ссылку через Ctrl+V, сразу проверяем и блокируем синюю кнопку
                current_link = self.entry_link.get().strip()
                if current_link and "Вставьте ссылку" not in current_link:
                    self.btn_submit.config(state="disabled", bg="#7f8c8d")
                # ------------------------------
            except tk.TclError:
                pass
            return "break"
        
    
    #==========БЛОК ЗАЩИТЫ ОТ ПЕРЕБОРА ПАРОЛЯ======================
    def lock_interface(self):
        """Включает блокировку на 3 минуты и фиксирует время на диске."""
        self.lock_remaining_time = 180
        
        # Высчитываем точную секунду в будущем, до которой вход закрыт
        lock_until_timestamp = time.time() + self.lock_remaining_time
        save_lock_time(lock_until_timestamp) # Запомнили в config.json
        
        self.entry_password.config(state="disabled")
        self.entry_link.config(state="disabled") # ДОБАВЛЕНО!!!
        self.btn_submit.config(state="disabled", bg="#7f8c8d")
        self.btn_create_new.config(state="disabled", bg="#7f8c8d") # ДОБАВЛЕНО!!!
        if hasattr(self, 'btn_download'): self.btn_download.config(state="disabled")
        self.update_lock_timer()

    def lock_interface_on_start(self):
        """Блокирует интерфейс при старте (БЕЗ перезаписи config.json)."""
        self.entry_password.config(state="disabled")
        self.entry_link.config(state="disabled") # ДОБАВЛЕНО!!!
        self.btn_submit.config(state="disabled", bg="#7f8c8d")
        self.btn_create_new.config(state="disabled", bg="#7f8c8d") # ДОБАВЛЕНО!!!
        if hasattr(self, 'btn_download'): self.btn_download.config(state="disabled")
        
        self.update_lock_timer()

    def update_lock_timer(self):
        """Ежесекундно обновляет тикающий текст на кнопке."""
        if self.lock_remaining_time > 0:
            minutes = self.lock_remaining_time // 60
            seconds = self.lock_remaining_time % 60
            time_str = f"{minutes:02d}:{seconds:02d}"
            
            self.btn_submit.config(text=f"Блокировка ({time_str})")
            
            self.lock_remaining_time -= 1
            self.lock_timer_id = self.root.after(1000, self.update_lock_timer)
        else:
            # Время вышло! Очищаем файл конфигурации
            self.failed_attempts = 0
            save_failed_attempts(0)
            self.lock_timer_id = None 
            save_lock_time(0) # Записываем 0, блокировка снята
            
            self.entry_password.config(state="normal")
            self.entry_link.config(state="normal") # ДОБАВЛЕНО!!!
            btn_text = "Создать новую базу" if self.is_first_run else "Войти в сейф"
            self.btn_submit.config(state="normal", text=btn_text, bg="#3498db")
            self.btn_create_new.config(state="normal", bg="#176407") # ДОБАВЛЕНО!!!

            if hasattr(self, 'btn_download'): self.btn_download.config(state="normal")
            
            messagebox.showinfo("Защита", "Доступ разблокирован. Вы можете снова ввести пароль.")

class AppMainWindow:
    def __init__(self, root, master_password):
        self.root = root
        self.timer_id = None
        self.root.title("CryptoVault — Ваше защищенное хранилище")
        self.root.geometry("750x450")
        self.root.minsize(700, 400)
        self.master_password = master_password
        
        # Загружаем реальные данные из зашифрованного файла
        self.vault_data = decrypt_data(master_password, CURRENT_FILE)

        # Разметка сетки окна
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # --- ЛЕВАЯ ПАНЕЛЬ МЕНЮ ---
        self.menu_frame = tk.Frame(root, bg="#2c3e50", width=180)
        self.menu_frame.grid(row=0, column=0, sticky="nsew")
        self.menu_frame.grid_propagate(False)

        self.logo_label = tk.Label(self.menu_frame, text="CryptoVault", font=("WDXL Lubrifont JP N", 23,), fg="white", bg="#2c3e50")
        self.logo_label.pack(pady=20)

        self.btn_passwords = tk.Button(self.menu_frame, text="          🗝 Пароли          ", font=("Arial", 11), bg="#34495e", fg="white", relief="flat", command=self.show_passwords_page)
        self.btn_passwords.pack(fill="x", padx=10, pady=5)

        self.btn_notes = tk.Button(self.menu_frame, text="📝 Заметки", font=("Arial", 11), bg="#34495e", fg="white", relief="flat", command=self.show_notes_page)
        self.btn_notes.pack(fill="x", padx=10, pady=5)

        self.btn_sync = tk.Button(self.menu_frame, text="☁ В облако", font=("Arial", 11), bg="#34495e", fg="white", relief="flat", command=self.sync_with_cloud)
        self.btn_sync.pack(fill="x", padx=10, pady=5)

        # ---КНОПКА АККАУНТЫ ---
        self.btn_accounts = tk.Button(self.menu_frame, text="👤 Аккаунты", font=("Arial", 11), bg="#34495e", fg="white", relief="flat", command=self.toggle_accounts_panel)
        self.btn_accounts.pack(fill="x", padx=10, pady=5)
        
        # Переменная для хранения всплывающей панели
        self.accounts_frame = None

        self.spacer = tk.Label(self.menu_frame, bg="#2c3e50")
        self.spacer.pack(expand=True, fill="both")

        self.btn_logout = tk.Button(self.menu_frame, text="⮌ Выйти из сейфа", font=("Arial", 10, "bold"), bg="#c0392b", fg="white", relief="ridge", command=self.logout)
        self.btn_logout.pack(fill="x", padx=10, pady=(10))

        # --- ПРАВАЯ РАБОЧАЯ ЗОНА ---
        self.work_frame = tk.Frame(root, bg="#f5f6fa")
        self.work_frame.grid(row=0, column=1, sticky="nsew")
        
        # По умолчанию открываем пароли
        self.show_passwords_page()

        # --- ТАЙМЕР АВТОБЛОКИРОВКИ (5 мин) ---
        self.timeout_ms = 300000  
        self.timer_id = None
        self.root.bind_all("<Any-KeyPress>", self.reset_timer)
        self.root.bind_all("<Any-ButtonPress>", self.reset_timer)
        self.start_timer()

    # --- СТРАНИЦА ПАРОЛЕЙ ---
    def show_passwords_page(self): 
        self.clear_work_frame()

        title = tk.Label(self.work_frame, text="Мои сохраненные пароли", font=("WDXL Lubrifont JP N", 23), bg="#f5f6fa")
        title.pack(anchor="w", padx=20, pady=(20,10))

        actions_frame = tk.Frame(self.work_frame, bg="#f5f6f9")
        actions_frame.pack(fill="x", padx=20, pady=5)

        # КНОПКА ДОБАВИТЬ ПАРОЛЬ
        btn_add = tk.Button(actions_frame, text="+ Добавить пароль", bg="#067375", fg="white", font=("Arial", 10, "bold"), padx=10, relief="ridge", command=self.add_password_dialog)
        btn_add.pack(side="left", padx=(0, 10))

        # КНОПКА УДАЛЕНИЯ ПАРОЛЯ
        btn_delete = tk.Button(actions_frame, text="✖ Удалить выбранный", bg="#e74c3c", fg="white", font=("Arial", 10, "bold"), padx=10, relief="ridge", command=self.delete_password)
        btn_delete.pack(side="left")

        columns = ("title", "login", "url")
        self.tree = ttk.Treeview(self.work_frame, columns=columns, show="headings")
        
        self.tree.heading("title", text="Название")
        self.tree.heading("login", text="Логин")
        self.tree.heading("url", text="Веб-сайт")
        
        self.tree.column("title", width=150)
        self.tree.column("login", width=150)
        self.tree.column("url", width=200)

        # Позволяем просматривать пароль по двойному клику на строку таблицы
        self.tree.bind("<Double-1>", self.view_password_details)
        
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        self.refresh_passwords_table()
    
    def view_password_details(self, event):
        """Открывает окно просмотра и копирования пароля при двойном клике на строку."""
        selected_item = self.tree.selection()
        if not selected_item:
            return
            
        # Получаем индекс выбранной строки в таблице
        index = self.tree.index(selected_item[0])
        
        # Достаем секретные данные из массива по этому индексу
        account_data = self.vault_data["credentials"][index]
        password_title = account_data["title"]
        secret_password = account_data["password"]

        # Создаем кастомное всплывающее окошко
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Пароль: {password_title}")
        dialog.geometry("380x150")
        dialog.resizable(False, False)
        dialog.grab_set()

        # Центрируем окошко на экране
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (190)
        y = (dialog.winfo_screenheight() // 2) - (75)
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text=f"Ключ от: {password_title}", font=("Arial", 11, "bold")).pack(pady=10)

        # Контейнер для поля ввода и кнопки глаза
        pass_frame = tk.Frame(dialog)
        # Оставляем чистый центр, без сковывающих padx
        pass_frame.pack(pady=5, padx=(25,4), anchor="center")

        # Поле, где отображается сам пароль
        pass_entry = tk.Entry(pass_frame, width=30, font=("Arial", 11), justify="center", show="*")
        pass_entry.pack(side="left", padx=(25, 4), anchor="center")
        
        pass_entry.insert(0, secret_password)
        pass_entry.config(state="readonly")

        # Вспомогательные функции для управления видимостью
        def show_password(event):
            """Показывает пароль (срабатывает при зажатии мыши)."""
            pass_entry.config(state="normal")
            pass_entry.config(show="")
            pass_entry.config(state="readonly")
            btn_eye.config(text="👁️")

        def hide_password(event):
            """Прячет пароль обратно (срабатывает при отпускании мыши)."""
            pass_entry.config(state="normal")
            pass_entry.config(show="*")
            pass_entry.config(state="readonly")
            btn_eye.config(text="👁️")

        # Кнопка глаза
        btn_eye = tk.Button(
            pass_frame, 
            text="👁️", 
            font=("Arial", 12), 
            bd=0,               
            relief="flat",      
            activebackground=dialog.cget("bg"), 
            bg=dialog.cget("bg"), 
            cursor="hand2"      
        )
        # Упаковываем глаз с минимальным зазором от поля, без правого отступа
        btn_eye.pack(side="left", padx=(0, 0), anchor="center")

        # Привязываем события зажатия и отпускания ЛКМ (Button-1)
        btn_eye.bind("<ButtonPress-1>", show_password)
        btn_eye.bind("<ButtonRelease-1>", hide_password)

        # Функция для кнопки копирования
        def copy_secret():
            self.root.clipboard_clear()
            self.root.clipboard_append(secret_password)
            btn_copy.config(text="✓ Скопировано!", bg="#2ecc71")    
            dialog.after(500, dialog.destroy)

        # Кнопка для быстрого копирования
        btn_copy = tk.Button(dialog, text="📋 Скопировать и закрыть", bg="#3498db", fg="white", font=("Arial", 10, "bold"),relief="ridge", command=copy_secret)
        btn_copy.pack(pady=10, padx=20) 

    def delete_password(self):
        """Удаляет выбранный пароль из таблицы и перезаписывает файл."""
        selected_item = self.tree.selection() # Смотрим, выбрал ли пользователь строку
        if not selected_item:
            messagebox.showwarning("Внимание", "Пожалуйста, выберите пароль из таблицы для удаления!")
            return

        # Получаем индекс выбранной строки
        index = self.tree.index(selected_item[0])
        password_title = self.vault_data["credentials"][index]["title"]

        # Спрашиваем подтверждение
        if messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите безвозвратно удалить пароль от '{password_title}'?"):
            # Удаляем из списка в памяти
            del self.vault_data["credentials"][index]
            # Шифруем обновленный список обратно в файл .dat
            encrypt_data(self.vault_data, self.master_password, CURRENT_FILE)
            # Обновляем таблицу на экране
            self.refresh_passwords_table()
            messagebox.showinfo("Успех", "Пароль успешно удален!")

    def refresh_passwords_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in self.vault_data.get("credentials", []):
            self.tree.insert("", "end", values=(row["title"], row["login"], row["url"]))

    def add_password_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить пароль")
        dialog.geometry("350x290")
        dialog.resizable(False, False)
        dialog.grab_set()

        tk.Label(dialog, text="Название:").pack(pady=2)
        entry_title = tk.Entry(dialog, width=35)
        entry_title.pack(pady=2)

        tk.Label(dialog, text="Логин:").pack(pady=2)
        entry_login = tk.Entry(dialog, width=35)
        entry_login.pack(pady=2)

        tk.Label(dialog, text="Веб-сайт:").pack(pady=2)
        entry_url = tk.Entry(dialog, width=35)
        entry_url.pack(pady=2)

        tk.Label(dialog, text="Пароль:").pack(pady=2)
        entry_pass = tk.Entry(dialog, width=35, show="*")
        entry_pass.pack(pady=2)

        def save_action():
            title, login, url, password = entry_title.get().strip(), entry_login.get().strip(), entry_url.get().strip(), entry_pass.get().strip()
            if not title or not password:
                messagebox.showwarning("Ошибка", "Заполните Название и Пароль!", parent=dialog)
                return

            self.vault_data["credentials"].append({"title": title, "login": login, "url": url, "password": password})
            encrypt_data(self.vault_data, self.master_password, CURRENT_FILE)
            messagebox.showinfo("Успех", "Пароль надежно зашифрован!", parent=dialog)
            self.refresh_passwords_table()
            dialog.destroy()

        btn_save_pass = tk.Button(dialog, text="⭳ Сохранить", width=26, bg="#0C9092", fg="black", font=("Arial", 10), relief="ridge", command=save_action)
        btn_save_pass.pack(pady=(15,10))
        btn_open_gen = tk.Button(dialog, text="⚙ Сгенерировать пароль", width=26, bg="#3498db", fg="black",font= ("Arial", 10),relief="ridge", command=lambda: self.open_password_generator(dialog, entry_pass))
        btn_open_gen.pack(pady=(0,15))

    
    def generate_random_password(self, length, use_special):
        """Генерирует криптографически стойкий случайный пароль."""
        import secrets
        import string

        letters = string.ascii_letters  # a-z, A-Z
        digits = string.digits          # 0-9 
        special = "!@#$%^&*()-_=+[{]};:,.<>/?" if use_special else ""

        # Собираем пул доступных символов
        alphabet = letters + digits + special

        # Гарантируем, что в пароле будет хотя бы одна буква и одна цифра
        password = [secrets.choice(letters), secrets.choice(digits)]
        if use_special:
            password.append(secrets.choice(special))

        # Забиваем оставшуюся длину случайными символами из пула
        remaining_length = length - len(password)
        password += [secrets.choice(alphabet) for _ in range(remaining_length)]

        # Перемешиваем символы, чтобы нарушить порядок гарантированных элементов
        secrets.SystemRandom().shuffle(password)
        return "".join(password)


    def open_password_generator(self, parent_dialog, target_entry):
        """Открывает модальное окно генератора паролей."""
        # Создаем всплывающее окно
        gen_window = tk.Toplevel(parent_dialog)
        gen_window.title("Генератор")
        gen_window.geometry("300x200")
        gen_window.resizable(False, False)
        
        # --- ДЕЛАЕМ ОКНО МОДАЛЬНЫМ ---
        gen_window.grab_set()  
        
        # Центрируем относительно родительского окна
        gen_window.update_idletasks()
        x = parent_dialog.winfo_x() + (parent_dialog.winfo_width() // 2) - 150
        y = parent_dialog.winfo_y() + (parent_dialog.winfo_height() // 2) - 110
        gen_window.geometry(f"+{x}+{y}")

        # Элементы интерфейса
        # 1. Создаем горизонтальный контейнер для строки управления длиной
        length_row_frame = tk.Frame(gen_window)
        length_row_frame.pack(pady=15) # Общий отступ для всей строки сверху и снизу

        # 2. Переменная для хранения длины
        length_var = tk.IntVar(master=gen_window, value=8) 

        # 3. Создаем спинбокс. Встраиваем его внутрь length_row_frame и пакуем СЛЕВА
        spin_length = tk.Spinbox(
            length_row_frame, # Изолируем внутри подфрейма
            from_=8, 
            to=32, 
            textvariable=length_var, 
            width=5, 
            justify="center", 
            font=("Arial", 10),
            state="readonly"
        )
        spin_length.pack(side="left") # Прижимаем к левому краю контейнера

        # 4. Создаем текстовую метку. Встраиваем туда же и пакуем СПРАВА (или тоже слева, но с отступом)
        label_length = tk.Label(length_row_frame, text="Длина пароля", font=("Arial", 10))
        label_length.pack(side="left", padx=(8, 0)) # Пакуем следом за спинбоксом и делаем отступ слева в 8 пикселей

        # Галочка для спецсимволов (тоже жестко привязываем к контексту окна)
        spec_var = tk.BooleanVar(master=gen_window, value=True)
        cb_special = tk.Checkbutton(
            gen_window, 
            text="Использовать спец. символы", 
            variable=spec_var, 
            font=("Arial", 10)
        )
        cb_special.pack(pady=10)

        # Функция нажатия кнопки
        def on_generate():
            try:
                length = int(length_var.get())
            except ValueError:
                length = 16 # Защита, если пользователь сотрет цифры в Spinbox вручную
                
            use_spec = spec_var.get()
            
            # Вызываем метод генерации через self
            new_password = self.generate_random_password(length, use_spec)
            
            # Вставляем пароль в целевое поле
            target_entry.config(state="normal")
            target_entry.delete(0, tk.END)
            target_entry.insert(0, new_password)
            
            gen_window.destroy() 

        # Кнопка генерации
        btn_gen = tk.Button(
            gen_window, 
            text="Сгенерировать и вставить", 
            bg="#1A937B", 
            fg="black", 
            font=("Arial", 10, "bold"),
            relief="ridge", 
            command=on_generate
        )
        btn_gen.pack(pady=15)

    # --- СТРАНИЦА ЗАМЕТОК ---
    def show_notes_page(self):
        self.clear_work_frame() 

        title = tk.Label(self.work_frame, text="Мои защищенные заметки", font=("WDXL Lubrifont JP N", 23), bg="#f5f6fa")
        title.pack(anchor="w", padx=20, pady=(20,10)) 

        # Панель для кнопок
        actions_frame = tk.Frame(self.work_frame, bg="#f5f6fa")
        actions_frame.pack(fill="x", padx=20, pady=5)

        # КНОПКА ДОБАВЛЕНИЯ ЗАМЕТКИ
        btn_add_note = tk.Button(actions_frame, text="+ Создать заметку", bg="#067375", fg="white", font=("Arial", 10, "bold"), padx=10, relief="ridge", command=self.add_note_dialog)
        btn_add_note.pack(side="left")

        # КНОПКА УДАЛЕНИЯ ЗАМЕТКИ
        btn_delete_note = tk.Button(actions_frame, text="✖ Удалить выбранную", bg="#e74c3c", fg="white", font=("Arial", 10, "bold"), padx=10, relief="ridge", command=self.delete_note)
        btn_delete_note.pack(side="left", padx=10)

        # Список заметок (выводим заголовки)
        self.notes_listbox = tk.Listbox(self.work_frame, font=("Arial", 12), width=50)
        self.notes_listbox.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Позволяем читать заметку по двойному клику
        self.notes_listbox.bind("<Double-1>", self.view_note_details)
        self.refresh_notes_list() 

    def delete_note(self):
        """Удаляет выбранную заметку из списка и перезаписывает файл."""
        selection = self.notes_listbox.curselection() # Смотрим, выделена ли заметка в списке
        if not selection:
            messagebox.showwarning("Внимание", "Пожалуйста, выберите заметку из списка для удаления!")
            return

        index = selection[0]
        note_title = self.vault_data["notes"][index]["title"]

        # Спрашиваем подтверждение
        if messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите безвозвратно удалить заметку '{note_title}'?"):
            # Удаляем из памяти
            del self.vault_data["notes"][index]
            # Шифруем базу заново
            encrypt_data(self.vault_data, self.master_password, CURRENT_FILE)
            # Перерисовываем список на экране
            self.refresh_notes_list()
            messagebox.showinfo("Успех", "Заметка успешно удалена!")

    def refresh_notes_list(self):
        self.notes_listbox.delete(0, tk.END)
        for note in self.vault_data.get("notes", []):
            self.notes_listbox.insert(tk.END, f"📝 {note['title']}")

    def add_note_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Создать заметку")
        dialog.geometry("400x350")
        dialog.grab_set()

        tk.Label(dialog, text="Название заметки:", font=("Arial", 10, "bold")).pack(pady=5)
        entry_title = tk.Entry(dialog, width=45)
        entry_title.pack(pady=5, fill="x", padx=20)

        tk.Label(dialog, text="Текст секретной заметки:", font=("Arial", 10, "bold")).pack(pady=5)
        text_content = tk.Text(dialog, width=45, height=10)
        text_content.pack(pady=5)

        def save_note():
            title = entry_title.get().strip()
            content = text_content.get("1.0", tk.END).strip()
            if not title or not content:
                messagebox.showwarning("Ошибка", "Заполните название и текст заметки!", parent=dialog)
                return

            self.vault_data["notes"].append({"title": title, "content": content})
            encrypt_data(self.vault_data, self.master_password, CURRENT_FILE)
            messagebox.showinfo("Успех", "Заметка зашифрована и сохранена!", parent=dialog)
            self.refresh_notes_list()
            dialog.destroy()

        tk.Button(dialog, text="⭳ Сохранить заметку", bg="#9b59b6", fg="white", font=("Arial", 10, "bold"), relief="ridge", command=save_note).pack(pady=10)

    def view_note_details(self, event):
        """Открывает окно просмотра и редактирования текста заметки при двойном клике."""
        selection = self.notes_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        note = self.vault_data["notes"][index]
        original_content = note["content"]

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Редактирование: {note['title']}")
        dialog.geometry("400x320")
        dialog.grab_set()

        tk.Label(dialog, text=note["title"], font=("Arial", 12, "bold")).pack(pady=5)
        
        # Текстовое поле РАЗРЕШЕНО для редактирования (по умолчанию state="normal") 
        text_widget = tk.Text(dialog, width=45, height=12, font=("Arial", 10))
        text_widget.pack(pady=5)
        text_widget.insert("1.0", original_content)
        text_widget.focus_set() # Сразу ставим курсор в текстовое поле

        def save_existing_note():
            """Внутренняя функция для сохранения изменений."""
            new_content = text_widget.get("1.0", tk.END).strip()
            if not new_content:
                messagebox.showwarning("Ошибка", "Текст заметки не может быть пустым!", parent=dialog)
                return
            
            # Обновляем данные в памяти и перезаписываем зашифрованный файл
            self.vault_data["notes"][index]["content"] = new_content
            encrypt_data(self.vault_data, self.master_password, CURRENT_FILE)
            
            # Обновляем локальную переменную original_content, чтобы окно закрывалось без предупреждений
            nonlocal original_content
            original_content = new_content
            
            # Меняем текст кнопки для визуального отклика
            btn_save.config(text="✓ Сохранено!", bg="#2ecc71")
            dialog.after(500, dialog.destroy)

        # Кнопка «Сохранить» внизу окна
        btn_save = tk.Button(dialog, text="⭳ Сохранить изменения", bg="#9b59b6", fg="white", font=("Arial", 10, "bold"), relief="ridge", command=save_existing_note)
        btn_save.pack(pady=10)

        def on_close_attempt():
            """Проверка изменений при попытке закрыть окно на крестик."""
            current_content = text_widget.get("1.0", tk.END).strip()
            
            # Если текст изменился по сравнению с тем, что было при открытии
            if current_content != original_content.strip():
                # Показываем диалоговое окно Да/Нет
                if messagebox.askyesno("Несохраненные изменения", "Сохранить изменения перед закрытием?", parent=dialog):
                    save_existing_note() # Если Да — сохраняем
                    return # save_existing_note сама закроет окно через 500мс
                
            # Если изменений нет или пользователь нажал "Нет" — просто закрываем окно
            dialog.destroy()

        # Перехватываем стандартное закрытие окна (нажатие на системный крестик 'X')
        dialog.protocol("WM_DELETE_WINDOW", on_close_attempt)

    #=================== ВСПЛЫВАЮЩЕЕ ОКНО АККАУНТОВ ===============================
    def toggle_accounts_panel(self):
        """Открывает или закрывает вылетающую панель аккаунтов поверх левого меню."""
        if self.accounts_frame and self.accounts_frame.winfo_exists():
            self.accounts_frame.destroy()
            return

        self.accounts_frame = tk.Frame(self.menu_frame, bg="#1a252f", width=185)
        self.accounts_frame.pack_propagate(False) #Чтобы виджеты не меняли размер окна 
        self.accounts_frame.place(x=0, y=0, relheight=1.0)

        # Кнопка-крестик для закрытия панели
        btn_close = tk.Button(self.accounts_frame, text="❌", font=("Arial", 10), bg="#1a252f", fg="#e74c3c", relief="flat", bd=0, command=self.accounts_frame.destroy)
        btn_close.pack(anchor="ne", padx=10, pady=5)

        tk.Label(self.accounts_frame, text="Аккаунты (Сейфы)", font=("WDXL Lubrifont JP N", 15), fg="white", bg="#1a252f").pack(pady=5)

        # Список аккаунтов
        self.acc_listbox = tk.Listbox(self.accounts_frame, bg="#2c3e50", fg="white", bd=0, highlightthickness=0, font=("Arial", 10), selectbackground="#3498db")
        self.acc_listbox.pack(fill="both", expand=True, padx=10, pady=5)
        
        # ОСТАВЛЯЕМ двойной клик как альтернативу
        self.acc_listbox.bind("<Double-1>", lambda event: self.switch_account())

        # --- КНОПКА ДЛЯ ВХОДА В АККАУНТ ---
        btn_login_acc = tk.Button(self.accounts_frame, text="✅Войти в выбранный", bg="#3498db", fg="black", font=("Arial", 10), relief="ridge", anchor="w", padx=10, command=self.switch_account)
        btn_login_acc.pack(fill="x", padx=10, pady=2)
        # --- КНОПКА ПЕРЕИМЕНОВАТЬ ---
        btn_rename_acc = tk.Button(self.accounts_frame, text="✅Переименовать", bg="#067375", fg="black", font=("Arial", 10), relief="ridge", anchor="w", padx=10, command=self.rename_account)
        btn_rename_acc.pack(fill="x", padx=10, pady=2)
        # --- КНОПКА СМЕНИТЬ ПАРОЛЬ ---
        btn_ch_password = tk.Button(self.accounts_frame, text="✅Сменить пароль", bg="#167A3B", fg="black", font=("Arial", 10), relief="ridge", anchor="w", padx=10, command=self.change_password)
        btn_ch_password.pack(fill="x", padx=10, pady=2)
        # --- КНОПКА ДОБАВИТЬ АККАУНТ ---
        btn_add_acc = tk.Button(self.accounts_frame, text="➕Добавить аккаунт", bg="#1db709", fg="black", font=("Arial", 10), relief="ridge", anchor="w", padx=10, command=self.add_account_dialog)
        btn_add_acc.pack(fill="x", padx=10, pady=2)
        # --- КНОПКА УДАЛИТЬ АККАУНТ ---
        btn_del_acc = tk.Button(self.accounts_frame, text="❎Удалить аккаунт", bg="#e74c3c", fg="black", font=("Arial", 10), relief="ridge", anchor="w", padx=10, command=self.delete_account_file)
        btn_del_acc.pack(fill="x", padx=10, pady=2)

        self.update_accounts_list() 

    def update_accounts_list(self):
        """Сканирует папку и обновляет список .dat файлов в панели аккаунтов."""
        self.acc_listbox.delete(0, tk.END)
        # Ищем все файлы, заканчивающиеся на .dat
        files = [f for f in os.listdir(".") if f.endswith(".dat")]
        for f in files:
            # Убираем расширение .dat для красивого отображения имени аккаунта
            acc_name = f.replace(".dat", "")
            # Помечаем звездочкой текущий активный аккаунт
            if f == CURRENT_FILE:
                acc_name += " ⭐"
            self.acc_listbox.insert(tk.END, acc_name)

    # --- ФУНКЦИИ ДЛЯ КНОПОК ОКНА АККАУНТОВ ---
    def switch_account(self):
        """Безопасно переключает текущий аккаунт и перезапускает авторизацию."""
        global CURRENT_FILE
        
        selection = self.acc_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Пожалуйста, сначала выберите аккаунт из списка!")
            return
            
        # Получаем чистое имя файла из выбранной строки
        selected_name = self.acc_listbox.get(selection[0]).replace(" ⭐", "")
        target_file = f"{selected_name}.dat"

        if target_file == CURRENT_FILE:
            messagebox.showinfo("Информация", "Этот аккаунт уже активен!")
            return

        # Переключаем глобальный указатель на новый файл
        CURRENT_FILE = target_file

        # Перед уничтожением окна обязательно сбрасываем таймер автоблокировки, чтобы он не тикал в фоне
        if self.timer_id is not None:
            self.root.after_cancel(self.timer_id)

        # Уничтожаем главное окно приложения
        self.root.destroy()
        
        # СРАЗУ ЖЕ запускаем новое окно входа для измененного CURRENT_FILE
        login_root = tk.Tk()
        
        # Передаем hide_cloud=True и жестко привязываем target_file
        LoginWindow(login_root, hide_cloud=True, target_file=target_file)
        
        login_root.mainloop()

    def rename_account(self):
        """Переименовывает выбранный в списке аккаунт (файл .dat и внутреннее поле JSON)."""
        global CURRENT_FILE
        
        # 1. Проверяем, выбран ли аккаунт в Listbox
        selection = self.acc_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Пожалуйста, сначала выберите аккаунт из списка!")
            return
            
        # Получаем текущее имя файла
        old_display_name = self.acc_listbox.get(selection[0]).replace(" ⭐", "")
        old_file = f"{old_display_name}.dat"
        
        # 2. Открываем мини-окно для ввода нового имени
        new_name = simpledialog.askstring(
            "Переименование", 
            f"Введите новое имя для аккаунта '{old_display_name}':", 
            parent=self.root
        )
        
        # Если пользователь нажал «Отмена» или ничего не ввёл
        if not new_name:
            return
            
        new_name = new_name.strip()
        new_file = f"{new_name}.dat"
        
        # 3. ПРОВЕРКА №1: Не совпадает ли новое имя со старым
        if new_file == old_file:
            return # Пользователь ввёл то же самое имя, ничего делать не нужно
            
        # 4. ПРОВЕРКА №2: Нет ли уже файла с таким же именем на диске
        if os.path.exists(new_file):
            messagebox.showerror("Ошибка", f"Аккаунт с именем '{new_name}' уже существует!")
            return

        # 5. Так как файл зашифрован, нам нужен Мастер-пароль, 
        # чтобы зайти внутрь и обновить поле "vault_name".
        # Если переименовывается текущий активный сейф, мы уже знаем пароль
        # Если переименовывается другой (неактивный) сейф, программа временно запросит от него пароль.
        
    
        password = None
        if old_file == CURRENT_FILE:
            password = self.master_password
        else:
            # Запрашиваем пароль от переименовываемого аккаунта
            password = simpledialog.askstring(
                "Подтверждение", 
                f"Введите Мастер-пароль от аккаунта '{old_display_name}' для подтверждения:", 
                show="*", 
                parent=self.root
            )
            if not password:
                return

        try:
            # Пробуем расшифровать старый файл, чтобы обновить структуру JSON
            decrypted_vault = decrypt_data(password, old_file)
            
            # Обновляем имя внутри JSON-шаблона
            decrypted_vault["vault_name"] = new_file
            
            # Перезаписываем данные уже в новый файл
            encrypt_data(decrypted_vault, password, new_file)
            
            # Удаляем старый физический файл с диска
            os.remove(old_file)
            
            # 6. Если мы переименовали тот сейф, в котором сейчас находимся,
            # обновляем глобальный указатель CURRENT_FILE
            if old_file == CURRENT_FILE:
                CURRENT_FILE = new_file
                
            messagebox.showinfo("Успех", f"Аккаунт успешно переименован в '{new_name}'!")
            self.update_accounts_list()
                
        except ValueError:
            messagebox.showerror("Ошибка доступа", "Неверный Мастер-пароль! Переименование отменено.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось переименовать файл: {e}")

    def change_password(self):
        """Открывает модальное окно для смены мастер-пароля выбранного сейфа."""
        global CURRENT_FILE

        # Создаем всплывающее модальное окно
        ch_window = tk.Toplevel(self.root)
        ch_window.title("Смена пароля")
        ch_window.geometry("350x180")
        ch_window.resizable(False, False)
        
        # --- ДЕЛАЕМ ОКНО МОДАЛЬНЫМ ---
        ch_window.grab_set()
        
        # Центрируем относительно главного окна
        ch_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 175
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 90
        ch_window.geometry(f"+{x}+{y}")
        
        # Получаем текущее имя файла для отображения в интерфейсе
        vault_name = CURRENT_FILE.removesuffix(".dat")
        
        # Элементы интерфейса
        lbl_title_1 = tk.Label(
            ch_window, 
            text=f"Смена пароля для \"{vault_name}\"", 
            font=("Arial", 11, "bold"),
            fg="#2c3e50"
        )
        lbl_title_1.pack(pady=(15, 10))
        
        # Поле ввода нового пароля (скрываем символы звездочками)
        entry_new_password = tk.Entry(ch_window, font=("Arial", 10), show="*", width=30)
        entry_new_password.pack(pady=5)
        entry_new_password.focus()
        
        # Функция обработки клика на "Подтвердить"
        def on_confirm():
            final_password = None
            new_password = entry_new_password.get().strip()
            # Собираем список всех локальных .dat файлов
            local_files = [f for f in os.listdir(".") if f.endswith(".dat")]
            
            if not new_password:
                messagebox.showerror("Ошибка", "Пароль не может быть пустым!", parent=ch_window)
                return
            
            if (len(new_password)<4):
                messagebox.showerror("Ошибка", "Пароль не меньше 4 символов!", parent=ch_window)
                return
            
            # Проверяем уникальность нового пароля
            conflict_again = False
            for local_file in local_files:
                try: 
                    decrypt_data(new_password, local_file)
                    conflict_again = True
                    break
                except ValueError:
                    continue
                        
            if conflict_again:
                messagebox.showerror("Ошибка", "Этот пароль занят! Придумайте другой.", parent=self.root)
                return
                            
            final_password = new_password
            

            
            try:
                # 1. Берем текущий словарь с паролями из памяти
                current_data = self.vault_data  
                
                # 2. Вызываем функцию шифрования, передавая данные, новый пароль и текущий файл
                encrypt_data(current_data, final_password, CURRENT_FILE) 
                
                # 3. Обновляем мастер-пароль в памяти текущей сессии главного окна
                self.master_password = final_password
                
                messagebox.showinfo("Успех", "Мастер-пароль успешно изменен!", parent=ch_window)
                ch_window.destroy()
                
            except Exception as e:
                # Проверяем, является ли пойманная ошибка ошибкой кодировки кириллицы
                if isinstance(e, UnicodeEncodeError):
                    messagebox.showerror("Ошибка","Пароль должен содержать только латиницу, цифры и спецсимволы!", parent=ch_window)
                else:
                # Для всех остальных непредвиденных ошибок оставляем стандартный вывод
                    messagebox.showerror("Ошибка", f"Не удалось изменить пароль: {e}", parent=ch_window)

        # Кнопка подтверждения
        btn_confirm = tk.Button(
            ch_window,
            text="Подтвердить",
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            command=on_confirm,
            width=15
        )
        btn_confirm.pack(pady=15)


    def add_account_dialog(self):
        """Перенаправляет пользователя на создание нового аккаунта в LoginWindow."""
        # Закрываем текущее главное окно приложения
        self.root.destroy()
        
        # Создаем новый корневой контекст для окна авторизации/регистрации
        login_root = tk.Tk()
        
        # Запускаем окно, скрывая блок облака и принудительно включая режим создания
        LoginWindow(login_root, force_create=True, hide_cloud=True, show_back_button=False)
        login_root.mainloop()
    


    def delete_account_file(self):
        """Удаляет выбранный файл аккаунта с диска после успешного ввода мастер-пароля."""
        selection = self.acc_listbox.curselection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите аккаунт для удаления!")
            return
        
        selected_name = self.acc_listbox.get(selection[0]).replace(" ⭐", "")
        target_file = f"{selected_name}.dat"

        # 1. Защита от удаления активного файла
        if target_file == CURRENT_FILE:
            messagebox.showerror("Ошибка", "Нельзя удалить текущий активный аккаунт!")
            return

        #2. Первое подтверждение намерения
        if not messagebox.askyesno("Удаление аккаунта",f"Вы уверены, что хотите БЕЗВОЗВРАТНО удалить аккаунт '{selected_name}'?\nЭто действие нельзя отменить!", default=messagebox.NO):
            return

        # 3. Запрос мастер-пароля для проверки прав
        confirm_password = simpledialog.askstring("Подтверждение пароля", f"Введите мастер-пароль от аккаунта '{selected_name}' для подтверждения удаления:", show="*")
    
        if not confirm_password:
            return # Пользователь нажал "Отмена" или ввел пустую строку

        # 4. Попытка расшифровать файл для валидации пароля
        if os.path.exists(target_file):
            try:
            # Вызываем твою стандартную функцию чтения и дешифрования.
                decrypt_data(confirm_password, target_file) 

            except Exception:
                # Если дешифрование упало — пароль точно не подошел
                messagebox.showerror("Ошибка", "Неверный мастер-пароль! Доступ к удалению заблокирован.")
                return

            # 5. Если дошли этой точки — дешифрование прошло успешно
            try:
                os.remove(target_file)
                self.update_accounts_list()
                messagebox.showinfo("Успех", f"Файл аккаунта '{selected_name}' успешно удален с диска.")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось физически удалить файл: {e}")
        else:
            messagebox.showerror("Ошибка", "Файл аккаунта не найден на диске.")


    # --- СЛУЖЕБНЫЕ МЕТОДЫ И СЕТЬ ---
    def clear_work_frame(self):
        for widget in self.work_frame.winfo_children():
            widget.destroy()

    def sync_with_cloud(self):
        if not os.path.exists(CURRENT_FILE):
            messagebox.showerror("Ошибка", "Файл базы данных не найден для бэкапа!")
            return
            
        messagebox.showinfo("Синхронизация", "Начинаем резервное копирование в облако...")
        
        backup_url = upload_to_cloud(CURRENT_FILE)
        
        if backup_url:
            # --- СОЗДАЕМ КАСТОМНОЕ ОКНО ДЛЯ КОПИРОВАНИЯ ССЫЛКИ ---
            copy_window = tk.Toplevel(self.root)
            copy_window.title("Бэкап завершен")
            copy_window.geometry("450x180")
            copy_window.resizable(False, False)
            copy_window.grab_set() # Блокирует основное окно, пока открыто это
            
            # Центрируем окошко относительно экрана
            copy_window.update_idletasks()
            x = (copy_window.winfo_screenwidth() // 2) - (225)
            y = (copy_window.winfo_screenheight() // 2) - (90)
            copy_window.geometry(f"+{x}+{y}")

            tk.Label(copy_window, text="🚀 Резервная копия успешно создана!", font=("WDXL Lubrifont JP N", 18), fg="#108564").pack(pady=10)
            tk.Label(copy_window, text="Ваша секретная ссылка для восстановления данных:", font=("WDXL Lubrifont JP N", 15)).pack(pady=2)
            
            # Поле со ссылкой (из него можно копировать вручную)
            url_entry = tk.Entry(copy_window, width=50, font=("Arial", 10), justify="center")
            url_entry.pack(pady=5)
            url_entry.insert(0, backup_url)
            url_entry.config(state="readonly") # Запрещаем редактировать ссылку, но выделять можно

            def copy_to_clipboard():
                self.root.clipboard_clear()
                self.root.clipboard_append(backup_url)
                #messagebox.showinfo("Успех", "Ссылка скопирована в буфер обмена!", parent=copy_window)
                copy_window.destroy()

            # Кнопка автоматического копирования
            btn_copy = tk.Button(copy_window, text="📋 Скопировать в буфер и закрыть", bg="#3498db", fg="white", relief="ridge", font=("Arial", 10, "bold"), command=copy_to_clipboard)
            btn_copy.pack(pady=10)
            
        else:
            messagebox.showerror("Ошибка соединения", "Не удалось отправить бэкап. Проверьте настройки сети или брандмауэра.")
            
    def logout(self):
        if messagebox.askyesno("Выход", "Закрыть сейф?"):
            if self.timer_id is not None:
                self.root.after_cancel(self.timer_id)
            self.root.destroy()
            login_root = tk.Tk()
            LoginWindow(login_root)
            login_root.mainloop()

    def start_timer(self):
        self.timer_id = self.root.after(self.timeout_ms, self.auto_lock)

    def reset_timer(self, event=None):
        """Сбрасывает таймер бездействия и запускает его заново."""
        if hasattr(self, 'timer_id') and self.timer_id is not None:
            try:
                self.root.after_cancel(self.timer_id)
            except Exception:
                pass # Если таймер уже выполнился или окно закрылось, игнорируем ошибку
        self.timer_id = None # Обнуляем указатель

        # Запускаем таймер заново
        self.start_timer()

    def auto_lock(self):
        self.master_password, self.vault_data, self.timer_id = None, None, None
        self.root.destroy()
        login_root = tk.Tk()
        LoginWindow(login_root)
        messagebox.showwarning("Сессия истекла", "Вы были разлогинены из-за отсутствия активности!", parent=login_root)
        login_root.mainloop()

#КЛАСС КАСТОМНОГО ОКНА ДЛЯ ИСКЛЮЧЕНИЯ: "Имя и пароль облачного файла совпадают с локальным файлом"
class DoubleInputDialog(tk.Toplevel):
    """Кастомное окно для одновременного ввода нового имени и пароля."""
    # Добавляем local_files и decrypt_func в аргументы init
    def __init__(self, parent, title, message, local_files=None, decrypt_func=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("350x220")
        self.resizable(False, False)
        self.grab_set() 
        
        self.local_files = local_files or []
        self.decrypt_func = decrypt_func
        self.result = None 
        
        # Текст ошибки/предупреждения
        tk.Label(self, text=message, wraplength=310, fg="#e74c3c", font=("Arial", 10, "bold")).pack(pady=10)
        
        # Поле имени
        frame_name = tk.Frame(self)
        frame_name.pack(fill='x', padx=20, pady=4)
        tk.Label(frame_name, text="Новое имя сейфа:", width=15, anchor='w').grid(row=0, column=0)
        self.entry_name = tk.Entry(frame_name, width=22)
        self.entry_name.grid(row=0, column=1)
        self.entry_name.focus_set() 
        
        # Поле пароля
        frame_pass = tk.Frame(self)
        frame_pass.pack(fill='x', padx=20, pady=4)
        tk.Label(frame_pass, text="Новый пароль:", width=15, anchor='w').grid(row=0, column=0)
        self.entry_pass = tk.Entry(frame_pass, width=22, show="*")
        self.entry_pass.grid(row=0, column=1)
        
        # Кнопки
        frame_btns = tk.Frame(self)
        frame_btns.pack(pady=15)
        tk.Button(frame_btns, text="Сохранить", bg="#117b3d", fg="white", width=12, relief="ridge", font=("Arial", 9, "bold"), command=self.on_submit).grid(row=0, column=0, padx=5)
        tk.Button(frame_btns, text="Отмена", bg="#95a5a6", fg="white", width=12, relief="ridge", font=("Arial", 9, "bold"), command=self.destroy).grid(row=0, column=1, padx=5)
        
        self.center_window()
        self.bind("<Return>", lambda event: self.on_submit())
        self.wait_window(self)
        
    def on_submit(self):
        name = self.entry_name.get().strip()
        password = self.entry_pass.get()
        
        if not name or not password:
            messagebox.showwarning("Ошибка", "Заполните все поля!", parent=self)
            return
        if len(password) < 4:
            messagebox.showwarning("Ошибка", "Пароль должен быть не менее 4 символов!", parent=self)
            return
            
        if not name.endswith(".dat"):
            name += ".dat"
            
        # 1. ПРОВЕРКА НА ЗАНЯТОЕ ИМЯ ФАЙЛА
        if os.path.exists(name):
            messagebox.showerror("Ошибка", f"Имя '{name}' уже занято локально! Придумайте другое.", parent=self)
            return

        # 2. ПРОВЕРКА НА ЗАНЯТЫЙ ПАРОЛЬ
        if self.decrypt_func:
            conflict_password = False
            for local_file in self.local_files:
                try:
                    self.decrypt_func(password, local_file)
                    conflict_password = True  # Если расшифровалось успешно — пароль совпал с каким-то сейфом
                    break
                except ValueError:
                    continue  # Ошибка расшифровки — значит пароль к этому файлу не подходит, идем дальше
            
            if conflict_password:
                messagebox.showerror("Ошибка", "Этот пароль уже используется для другого сейфа! Придумайте другой.", parent=self)
                return
            
        self.result = (name, password)
        self.destroy()

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LoginWindow(root)
    root.mainloop()