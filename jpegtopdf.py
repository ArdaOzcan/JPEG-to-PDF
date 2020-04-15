import os
import sys
import argparse
import datetime

from fpdf import FPDF
from PIL import Image, ExifTags

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
    return os.path.join('temp', f'cmp_{old_name}')


def open_with_correct_rotation(im_dir, fp):
    picture = Image.open(os.path.join(im_dir, fp))
    for orientation in ExifTags.TAGS.keys():
        if ExifTags.TAGS[orientation] == 'Orientation':
            break

    if picture._getexif()[orientation] == 3:
        picture = picture.transpose(Image.ROTATE_180)
    elif picture._getexif()[orientation] == 6:
        picture = picture.transpose(Image.ROTATE_270)
    elif picture._getexif()[orientation] == 8:
        picture = picture.transpose(Image.ROTATE_90)

    return picture


def compress(im_dir, file):
    picture = open_with_correct_rotation(im_dir, file)
    picture.save(compressed_image_name(file),
                 'JPEG', optimize=True, quality=85)


def check_temp_folder():
    log('CHECKING IF \\temp EXISTS')
    if not os.path.isdir('temp'):
        os.mkdir('temp')
        log('CREATING \\temp')


def temp_cleanup(list_images):
    for page in list_images:
        os.remove(compressed_image_name(page))
        log(f'REMOVING {compressed_image_name(str(page))}')


def create_pdf(pdf_file_name, list_images, dir=''):
    check_temp_folder()

    if not pdf_file_name.endswith('.pdf'):
        pdf_file_name += '.pdf'

    try:
        with Image.open(compressed_image_name(str(list_images[0]))) as cover:
            width, height = cover.size
    except FileNotFoundError:
        compress(dir, list_images[0])
        log(f'COMPRESSING {list_images[0]}')
        with Image.open(compressed_image_name(str(list_images[0]))) as cover:
            width, height = cover.size

    pdf = FPDF(unit="pt", format=[width, height])

    for page in list_images:
        pdf.add_page()

        try:
            pdf.image(compressed_image_name(str(page)), 0, 0)
        except RuntimeError:
            compress(dir, page)
            log(f'COMPRESSING {page}')
            pdf.image(compressed_image_name(str(page)), 0, 0)

        log(f'ADDING {compressed_image_name(str(page))}')

    pdf.output(os.path.join(os.getcwd(), pdf_file_name), 'F')
    log(f'EXPORTING TO {os.path.join(os.getcwd(), pdf_file_name)}')


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('pdf_file_name')
    parser.add_argument('-d', '--images_dir_path')
    parser.add_argument('-l', '--image_list', nargs='+', required=True)
    parser.add_argument('-v', '--verbose', action='store_true', default=False)

    args = parser.parse_args()
    if args.images_dir_path is None:
        args.images_dir_path = os.getcwd()

    verbose = args.verbose
    create_pdf(args.pdf_file_name, args.image_list, args.images_dir_path)
    temp_cleanup(args.image_list) # If called by command-line, cleanup here. If using UI, cleanup is done in closeEvent()
