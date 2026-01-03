import sys
import os
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QListWidget, QProgressBar, 
                             QTextEdit, QFileDialog, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from uploader import KATEGORILER

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_config():
    """JSON dosyasından konfigürasyonu yükle"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_config(config):
    """Konfigürasyonu JSON dosyasına kaydet"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except IOError:
        return False

class UploadThread(QThread):
    progress_update = pyqtSignal(int)
    log_update = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, uploader_class, api_key, files, category_id):
        super().__init__()
        self.uploader_class = uploader_class
        self.api_key = api_key
        self.files = files
        self.category_id = category_id

    def run(self):
        uploader = self.uploader_class(self.api_key, self.log_update.emit)
        try:
            uploader.upload_files(self.files, self.category_id, self.progress_update.emit)
        except Exception as e:
            self.log_update.emit(f"Error: {str(e)}")
        finally:
            self.finished_signal.emit()

class DropListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDropMode.DropOnly)
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            links = []
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isfile(path):
                    links.append(path)
                elif os.path.isdir(path):
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            links.append(os.path.join(root, file))
            self.addItems(links)
        else:
            event.ignore()

class NewsturkUploaderApp(QMainWindow):
    def __init__(self, uploader_cls):
        super().__init__()
        self.uploader_cls = uploader_cls
        self.config = load_config()
        self.setWindowTitle("Newsturk Yükleyici")
        self.resize(600, 600)
        
        self.init_ui()
        self.apply_styles()
        self.load_saved_api_key()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # API Key Section
        api_layout = QHBoxLayout()
        api_label = QLabel("API Anahtarı:")
        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("API Anahtarınızı buraya girin...")
        self.save_api_btn = QPushButton("Kaydet")
        self.save_api_btn.setMaximumWidth(80)
        api_layout.addWidget(api_label)
        api_layout.addWidget(self.api_input)
        api_layout.addWidget(self.save_api_btn)
        main_layout.addLayout(api_layout)

        # Category Section
        cat_layout = QHBoxLayout()
        cat_label = QLabel("Kategori:")
        self.cat_combo = QComboBox()
        # Sort categories by ID
        for cat_id, cat_name in sorted(KATEGORILER.items()):
            self.cat_combo.addItem(f"{cat_name} (ID: {cat_id})", cat_id)
        
        cat_layout.addWidget(cat_label)
        cat_layout.addWidget(self.cat_combo)
        main_layout.addLayout(cat_layout)

        # File Selection Section
        file_btn_layout = QHBoxLayout()
        self.add_files_btn = QPushButton("Dosya Ekle")
        self.add_folder_btn = QPushButton("Klasör Ekle")
        self.clear_btn = QPushButton("Listeyi Temizle")
        
        file_btn_layout.addWidget(self.add_files_btn)
        file_btn_layout.addWidget(self.add_folder_btn)
        file_btn_layout.addStretch()
        file_btn_layout.addWidget(self.clear_btn)
        main_layout.addLayout(file_btn_layout)

        self.file_list = DropListWidget()
        main_layout.addWidget(QLabel("Dosyaları aşağıya sürükleyip bırakın:"))
        main_layout.addWidget(self.file_list)

        # Progress Section
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        # Action Buttons
        self.start_btn = QPushButton("Yüklemeyi Başlat")
        self.start_btn.setMinimumHeight(40)
        main_layout.addWidget(self.start_btn)

        # Log Section
        main_layout.addWidget(QLabel("İşlem Kayıtları (Logs):"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        main_layout.addWidget(self.log_output)

        # Connections
        self.add_files_btn.clicked.connect(self.add_files)
        self.add_folder_btn.clicked.connect(self.add_folder)
        self.clear_btn.clicked.connect(self.file_list.clear)
        self.start_btn.clicked.connect(self.start_upload)
        self.save_api_btn.clicked.connect(self.save_api_key)

    def apply_styles(self):
        # A simple dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #dddddd;
                font-size: 14px;
            }
            QLineEdit, QComboBox {
                padding: 8px;
                background-color: #3b3b3b;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
            }
            QComboBox::drop-down {
                border: 0px;
            }
            QListWidget {
                background-color: #3b3b3b;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                font-family: Consolas, monospace;
            }
            QPushButton {
                padding: 8px 16px;
                background-color: #007acc;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #008be0;
            }
            QPushButton:pressed {
                background-color: #005f99;
            }
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #05B8CC;
                width: 20px;
            }
        """)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Dosyaları Seç", "", "NZB Files (*.nzb);;All Files (*)")
        if files:
            self.file_list.addItems(files)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Klasör Seç")
        if folder:
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(".nzb"):
                        self.file_list.addItem(os.path.join(root, file))

    def log_message(self, message):
        self.log_output.append(message)
        # Scroll to bottom
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def start_upload(self):
        api_key = self.api_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "Hata", "Lütfen geçerli bir API Anahtarı girin.")
            return

        count = self.file_list.count()
        if count == 0:
            QMessageBox.warning(self, "Hata", "Lütfen yüklenecek dosyaları ekleyin.")
            return
        
        # API anahtarını otomatik olarak kaydet
        self.config["api_key"] = api_key
        save_config(self.config)
            
        category_id = self.cat_combo.currentData()

        files = [self.file_list.item(i).text() for i in range(count)]
        
        self.start_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log_message("Yükleme başlatılıyor...")

        self.thread = UploadThread(self.uploader_cls, api_key, files, category_id)
        self.thread.progress_update.connect(self.update_progress)
        self.thread.log_update.connect(self.log_message)
        self.thread.finished_signal.connect(self.upload_finished)
        self.thread.start()

    def upload_finished(self):
        self.start_btn.setEnabled(True)
        self.log_message("İşlem tamamlandı.")

    def load_saved_api_key(self):
        """Kaydedilmiş API anahtarını yükle"""
        api_key = self.config.get("api_key", "")
        if api_key:
            self.api_input.setText(api_key)
            self.log_message("✓ Kaydedilmiş API anahtarı yüklendi.")

    def save_api_key(self):
        """API anahtarını manuel olarak kaydet"""
        api_key = self.api_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "Hata", "Lütfen geçerli bir API Anahtarı girin.")
            return
        
        self.config["api_key"] = api_key
        if save_config(self.config):
            QMessageBox.information(self, "Başarılı", "API anahtarı kaydedildi!")
            self.log_message("✓ API anahtarı config.json dosyasına kaydedildi.")
        else:
            QMessageBox.warning(self, "Hata", "API anahtarı kaydedilemedi.")
