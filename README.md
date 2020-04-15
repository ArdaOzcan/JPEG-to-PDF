# JPEG-to-PDF
Simple python script to convert multiple or single JPEG images to .pdf files using JPEG compression and a UI version created with PyQt5

## Downloading

You can clone the repo using git:
```
git clone https://github.com/ArdaOzcan/JPEG-to-PDF
```
Or under the repository name, click **Clone or download** and then click **Download ZIP**.

### Note
After download, if you want to use the python file run:
```
pip install -r requirements.txt
```

## Usage

There are two ways to use the program, you can either 
- Execute jpegtopdf.py alone from the command line 
**or**
- Use the UI version (ui.py or bin/ui.exe).

**Note:** The binary version was built in a **_64-bit Windows 10_**. It may not be compatible with your PC. If you want to compile the python script yourself according to your structure please visit [PyInstaller](https://pyinstaller.readthedocs.io/en/stable/usage.html).

Usage of jpegtopdf.py is simple, you can see all the options by writing:
```
D:\\Users\\user\\JPEG-to-PDF>.\jpegtopdf.py -h
usage: jpegtopdf.py [-h] [-d IMAGES_DIR_PATH] -l IMAGE_LIST [IMAGE_LIST ...]
                    [-v]
                    pdf_file_name

positional arguments:
  pdf_file_name

optional arguments:
  -h, --help            show this help message and exit
  -d IMAGES_DIR_PATH, --images_dir_path IMAGES_DIR_PATH
  -l IMAGE_LIST [IMAGE_LIST ...], --image_list IMAGE_LIST [IMAGE_LIST ...]
  -v, --verbose

```

