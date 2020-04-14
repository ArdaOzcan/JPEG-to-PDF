from PyQt5.QtGui import QPixmap
import sys
from PyQt5.QtWidgets import QMainWindow, QDialog, QApplication, QGridLayout, QPushButton, QFileDialog, QWidget, QLabel, QComboBox, QGroupBox, QScrollArea, QHBoxLayout, QLineEdit
import converter
import os


class Theme:
    default_creation = False
    def __init__(self, source_file, fg_color="#BBBBBB", mid_color="#252525", bg_color="#151515"):
        self.fg_color = fg_color
        self.mid_color = mid_color
        self.bg_color = bg_color
        self.source_file = source_file

    @staticmethod
    def load_from_json(fp):
        import json
        t = Theme(fp)
        try:
            with open(fp, 'r') as file:
                t.__dict__ = json.load(file)
        except FileNotFoundError:
            t.fg_color = "#BBBBBB"
            t.mid_color = "#252525"
            t.bg_color = "#151515"
            t.default_creation = True
        return t


class InfoDialog(QDialog):
    def __init__(self, parent, title, message, theme):
        super().__init__(parent)
        self.setStyleSheet(
            f'background:{theme.bg_color}; color:{theme.fg_color}')
        self.setWindowTitle(title)
        self.layout = QGridLayout()
        self.layout.addWidget(QLabel(message))
        self.ok_button = QPushButton('OK')
        self.ok_button.pressed.connect(self.accept)
        self.layout.addWidget(self.ok_button)
        self.setLayout(self.layout)
        self.show()


class Window(QMainWindow):
    def __init__(self, theme, title='window'):
        super().__init__()
        self.theme = theme
        if self.theme.default_creation:
            dlg = InfoDialog(self, 'INFO',
                             f'Theme file you provided "{theme.source_file}" not found.\nContinuing with the default theme', self.theme)
            dlg.exec_()

        self.setStyleSheet(
            f'background:{self.theme.bg_color}; color:{self.theme.fg_color}')

        self.setWindowTitle(title)
        self.initiate_ui()

        self.show()

    def open_file_names_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "QFileDialog.getOpenFileNames()", "", "JPEG Files (*.jpg; *.jpeg)")
        self.list_images = []
        self.image_dir = os.path.split(files[0])[0]

        if files:
            mygroupbox = QGroupBox()
            myform = QHBoxLayout()
            label_list = []
            for i, f in enumerate(files):
                self.list_images.append(os.path.split(f)[1])
                l = QLabel()
                p = QPixmap(f)
                p = p.scaledToHeight(75)
                l.setPixmap(p)
                label_list.append(l)
                myform.addWidget(l)
            self.new_image_order = [i for i in self.list_images]

            for i in range(len(self.list_images)):
                cb = QComboBox()
                cb.addItems(self.list_images)
                cb.setCurrentIndex(i)
                set_order_func = self.order_changer(i)
                cb.currentIndexChanged.connect(set_order_func)
                self.layout.addWidget(cb, i + 2, 0)

            mygroupbox.setLayout(myform)
            scroll = QScrollArea()
            scroll.setWidget(mygroupbox)
            scroll.setWidgetResizable(True)
            scroll.setFixedHeight(100)
            self.layout.addWidget(scroll, 1, 0)
            self.pdf_file_name_horiztonal = QHBoxLayout()
            self.pdf_file_name_horiztonal.addWidget(QLabel('PDF File Name: '))
            self.pdf_file_name_line_edit = QLineEdit()
            self.pdf_file_name_line_edit.setStyleSheet(
                f'background:{self.theme.mid_color}')
            self.pdf_file_name_horiztonal.addWidget(
                self.pdf_file_name_line_edit)
            self.setFixedWidth(400)

            self.layout.addLayout(
                self.pdf_file_name_horiztonal, len(self.list_images) + 3, 0)
            self.layout.addWidget(self.create_button)

    def order_changer(self, index):
        def set_order_index(image):
            self.new_image_order[index] = self.list_images[image]
        return set_order_index

    def create_pdf(self):
        converter.create_pdf(self.pdf_file_name_line_edit.text(),
                             self.new_image_order, self.image_dir)

    def initiate_ui(self):
        self.layout = QGridLayout()

        self.choose_file_button = QPushButton('Choose files')
        self.choose_file_button.clicked.connect(self.open_file_names_dialog)
        self.layout.addWidget(self.choose_file_button, 0, 0)

        self.create_button = QPushButton('Create')
        self.create_button.clicked.connect(self.create_pdf)

        self.w = QWidget()
        self.w.setLayout(self.layout)
        self.setCentralWidget(self.w)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    win = Window(Theme.load_from_json('theme.json'), 'JPEG to PDF')
    sys.exit(app.exec_())
