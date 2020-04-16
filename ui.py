from PyQt5 import QtWidgets, QtGui, QtCore
import jpegtopdf
import os
import datetime
import subprocess
import sys
import platform


def open_document(filepath):
    if platform.system() == "Windows":
        filepath = filepath.replace('/', '\\')
        subprocess.Popen(f'explorer /select,{filepath}')


class LabelWidgetCouple(QtWidgets.QHBoxLayout):

    def __init__(self, label_text, widget):
        super().__init__()

        self.label = QtWidgets.QLabel(label_text)
        self.addWidget(self.label)

        self.widget = widget
        self.addWidget(self.widget)


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


class Window(QtWidgets.QMainWindow):
    def __init__(self, title, theme):
        super().__init__()
        self.theme = theme
        self.action_index = 0
        self.setGeometry(0, 0, 850, 500)

        self.setMinimumWidth(650)
        self.setMinimumHeight(400)

        self.setWindowTitle(title)
        self.setStyleSheet(
            f'background:{theme.bg_color}; color:{theme.fg_color}')
        self.initiate_ui()
        self.show()
        self.log('PROGRAM STARTED SUCCESSFULLY')

        self.temp_files = set()

    def initiate_ui(self):
        # Main Layout
        self.layout = QtWidgets.QGridLayout()

        # Top bar
        self.top_bar = QtWidgets.QFrame()
        self.top_bar.setStyleSheet(f'background:{self.theme.mid_color}')
        self.top_bar.setFixedHeight(75)
        self.layout.addWidget(self.top_bar, 0, 0)

        self.top_bar_layout = QtWidgets.QGridLayout(self.top_bar)
        self.top_bar_layout.setColumnStretch(2, 4)

        title_font = QtGui.QFont()
        title_font.setBold(True)
        title_font.setPointSize(25)
        self.title_label = QtWidgets.QLabel('JPEG-to-PDF')
        self.title_label.setFont(title_font)

        by_font = QtGui.QFont()
        by_font.setBold(True)
        by_font.setPointSize(12)
        self.by_label = QtWidgets.QLabel('by Arda Özcan')
        self.by_label.setFont(by_font)

        self.top_bar_layout.addWidget(self.title_label, 0, 3)
        self.top_bar_layout.addWidget(self.by_label, 1, 3)

        self.open_files_button = QtWidgets.QPushButton('Open File...')
        self.open_files_button.pressed.connect(self.open_file_names_dialog)
        self.top_bar_layout.addWidget(self.open_files_button, 0, 0)

        self.save_button = QtWidgets.QPushButton('Save')
        self.save_button.pressed.connect(self.create_pdf)
        self.top_bar_layout.addWidget(self.save_button, 1, 0)

        # Compression amount
        self.quality_input = LabelWidgetCouple(
            'JPEG Quality: ', QtWidgets.QLineEdit('85'))
        self.quality_input.widget.setValidator(QtGui.QIntValidator())
        self.top_bar_layout.addLayout(self.quality_input, 0, 1)

        self.bottom_bar = QtWidgets.QFrame()
        self.bottom_bar.setStyleSheet(f'background:{self.theme.bg_color}')
        self.layout.addWidget(self.bottom_bar, 1, 0)

        self.bottom_bar_layout = QtWidgets.QGridLayout(self.bottom_bar)
        self.bottom_bar_right_layout = QtWidgets.QGridLayout()

        self.combo_box_layout = QtWidgets.QVBoxLayout()

        self.log_console = QtWidgets.QTextEdit()
        self.log_console.setStyleSheet(f'background:{self.theme.mid_color}')
        self.log_console.setFocusPolicy(QtCore.Qt.NoFocus)

        self.bottom_bar_right_layout.addWidget(self.log_console, 1, 0)
        self.bottom_bar_right_layout.addLayout(self.combo_box_layout, 0, 0)

        self.bottom_bar_layout.addLayout(self.bottom_bar_right_layout, 0, 1)

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFixedWidth(200)
        self.bottom_bar_layout.addWidget(self.scroll, 0, 0)

        self.w = QtWidgets.QWidget()
        self.setCentralWidget(self.w)
        self.w.setLayout(self.layout)

    def order_changer(self, index):
        def set_order_index(image):
            self.new_image_order[index] = self.list_images[image]
            new_p = QtGui.QPixmap(os.path.join(
                self.image_dir, self.list_images[image]))
            new_p = new_p.scaledToWidth(155)
            self.label_list[index].setPixmap(new_p)
        return set_order_index

    def open_file_names_dialog(self):
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, "Choose files", "", "JPEG Files (*.jpg; *.jpeg)")

        if not files:
            return

        self.list_images = []
        self.image_dir = os.path.split(files[0])[0]

        mygroupbox = QtWidgets.QGroupBox()
        myform = QtWidgets.QVBoxLayout()
        self.label_list = []
        for i, f in enumerate(files):
            self.list_images.append(os.path.split(f)[1])
            jpegtopdf.compress(
                self.image_dir, self.list_images[i], self.log,
                self.get_quality_input())
            self.temp_files.add(jpegtopdf.compressed_image_name(
                self.list_images[i], self.get_quality_input()))
            l = QtWidgets.QLabel()
            p = QtGui.QPixmap(jpegtopdf.compressed_image_name(
                self.list_images[i], self.get_quality_input()))
            p = p.scaledToWidth(155)
            l.setPixmap(p)
            self.label_list.append(l)
            myform.addWidget(l)

        self.new_image_order = [i for i in self.list_images]

        for i in reversed(range(self.combo_box_layout.count())):
            self.combo_box_layout.itemAt(i).widget().setParent(None)

        for i in range(len(self.list_images)):
            cb = QtWidgets.QComboBox()
            cb.addItems(self.list_images)
            cb.setCurrentIndex(i)
            set_order_func = self.order_changer(i)
            cb.currentIndexChanged.connect(set_order_func)
            self.combo_box_layout.addWidget(cb)

        mygroupbox.setLayout(myform)
        self.scroll.setWidget(mygroupbox)

    def log(self, msg):
        date = str(datetime.datetime.now()).split('.')[0]
        prompt = f'[{"{:05d}".format(self.action_index)}][{date}]: '
        self.log_console.append(f'<b>{prompt}</b> <h>{msg}</h>')
        self.action_index += 1

    def get_quality_input(self):
        try:
            quality = int(self.quality_input.widget.text())
        except ValueError:
            quality = 85

        return quality

    def create_pdf(self):
        pdf_file_name, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save file", "", "PDF File (*.pdf)")

        if not pdf_file_name:
            return

        if not pdf_file_name.endswith('.pdf'):
            pdf_file_name += '.pdf'

        additional_temps = jpegtopdf.create_pdf(pdf_file_name, self.new_image_order,
                                                quality=self.get_quality_input(), im_dir=self.image_dir, log_func=self.log)

        self.temp_files = self.temp_files.union(additional_temps)

        if platform.system() == "Windows":
            buttons = QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes
            msg = QtWidgets.QMessageBox.question(
                self, 'JPEG-to-PDF', 'Do you want to open the exported file in the explorer?', buttons,
                QtWidgets.QMessageBox.No)

            if msg == QtWidgets.QMessageBox.Yes:
                open_document(pdf_file_name)

    def closeEvent(self, *args, **kwargs):
        super(QtWidgets.QMainWindow, self).closeEvent(*args, **kwargs)
        jpegtopdf.temp_cleanup(self.temp_files, self.log)


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    w = Window('JPEG-to-PDF', Theme('theme.json'))
    sys.exit(app.exec_())
