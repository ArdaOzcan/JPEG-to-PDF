import os
import sys
import datetime
import platform
import jpegtopdf
from PyQt5 import QtWidgets, QtGui, QtCore


class LabelWidgetCouple(QtWidgets.QHBoxLayout):
    """A class to create a label and a widget next to it

    Since it inherits QtWidgets.QHBoxLayout, passing a LabelWidgetCouple object to e.g. QtWidgets.QGridLayout().addLayout() would work.
    """

    def __init__(self, label_text, widget):
        """Initiate method for LabelWidgetCouple

        Positional arguments:
        label_text -- text of the label
        widget -- QtWidgets.QWidget object next to the label
        """

        super().__init__()

        self.label = QtWidgets.QLabel(label_text)
        self.addWidget(self.label)

        self.widget = widget
        self.addWidget(self.widget)


class Theme:
    """A class for holding three colors

    Three colors are: bg_color, mid_color and fg_color.
    Mostly, only bg_color and fg_color is used but mid_color was also added
    to create more depth with some widgets.

    Methods:

    @staticmethod
    load_from_json(fp) -- load a json file, convert it to a Theme object and return it

    """

    def __init__(self, source_file, fg_color="#BBBBBB", mid_color="#252525", bg_color="#151515"):
        """Initiate method for Theme

        Positional arguments:
        source_file -- source file path of the theme

        Keyword arguments:
        fg_color -- foreground color
        mid_color -- a color between bg_color and fg_color
        bg_color -- background color

        """
        self.fg_color = fg_color
        self.mid_color = mid_color
        self.bg_color = bg_color
        self.source_file = source_file

    @staticmethod
    def load_from_json(fp):
        """Load a json file, convert it to a Theme object and return it

        If no file named fp was found then source_file is set to None 
        and the program uses the hard coded colors.
        """
        import json
        t = Theme(fp)
        try:
            with open(fp, 'r') as file:
                t_dict = json.load(file)
                t.bg_color = t_dict['bg_color']
                t.mid_color = t_dict['mid_color']
                t.fg_color = t_dict['fg_color']
        except FileNotFoundError:
            t.fg_color = "#BBBBBB"
            t.mid_color = "#252525"
            t.bg_color = "#151515"
            t.source_file = None
        return t


