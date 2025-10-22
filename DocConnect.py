import os
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
from PyPDF2 import PdfReader, PdfWriter
import customtkinter as ctk
from PIL import Image
import sys


class PDFMergerApp:
    def __init__(self):
        # Настройка внешнего вида
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("PDF Merger - Замена титульных листов")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # Переменные для хранения путей
        self.titles_folder = tk.StringVar()
        self.reports_folder = tk.StringVar()
        self.output_folder = tk.StringVar()

        self.is_processing = False
        self.setup_ui()

    def setup_ui(self):
        # Главный контейнер
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Заголовок
        title_label = ctk.CTkLabel(
            main_frame,
            text="Замена титульных листов в PDF",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 30))

        # Фрейм для выбора папок
        folders_frame = ctk.CTkFrame(main_frame)
        folders_frame.pack(fill="x", pady=(0, 20))

        # Папка с титулами
        self.create_folder_selector(
            folders_frame,
            "Папка с титульными листами:",
            self.titles_folder,
            0
        )

        # Папка с отчетами
        self.create_folder_selector(
            folders_frame,
            "Папка с исходными PDF:",
            self.reports_folder,
            1
        )

        # Папка для результатов
        self.create_folder_selector(
            folders_frame,
            "Папка для сохранения результатов:",
            self.output_folder,
            2
        )

        # Кнопки управления
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.pack(fill="x", pady=(0, 20))

        self.process_btn = ctk.CTkButton(
            buttons_frame,
            text="Начать обработку",
            command=self.start_processing,
            font=ctk.CTkFont(size=16),
            height=40
        )
        self.process_btn.pack(side="left", padx=(0, 10))

        self.clear_btn = ctk.CTkButton(
            buttons_frame,
            text="Очистить все",
            command=self.clear_all,
            font=ctk.CTkFont(size=16),
            fg_color="#D35B58",
            hover_color="#C04B48",
            height=40
        )
        self.clear_btn.pack(side="left")

        # Прогресс бар
        self.progress = ctk.CTkProgressBar(main_frame)
        self.progress.pack(fill="x", pady=(0, 10))
        self.progress.set(0)

        # Статус
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Готов к работе",
            font=ctk.CTkFont(size=14)
        )
        self.status_label.pack(pady=(0, 20))

        # Лог выполнения
        log_label = ctk.CTkLabel(
            main_frame,
            text="Лог выполнения:",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        log_label.pack(anchor="w")

        # Текстовое поле для лога
        self.log_text = ctk.CTkTextbox(
            main_frame,
            height=200,
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.log_text.pack(fill="both", expand=True)

        # Добавляем начальное сообщение в лог
        self.log("Программа готова к работе. Выберите папки и нажмите 'Начать обработку'.")

    def create_folder_selector(self, parent, label_text, variable, row):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=5)

        label = ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(size=14))
        label.pack(anchor="w", pady=(5, 2))

        entry_frame = ctk.CTkFrame(frame, fg_color="transparent")
        entry_frame.pack(fill="x")

        entry = ctk.CTkEntry(
            entry_frame,
            textvariable=variable,
            font=ctk.CTkFont(size=12),
            height=35
        )
        entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        browse_btn = ctk.CTkButton(
            entry_frame,
            text="Обзор",
            command=lambda: self.browse_folder(variable),
            width=80,
            height=35
        )
        browse_btn.pack(side="right")

    def browse_folder(self, variable):
        folder = filedialog.askdirectory()
        if folder:
            variable.set(folder)

    def log(self, message):
        """Добавляет сообщение в лог"""
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.root.update_idletasks()

    def clear_all(self):
        """Очищает все поля"""
        self.titles_folder.set("")
        self.reports_folder.set("")
        self.output_folder.set("")
        self.log_text.delete("1.0", "end")
        self.progress.set(0)
        self.status_label.configure(text="Готов к работе")
        self.log("Все поля очищены. Программа готова к новой работе.")

    def validate_inputs(self):
        """Проверяет корректность введенных данных"""
        if not self.titles_folder.get():
            messagebox.showerror("Ошибка", "Выберите папку с титульными листами")
            return False

        if not self.reports_folder.get():
            messagebox.showerror("Ошибка", "Выберите папку с исходными PDF")
            return False

        if not self.output_folder.get():
            messagebox.showerror("Ошибка", "Выберите папку для сохранения результатов")
            return False

        if not os.path.exists(self.titles_folder.get()):
            messagebox.showerror("Ошибка", "Папка с титульными листами не существует")
            return False

        if not os.path.exists(self.reports_folder.get()):
            messagebox.showerror("Ошибка", "Папка с исходными PDF не существует")
            return False

        return True

    def start_processing(self):
        """Запускает процесс обработки в отдельном потоке"""
        if self.is_processing:
            return

        if not self.validate_inputs():
            return

        self.is_processing = True
        self.process_btn.configure(state="disabled")
        self.clear_btn.configure(state="disabled")
        self.progress.set(0)

        # Запуск в отдельном потоке
        thread = threading.Thread(target=self.process_pdfs)
        thread.daemon = True
        thread.start()

    def process_pdfs(self):
        """Основной процесс обработки PDF"""
        try:
            folder_titles = self.titles_folder.get()
            folder_reports = self.reports_folder.get()
            folder_output = self.output_folder.get()

            os.makedirs(folder_output, exist_ok=True)

            # Получаем список PDF файлов
            pdf_files = [f for f in os.listdir(folder_titles) if f.lower().endswith(".pdf")]
            total_files = len(pdf_files)

            if total_files == 0:
                self.log("❌ В папке с титульными листами не найдено PDF файлов")
                return

            self.log(f"📁 Найдено файлов для обработки: {total_files}")

            processed = 0
            errors = 0

            for filename in pdf_files:
                try:
                    self.status_label.configure(text=f"Обработка: {filename}")
                    self.log(f"🔹 Обрабатывается: {filename}")

                    title_path = os.path.join(folder_titles, filename)
                    report_path = os.path.join(folder_reports, filename)

                    if not os.path.exists(report_path):
                        self.log(f"❌ Отчет не найден: {filename}")
                        errors += 1
                        continue

                    # Читаем титул и отчет
                    title_reader = PdfReader(title_path)
                    report_reader = PdfReader(report_path)

                    # Проверка: титул должен содержать 1 страницу
                    if len(title_reader.pages) != 1:
                        self.log(f"⚠️ В титуле {filename} не 1 страница (найдено {len(title_reader.pages)})")
                        errors += 1
                        continue

                    writer = PdfWriter()

                    # Добавляем титул
                    writer.add_page(title_reader.pages[0])

                    # Добавляем остальные страницы отчета
                    for page in report_reader.pages[1:]:
                        writer.add_page(page)

                    output_path = os.path.join(folder_output, filename)
                    with open(output_path, "wb") as f_out:
                        writer.write(f_out)

                    self.log(f"✅ Успешно обработан: {filename}")
                    processed += 1

                except Exception as e:
                    self.log(f"❌ Ошибка при обработке {filename}: {str(e)}")
                    errors += 1

                # Обновляем прогресс
                processed += 1
                progress_value = processed / total_files
                self.progress.set(progress_value)

            # Итоговое сообщение
            self.status_label.configure(text="Обработка завершена")
            self.log("=" * 50)
            self.log(f"🎉 ОБРАБОТКА ЗАВЕРШЕНА!")
            self.log(f"✅ Успешно обработано: {processed} файлов")
            self.log(f"❌ Ошибок: {errors}")
            self.log(f"📁 Результаты сохранены в: {folder_output}")

        except Exception as e:
            self.log(f"💥 Критическая ошибка: {str(e)}")
            messagebox.showerror("Ошибка", f"Произошла критическая ошибка:\n{str(e)}")

        finally:
            self.is_processing = False
            self.process_btn.configure(state="normal")
            self.clear_btn.configure(state="normal")

    def run(self):
        """Запускает приложение"""
        self.root.mainloop()


def main():
    try:
        app = PDFMergerApp()
        app.run()
    except Exception as e:
        messagebox.showerror("Ошибка запуска", f"Не удалось запустить приложение:\n{str(e)}")


if __name__ == "__main__":
    main()