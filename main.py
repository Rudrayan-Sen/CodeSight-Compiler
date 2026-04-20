import sys
from PyQt6.QtWidgets import QApplication
from gui import CompilerGUI

def main():
    app = QApplication(sys.argv)
    window = CompilerGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
