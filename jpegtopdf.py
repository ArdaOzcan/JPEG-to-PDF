import os
import sys
import argparse
import datetime
import tempfile
import platform
import subprocess
from fpdf import FPDF
from PIL import Image, ExifTags

action_index = 0
verbose = False


def show_file_in_explorer(file_path):
    """Open the file explorer and highlight the given file in it.

    This function is Windows-specific for now due to my lack of machines with different operating systems

    Positional arguments:
    file_path -- path of the file to be shown
    """
    if platform.system() == "Windows":
        file_path = file_path.replace('/', '\\')
        subprocess.Popen(f'explorer /select,{file_path}')


def log(msg):
    """Log a message to console using format [{action_index}][{date}]: {msg}.

    Positional arguments:
    msg -- message to be logged
    """
    global action_index
    global verbose
    if verbose:
        date = str(datetime.datetime.now()).split('.')[0]
        print(f'[{"{:05d}".format(action_index)}][{date}]: {msg}')
    action_index += 1


def compressed_image_name(old_name, quality):
    """Format a file name as CMP_{quality}_{filename}.

    Positional arguments:
    old_name -- name of the original image file
    quality -- desired JPEG quality of the output file
    """
    return os.path.join(tempfile.gettempdir(), f"CMP_{str(quality)}_{os.path.basename(old_name)}")


def open_with_correct_rotation(im_dir, file_name):
    """Return a PIL.Image object with correct rotation.

    This function was added due to PIL's way of opening JPEG images.
    JPEG images have an exif tag that tells the orientation of the image,
    check this link for further information: (https://magnushoff.com/articles/jpeg-orientation/)
    Opened image is rotated according to its orientation tag and returned to the caller.

    Positional arguments:
    im_dir -- directory path of the image to be opened
    file_name -- name of the image file to be opened
    """
    picture = Image.open(os.path.join(im_dir, file_name))
    exif = picture._getexif()
    if exif:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break

        if exif[orientation] == 3:
            picture = picture.transpose(Image.ROTATE_180)
        elif exif[orientation] == 6:
            picture = picture.transpose(Image.ROTATE_270)
        elif exif[orientation] == 8:
            picture = picture.transpose(Image.ROTATE_90)

    return picture


def compress(im_dir, file_name, log_func, quality=85):
    """Save PIL.Image object as a compressed JPEG image in the given quality.

    Positional arguments:
    im_dir -- directory path of the image to be compressed
    file_name -- name of the image file to be compressed
    log_func -- log function

    Keyword arguments:
    quality -- desired quality of the output file
    """
    picture = open_with_correct_rotation(im_dir, file_name)
    picture.save(compressed_image_name(file_name, quality),
                 'JPEG', optimize=True, quality=quality)
    log_func(f'COMPRESSED {os.path.join(im_dir, file_name)}')


def temp_cleanup(temp_list, log_func):
    """Clean up the temp directory of the user.

    Positional arguments:
    temp_list -- list of names of the every temp file created
    log_func -- log function
    """
    for file in temp_list:
        os.remove(file)
        log_func(f'REMOVING {file}')


def create_pdf(pdf_file_path, list_images, quality=85, im_dir='', log_func=log):
    """Create pdf file and return any temp files created.

    This is the main function called to create a pdf file.
    If this function is called by this file, images are compressed here.
    If this function is called by ui.py, images are already compressed before the call.
    log_func parameter is added because this function can be called either from this file or ui.py,
    in the ui version log function is different so it passes its own log function.

    Positional arguments:
    pdf_file_path -- path of the pdf file to be created
    list_images -- list of every compressed images that are going to be used in the pdf.

    Keyword arguments:
    quality -- desired quality of the output file
    im_dir -- directory path of the image to be compressed
    log_func -- log function
    """

    temp_files = set()
    if not pdf_file_path.endswith('.pdf'):
        pdf_file_path += '.pdf'

    cover_path = compressed_image_name(str(list_images[0]), quality)

    if not os.path.isfile(cover_path):
        compress(im_dir, list_images[0], log_func, quality=quality)
        temp_files.add(cover_path)

    with Image.open(cover_path) as cover:
        width, height = cover.size

    pdf = FPDF(unit='pt', format=[width, height])

    for page in list_images:
        pdf.add_page()

        try:
            pdf.image(compressed_image_name(str(page), quality), 0, 0)
        except RuntimeError:
            compress(im_dir, page, log_func, quality=quality)
            temp_files.add(compressed_image_name(page, quality))

            pdf.image(compressed_image_name(str(page), quality), 0, 0)

        log_func(f'ADDING {compressed_image_name(str(page), quality)}')

    pdf.output(pdf_file_path, 'F')
    log_func(f'EXPORTED TO {pdf_file_path}')
    return temp_files


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('pdf_file_name')
    parser.add_argument('-d', '--images_dir_path')
    parser.add_argument('-l', '--image_list', nargs='+', required=True)
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    parser.add_argument('-q', '--quality', action='store',
                        type=int, default=85)

    args = parser.parse_args()
    if args.images_dir_path is None:
        args.images_dir_path = os.getcwd()

    verbose = args.verbose
    pdf_path = os.path.join(os.getcwd(), args.pdf_file_name)
    temps = create_pdf(pdf_path, args.image_list,
                       quality=args.quality, im_dir=args.images_dir_path,
                       log_func=log)

    # If called by command-line, cleanup here. If using UI, cleanup is done in closeEvent()
    temp_cleanup(temps, log)

    if platform.system() == "Windows":
        print('Do you want to see the exported file in the explorer? (y/n) ', end='')
        if input() == 'y':
            show_file_in_explorer(pdf_path)
