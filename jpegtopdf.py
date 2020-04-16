import os
import sys
import argparse
import datetime

from fpdf import FPDF
from PIL import Image, ExifTags
import tempfile

action_index = 0
verbose = False


def log(msg):
    global action_index
    global verbose
    if verbose:
        date = str(datetime.datetime.now()).split('.')[0]
        print(f'[{"{:05d}".format(action_index)}][{date}]: {msg}')
    action_index += 1


def compressed_image_name(old_name):
    return os.path.join(tempfile.gettempdir(), f"CMP_{os.path.basename(old_name)}")


def open_with_correct_rotation(im_dir, fp):
    picture = Image.open(os.path.join(im_dir, fp))
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


def compress(im_dir, file, quality=85):
    picture = open_with_correct_rotation(im_dir, file)
    picture.save(compressed_image_name(file),
                 'JPEG', optimize=True, quality=quality)


def temp_cleanup(list_images, log_func):
    for page in list_images:
        os.remove(compressed_image_name(page))
        log_func(f'REMOVING {compressed_image_name(str(page))}')


def create_pdf(pdf_file_path, list_images, quality=85, im_dir='', log_func=log):

    if not pdf_file_path.endswith('.pdf'):
        pdf_file_path += '.pdf'

    try:
        with Image.open(compressed_image_name(str(list_images[0]))) as cover:
            width, height = cover.size
    except FileNotFoundError:
        compress(im_dir, list_images[0], quality=quality)
        log_func(f'COMPRESSING {list_images[0]}')
        with Image.open(compressed_image_name(str(list_images[0]))) as cover:
            width, height = cover.size

    pdf = FPDF(unit="pt", format=[width, height])

    for page in list_images:
        pdf.add_page()

        try:
            pdf.image(compressed_image_name(str(page)), 0, 0)
        except RuntimeError:
            compress(im_dir, page, quality=quality)
            log_func(f'COMPRESSING {page}')
            pdf.image(compressed_image_name(str(page)), 0, 0)

        log_func(f'ADDING {compressed_image_name(str(page))}')

    pdf.output(pdf_file_path, 'F')
    log_func(f'EXPORTING TO {pdf_file_path}')


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('pdf_file_name')
    parser.add_argument('-d', '--images_dir_path')
    parser.add_argument('-l', '--image_list', nargs='+', required=True)
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    parser.add_argument('-q', '--quality', action='store', type=int, default=85)

    args = parser.parse_args()
    if args.images_dir_path is None:
        args.images_dir_path = os.getcwd()

    verbose = args.verbose
    print(args.quality)
    create_pdf(os.path.join(os.getcwd(), args.pdf_file_name), args.image_list,
               quality=args.quality, im_dir=args.images_dir_path,
               log_func=log)
    # If called by command-line, cleanup here. If using UI, cleanup is done in closeEvent()
    temp_cleanup(args.image_list, log)
