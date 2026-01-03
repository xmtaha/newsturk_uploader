import sys
from PyQt6.QtWidgets import QApplication
from gui import NewsturkUploaderApp
from uploader import Uploader

def main():
    app = QApplication(sys.argv)
    window = NewsturkUploaderApp(Uploader)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
