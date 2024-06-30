#!/usr/bin/env python3
"""
Program to automatically download comics from
readallcomics.com. Outputs whole comics collected
into one pdf per comic with automatic scaling and
advertisement removal, also rotates landscape pages
automatically.
"""
from os import makedirs

import requests
from bs4 import BeautifulSoup as BS
from fpdf import FPDF
from PIL import Image

from status.status import Status, get_status_length

__author__ = "nighmared"
__version__ = 1.21

DEBUG = False  # makes it more verbose
# Default PDF dimensions, will be adjusted dynamically
PDF_H = 300  # Height of resulting PDF
PDF_W = 200  # Width of resulting PDF

PROGRESS_BAR_LEN = 50  # length of the progress bar that is displayed
STATUS_LEN = get_status_length() + 1  # How much space must be accounted for the status in the progress bar
NUM_STEPS = len(Status)  # Number of steps the program goes through
STEP_SIZE = PROGRESS_BAR_LEN // NUM_STEPS  # equal length parts for the status bar

def main():
    """
    Main method that reads entries from the links.txt file and processes them one after another.
    """
    lines = []
    try:
        with open("links.txt", "r") as file:
            makedirs("pdfs", exist_ok=True)
            lines = file.readlines()
    except FileNotFoundError:
        with open("links.txt", "w"):
            pass
        print("Can't find the 'links.txt' file. I created one for you. Make sure to fill it with entries!")
    print(f"Found {len(lines)} Entries")
    i = 0
    for entry in lines:
        name, link = entry.split(";")
        handle_entry(url=link, name=name)
        i += 1
    if i == 0:
        print("No entries in 'links.txt'. Did nothing.")

def make_progress_bar(current: int, max_len: int, step: int) -> str:
    """
    Creates a progress bar string for the given current progress.
    """
    perc = step * STEP_SIZE + (STEP_SIZE * current) // max_len
    return f"[{('|' * perc).ljust(PROGRESS_BAR_LEN)}]"

def make_status_string(current_status: Status, step_num: int, title: str, current_progress: int, max_progress: int) -> str:
    """
    Creates a status string for the current progress of the script.
    """
    res = (
        title.ljust(40)
        + current_status.value.center(STATUS_LEN)
        + make_progress_bar(current_progress, max_progress, step_num)
    )
    return res

def handle_entry(url: str, name: str) -> None:
    """
    Processes a single comic entry, downloads the images, removes banners, and creates a PDF.
    """
    url = url.strip()
    name = name.strip()
    clean_name = name.replace(" ", "_")
    makedirs(f"imgs/{clean_name}", exist_ok=True)
    base = requests.get(url)
    base.close()
    soup = BS(base.content, "html.parser")
    pages = soup.select("center center div img")
    num_pages = len(pages) - 1
    page_num = 0
    stored_page_paths = []
    for page in pages:
        print(make_status_string(Status.DOWNLOADING, 0, name, page_num, num_pages), end="\r")
        with requests.Session():
            response = requests.get(page["src"])
        fname = f"imgs/{clean_name}/{page_num}.jpg"
        with open(fname, "wb") as page_file:
            page_file.write(response.content)
        stored_page_paths.append(fname)
        page_num += 1

    images: list[Image.Image] = []
    to_rotate_imgs = []
    for i, path in enumerate(stored_page_paths):
        img = Image.open(path)
        images.append(img)
        if img.width > img.height:
            to_rotate_imgs.append(i)
    
    # Check aspect ratio
    if images:
        width_a = images[0].width
        height_a = images[0].height
        aspect_ratio = width_a / height_a
        global PDF_W, PDF_H
        PDF_W = 210  # A4 width in mm
        PDF_H = PDF_W / aspect_ratio  # Adjust height to maintain aspect ratio
    
    # Removing banners
    for i, img in enumerate(images):
        if img.width == width_a and img.height != height_a:
            images[i] = img.crop((0, 0, img.width, height_a))
        elif img.width != width_a and img.height == height_a:
            images[i] = img.crop((0, 0, width_a, img.height - 50))
    
    # Creating PDF
    pdf = FPDF("P", "mm", (PDF_W, PDF_H))
    for i, img_path in enumerate(stored_page_paths):
        print(make_status_string(Status.ADDING_PAGES, 2, name, i, num_pages), end="\r")
        pdf.add_page()
        pdf.image(img_path, x=0, y=0, w=PDF_W, h=PDF_H)
    
    print(make_status_string(Status.EXPORTING, 3, name, 0, 1), end="\r")
    pdf.output(f"pdfs/{name}.pdf")
    print(make_status_string(Status.COMPLETE, 4, name, 1, 1))

if __name__ == "__main__":
    main()
