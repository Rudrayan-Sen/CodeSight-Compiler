import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QPushButton, QTabWidget, 
                             QTableWidget, QTableWidgetItem, QTreeWidget, 
                             QTreeWidgetItem, QSplitter, QLabel, QHeaderView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QPalette

from lexer import Lexer
from parser import Parser, ASTNode
from semantic import SemanticAnalyzer
from intermediate_code import TACGenerator
from optimizer import Optimizer

class CompilerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Mini Compiler")
        self.resize(1000, 700)
        self.setup_ui()
        self.apply_dark_theme()

    def setup_ui(self):
        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Editor Panel (Left)
        editor_panel = QWidget()
        editor_layout = QVBoxLayout(editor_panel)
        
        editor_label = QLabel("Source Code:")
        editor_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.editor = QTextEdit()
        self.editor.setFont(QFont("Consolas", 12))
        self.editor.setPlainText("int a = 10;\nfloat b = 3.14;\nif (a == 10) {\n    b = b + 2.0 * 5.0;\n}")
        
        btn_layout = QHBoxLayout()
        self.btn_compile = QPushButton("Compile All")
        self.btn_compile.clicked.connect(self.compile_all)
        btn_layout.addWidget(self.btn_compile)
        
        editor_layout.addWidget(editor_label)
        editor_layout.addWidget(self.editor)
        editor_layout.addLayout(btn_layout)
        
        # Tabs Panel (Right)
        tabs_panel = QWidget()
        tabs_layout = QVBoxLayout(tabs_panel)
        self.tabs = QTabWidget()
        
        # Tokens Tab
        self.tokens_table = QTableWidget(0, 4)
        self.tokens_table.setHorizontalHeaderLabels(["Type", "Value", "Line", "Column"])
        self.tokens_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabs.addTab(self.tokens_table, "Tokens")
        
        # Parse Tree Tab
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("Abstract Syntax Tree")
        self.tabs.addTab(self.tree_widget, "Parse Tree")
        
        # Symbol Table Tab
        self.sym_table = QTableWidget(0, 2)
        self.sym_table.setHorizontalHeaderLabels(["Name", "Type"])
        self.sym_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabs.addTab(self.sym_table, "Symbol Table")
        
        # TAC Tab
        self.tac_text = QTextEdit()
        self.tac_text.setReadOnly(True)
        self.tac_text.setFont(QFont("Consolas", 12))
        self.tabs.addTab(self.tac_text, "Intermediate Code")
        
        # Opt TAC Tab
        self.opt_text = QTextEdit()
        self.opt_text.setReadOnly(True)
        self.opt_text.setFont(QFont("Consolas", 12))
        self.tabs.addTab(self.opt_text, "Optimized Code")
        
        # Errors Tab
        self.error_text = QTextEdit()
        self.error_text.setReadOnly(True)
        self.error_text.setTextColor(QColor("red"))
        self.error_text.setFont(QFont("Consolas", 11))
        self.tabs.addTab(self.error_text, "Errors")

        tabs_layout.addWidget(self.tabs)

        # Add to splitter
        splitter.addWidget(editor_panel)
        splitter.addWidget(tabs_panel)
        splitter.setSizes([400, 600])

    def apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(45, 45, 45))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(212, 212, 212))
        palette.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 45))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(212, 212, 212))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(212, 212, 212))
        palette.setColor(QPalette.ColorRole.Text, QColor(212, 212, 212))
        palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(212, 212, 212))
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(212, 212, 212))
        
        self.setPalette(palette)
        
        self.setStyleSheet("""
            QWidget { background-color: #2D2D2D; color: #D4D4D4; }
            QTextEdit { background-color: #1E1E1E; border: 1px solid #3C3C3C; }
            QTableWidget { background-color: #1E1E1E; gridline-color: #3C3C3C; }
            QHeaderView::section { background-color: #3C3C3C; color: #D4D4D4; border: 1px solid #2D2D2D; }
            QTreeWidget { background-color: #1E1E1E; border: 1px solid #3C3C3C; }
            QPushButton { background-color: #0E639C; color: white; border-radius: 4px; padding: 6px; }
            QPushButton:hover { background-color: #1177BB; }
            QTabBar::tab { background: #3C3C3C; padding: 8px; margin: 2px; border-radius: 4px; }
            QTabBar::tab:selected { background: #0E639C; }
        """)

    def build_ast_tree(self, parent_item, node):
        if not node:
            return
        item = QTreeWidgetItem(parent_item, [node.name])
        for child in node.children:
            if isinstance(child, ASTNode):
                self.build_ast_tree(item, child)
            else:
                QTreeWidgetItem(item, [str(child)])

    def compile_all(self):
        source = self.editor.toPlainText()
        all_errors = []

        # 1. Lexical Analysis
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        all_errors.extend(lexer.errors)
        
        self.tokens_table.setRowCount(0)
        for t in tokens:
            row = self.tokens_table.rowCount()
            self.tokens_table.insertRow(row)
            self.tokens_table.setItem(row, 0, QTableWidgetItem(t.type))
            self.tokens_table.setItem(row, 1, QTableWidgetItem(str(t.value)))
            self.tokens_table.setItem(row, 2, QTableWidgetItem(str(t.line)))
            self.tokens_table.setItem(row, 3, QTableWidgetItem(str(t.column)))

        # 2. Syntax Analysis
        parser = Parser(tokens)
        ast, parse_errors = parser.parse()
        all_errors.extend(parse_errors)
        
        self.tree_widget.clear()
        if ast:
            self.build_ast_tree(self.tree_widget, ast)
            self.tree_widget.expandAll()

        # 3. Semantic Analysis
        if ast:
            semantic = SemanticAnalyzer(ast)
            sym_table, sym_errors = semantic.analyze()
            all_errors.extend(sym_errors)
            
            self.sym_table.setRowCount(0)
            for name, type_ in sym_table.get_all().items():
                row = self.sym_table.rowCount()
                self.sym_table.insertRow(row)
                self.sym_table.setItem(row, 0, QTableWidgetItem(name))
                self.sym_table.setItem(row, 1, QTableWidgetItem(type_))
        else:
            self.sym_table.setRowCount(0)

        # 4. Intermediate Code Gen
        tac_code = []
        if ast and not parse_errors:
            tac = TACGenerator(ast)
            tac_code = tac.generate()
            self.tac_text.setPlainText("\n".join(tac_code))
        else:
            self.tac_text.setPlainText("TAC Generation skipped due to parse errors.")

        # 5. Optimization
        if tac_code:
            optimizer = Optimizer(tac_code)
            opt_code = optimizer.optimize()
            self.opt_text.setPlainText("\n".join(opt_code))
        else:
            self.opt_text.setPlainText("")

        # Display Errors
        if all_errors:
            self.error_text.setPlainText("\n".join(all_errors))
            self.tabs.setCurrentIndex(5) # Jump to Errors tab
        else:
            self.error_text.setPlainText("No errors found. Compilation successful!")
            self.tabs.setCurrentIndex(1) # Jump to AST tab

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CompilerGUI()
    window.show()
    sys.exit(app.exec())