class Window(QtWidgets.QMainWindow):
    """Main window class

    This class is the main window of the application.

    Methods:
    initiate_ui() -- initiate every permament UI component
    make_set_image_func(order_index) -- return another function to be called 
                                        when a combobox is changed
    open_file_names_dialog() -- open a dialog to choose one or more files 
                                of type .jpg or .jpeg  and return the paths
    log(msg) -- log a message to the log console
    get_quality_input() -- get current quality in the QTextEdit
    create_pdf() -- open a dialog to save file and calls jpegtopdf.create_pdf()
    closeEvent(*args, **kwargs) -- overridden function from 
                                   QtWidgets.QMainWindow, do temp cleanup

    """

    def __init__(self, title, theme):
        """Initiate method for Window.

        Positional arguments:
        title -- window title
        theme -- theme of the window

        """
        super().__init__()
        self.theme = theme
        self.action_index = 0
        self.setGeometry(0, 0, 850, 500)

        self.setMinimumWidth(650)
        self.setMinimumHeight(400)

        self.temp_files = set()
        self.list_images = []
        self.list_pixmaps = []

        self.current_pixmap_width = 100

        self.setWindowTitle(title)
        self.setStyleSheet(
            f'background:{theme.bg_color}; color:{theme.fg_color}')
        self.initiate_ui()
        self.show()
        self.log('PROGRAM STARTED SUCCESSFULLY')

    def initiate_ui(self):
        """Initiate every permament UI component.

        Most UI initiation is done here but some widgets 
        like local gbox, vbox and cb are initiated in 
        open_files_name_dialog()

        """
        # Main Layout
        self.layout = QtWidgets.QGridLayout()

        # Top bar
        self.top_bar = QtWidgets.QFrame()
        self.top_bar.setStyleSheet(f'background:{self.theme.mid_color}')
        self.top_bar.setFixedHeight(75)
        self.layout.addWidget(self.top_bar, 0, 0)

        self.top_bar_layout = QtWidgets.QGridLayout(self.top_bar)
        self.top_bar_layout.setColumnStretch(2, 4)

        # Title
        title_font = QtGui.QFont()
        title_font.setBold(True)
        title_font.setPointSize(25)
        self.title_label = QtWidgets.QLabel('JPEG-to-PDF')
        self.title_label.setFont(title_font)

        # By-line
        by_font = QtGui.QFont()
        by_font.setBold(True)
        by_font.setPointSize(12)
        self.by_label = QtWidgets.QLabel('by Arda Özcan')
        self.by_label.setFont(by_font)

        self.top_bar_layout.addWidget(self.title_label, 0, 3)
        self.top_bar_layout.addWidget(self.by_label, 1, 3)

        # Open files button
        self.open_files_button = QtWidgets.QPushButton('Open Files...')
        self.open_files_button.pressed.connect(self.open_file_names_dialog)
        self.top_bar_layout.addWidget(self.open_files_button, 0, 0)

        # Save button
        self.save_button = QtWidgets.QPushButton('Save')
        self.save_button.pressed.connect(self.create_pdf)
        self.top_bar_layout.addWidget(self.save_button, 1, 0)

        # Quality input
        self.quality_input = LabelWidgetCouple(
            'JPEG Quality: ', QtWidgets.QLineEdit('85'))
        self.quality_input.widget.setValidator(QtGui.QIntValidator())
        self.top_bar_layout.addLayout(self.quality_input, 0, 1)

        # Pixmap width
        self.pixmap_width_slider = QtWidgets.QSlider()
        self.pixmap_width_slider.setOrientation(QtCore.Qt.Horizontal)
        self.pixmap_width_slider.setFixedWidth(self.get_scroll_width())
        self.pixmap_width_slider.setMaximum(250)
        self.pixmap_width_slider.setMinimum(150)
        # Start in the middle
        self.pixmap_width_slider.setValue(self.pixmap_width_slider.minimum()
                                          + ((self.pixmap_width_slider.maximum() - self.pixmap_width_slider.minimum()) * 0.5))
        self.pixmap_width_slider.valueChanged.connect(
            self.on_pixmap_width_changed)

        # Bottom bar
        self.bottom_bar = QtWidgets.QFrame()
        self.bottom_bar.setStyleSheet(f'background:{self.theme.bg_color}')
        self.layout.addWidget(self.bottom_bar, 1, 0)

        self.bottom_bar_layout = QtWidgets.QGridLayout(self.bottom_bar)
        self.bottom_bar_right_layout = QtWidgets.QGridLayout()

        # Layout for combo boxes that will be created
        self.combo_box_layout = QtWidgets.QVBoxLayout()

        # Log console
        self.log_console = QtWidgets.QTextEdit()
        self.log_console.setStyleSheet(f'background:{self.theme.mid_color}')
        self.log_console.setFocusPolicy(QtCore.Qt.NoFocus)

        self.bottom_bar_right_layout.addWidget(self.log_console, 1, 0)
        self.bottom_bar_right_layout.addLayout(self.combo_box_layout, 0, 0)

        self.bottom_bar_layout.addLayout(self.bottom_bar_right_layout, 0, 1)

        # Scroll area
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFixedWidth(self.get_scroll_width())
        self.bottom_bar_layout.addWidget(self.scroll, 0, 0)
        self.bottom_bar_layout.addWidget(self.pixmap_width_slider, 1, 0)

        self.w = QtWidgets.QWidget()
        self.setCentralWidget(self.w)
        self.w.setLayout(self.layout)

    def make_set_image_func(self, order_index):
        """Create a set_image(image_index) function specific for every order_index.

        QtWidgets.QComboBox.currentIndexChanged calls its connected function 
        and passes in the new index when the selection changes. For every combobox 
        at index of order_index, a set_image(image_index) function is created and connected to
        currentIndexChanged signal so when a selection changes, image order and pixmap of the label
        in order_index changes to the image at the image_index.

        Positional argumenst:
        order_index -- index of combobox and label

        For further information on function returning check:
        https://stackoverflow.com/questions/12738031/creating-a-new-function-as-return-in-python-function/12738091
        https://en.wikipedia.org/wiki/First-class_function

        """
        def set_image(image_index):
            """Set image of label at the order_index to image at image_index"""
            # Change order of images
            self.image_order[order_index] = image_index

            # Create new QPixmap with path of image at index of image_index
            new_p = QtGui.QPixmap(os.path.join(
                self.image_dir, self.list_images[image_index]))
            new_p = new_p.scaledToWidth(self.current_pixmap_width)

            # Set pixmap of label at index of order_index
            self.label_list[order_index].setPixmap(new_p)

        return set_image

    def on_pixmap_width_changed(self, v):
        """Change related widgets according to pixmap width slider
        
        This is called when self.pixmap_width_slider 's value changes.
        
        Positional arguments:
        v -- new value
        """
        for i in range(len(self.list_images)):
            self.label_list[i].setPixmap(
                self.list_pixmaps[self.image_order[i]].scaledToWidth(v))
        self.scroll.setFixedWidth(self.get_scroll_width())
        self.pixmap_width_slider.setFixedWidth(self.get_scroll_width())
        self.current_pixmap_width = v

    def open_file_names_dialog(self):
        """Open a 'Open files' dialog and update everything accordingly

        This method opens a dialog to get input files. 
        If the return value is None, this method returns as well.
        If the operation was successful, this method continues to 
        update every widget and variable accordingly. 
        """
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, "Choose files", "", "JPEG Files (*.jpg; *.jpeg)")

        if not files:
            return

        # Empty lists for a new process
        self.list_images = []
        self.label_list = []
        self.list_pixmaps = []

        # Update self.image_dir
        self.image_dir = os.path.split(files[0])[0]

        # These variables are for UI layout
        gbox = QtWidgets.QGroupBox()
        vbox = QtWidgets.QVBoxLayout()
        for i, f in enumerate(files):
            # Add image name to self.list_images
            self.list_images.append(os.path.split(f)[1])
            compressed_name = jpegtopdf.compressed_image_name(
                self.list_images[i], self.get_quality_input())

            # Compress image
            jpegtopdf.compress(
                self.image_dir, self.list_images[i], self.log,
                self.get_quality_input())

            # Add compressed image to self.temp_files
            self.temp_files.add(compressed_name)

            p = QtGui.QPixmap(compressed_name)
            self.list_pixmaps.append(p)
            p = p.scaledToWidth(self.current_pixmap_width)

            l = QtWidgets.QLabel()
            l.setPixmap(p)
            self.label_list.append(l)
            vbox.addWidget(l)

        # List to hold image indexes of labels
        self.image_order = [i for i in range(len(self.list_images))]

        # Loop to clear previous comboboxes
        for i in reversed(range(self.combo_box_layout.count())):
            self.combo_box_layout.itemAt(i).widget().setParent(None)

        # Loop to create new comboboxes
        for i in range(len(self.list_images)):
            cb = QtWidgets.QComboBox()
            cb.addItems(self.list_images)
            cb.setCurrentIndex(i)

            set_order_func = self.make_set_image_func(i)
            cb.currentIndexChanged.connect(set_order_func)
            self.combo_box_layout.addWidget(cb)

        gbox.setLayout(vbox)
        self.scroll.setWidget(gbox)

    def log(self, msg):
        """Log a message to the log console using format [{self.action_index}][{date}]: {msg}.

        Positional arguments:
        msg -- message to be logged
        """
        date = str(datetime.datetime.now()).split('.')[0]
        prompt = f'[{"{:05d}".format(self.action_index)}][{date}]: '
        # Used HTML tags to create both bold and regular text in one line
        self.log_console.append(f'<b>{prompt}</b> <h>{msg}</h>')
        self.action_index += 1

    def get_quality_input(self):
        """Get the current input from the QTextEdit"""
        try:
            quality = int(self.quality_input.widget.text())
        except ValueError:
            quality = 85

        return quality

    def get_scroll_width(self):
        return self.current_pixmap_width + 46

    def create_pdf(self):
        """Call the jpegtopdf.create_pdf function using the correct inputs.

        Temp files that are returned from the jpegtopdf.create_pdf 
        function are unioned with self.temp_files to be used in temp_cleanup.
        If the user is using Windows, a dialog appears and 
        asks if the user wants to see the exported file in the explorer. 
        If the user says yes, it is shown.
        """
        pdf_file_name, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save file", "", "PDF File (*.pdf)")

        if not pdf_file_name:
            return

        if not pdf_file_name.endswith('.pdf'):
            pdf_file_name += '.pdf'

        additional_temps = jpegtopdf.create_pdf(pdf_file_name, [self.list_images[i] for i in self.image_order],
                                                quality=self.get_quality_input(), im_dir=self.image_dir, log_func=self.log)

        self.temp_files = self.temp_files.union(additional_temps)

        if platform.system() == "Windows":
            buttons = QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes
            msg = QtWidgets.QMessageBox.question(
                self, 'JPEG-to-PDF', 'Do you want to see the exported file in the explorer?', buttons,
                QtWidgets.QMessageBox.No)

            if msg == QtWidgets.QMessageBox.Yes:
                jpegtopdf.show_file_in_explorer(pdf_file_name)

    def closeEvent(self, *args, **kwargs):
        """Clean temp files up in close event.
        Note: If the application is forcibly closed, this cleanup can't be done.
        """
        jpegtopdf.temp_cleanup(self.temp_files, self.log)
        super(QtWidgets.QMainWindow, self).closeEvent(*args, **kwargs)


if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    w = Window('JPEG-to-PDF', Theme.load_from_json('theme.json'))
    sys.exit(app.exec_())
