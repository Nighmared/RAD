#! /usr/bin/env python3
import requests
from fpdf import FPDF
from bs4 import BeautifulSoup as BS
from os import makedirs
from PIL import Image
from typing import List
from typing import Tuple


DEBUG = False

def main():
    try:
        with open("links.txt", "r") as file:
            makedirs("pdfs", exist_ok=True)
            i = 0
            for entry in (lines:=file.readlines()):
                name, link = entry.split(";")
                handle_entry(url=link, name=name)
                i+=1
                print(f"{i}/{len(lines)} done.")
            if i==0:
                print("No entries in 'links.txt'. Did nothing.")
    except FileNotFoundError:
        open("links.txt",'w').close()
        print("Can't find the 'links.txt' file. I created one for you. Make sure to fill it with entries!")

def make_progress_bar(current, max):
    perc = (50 * current) // max
    return f"[{('|'*perc).ljust(50)}]"


def handle_entry(url: str, name: str):
    url = url.strip()
    name = name.strip()
    print(f"Starting {name}")
    makedirs(f"imgs/{name}", exist_ok=True)
    base = requests.get(url)
    soup = BS(base.content, "html.parser")
    pages = soup.find_all("img", {"width": "1000px"})
    num_pages = len(pages) - 1
    page_num = 0
    stored_page_paths = []
    for page in pages:
        print(
            f"Downloading {str(page_num).rjust(4)}/{str(num_pages).ljust(4)} "
            + make_progress_bar(page_num, num_pages),
            end="\r",
        )
        response = requests.get(page["src"])
        fname = f"imgs/{name}/{page_num}.jpg"
        page_file = open(fname, "wb")
        page_file.write(response.content)
        page_file.close()
        stored_page_paths.append(fname)
        page_num += 1
    print("\nLet's lose those stupid banners...")
    to_rotate_imgs = []
    images: List[Tuple[Image.Image, int]] = []
    for i in range(0, len(stored_page_paths)):
        fname = stored_page_paths[i]
        images.append((img:=Image.open(fname), i))
        if img.width>img.height:
            to_rotate_imgs.append(i)
    assert len(images) >= 2  # i mean come on
    height_a = images[1][0].height
    width_a = images[1][0].width
    i = 0
    while i<len(images) and ((wdiff:=abs(images[i][0].width - width_a))<30 or wdiff>100) and ((hdiff:=abs(images[i][0].height - height_a))<50 or hdiff>200):
        i += 1

    # either the the pages with banners are higher and just have a 100px banner added to the bottom
    # or the width has changed and a 50px high banner is added at the bottom and the comic page just 
    # 'zoomed' out
    if DEBUG:
        print(images[i][1],images[i][0].size)
        print(width_a,height_a,wdiff)
    if width_a == images[i][0].width: # so the height changed
        height_b = images[i][0].height
        actual_height = min(height_a, height_b)
        banner_height = max(height_a, height_b)
        assert actual_height != banner_height  # please
        crop_count = 0
        for image, indx in images:
            if indx in to_rotate_imgs: continue
            print(f"Iterating & Cropping  {make_progress_bar(indx,num_pages)}", end="\r")
            if image.height == banner_height:
                crop_count += 1
                image = image.crop((0, 0, image.width, actual_height))
                fname = stored_page_paths[indx]
                image.save(fname)
            image.close()
        print(f"\nCropped {crop_count} images!".ljust(72))
    elif height_a == images[i][0].height: # so the width changed
        # here banner is at bottom and 50px high!!
        width_b = images[i][0].width
        banner_height = 50
        banner_width = min(width_a,width_b)
        crop_count = 0
        for image,indx in images:
            if indx in to_rotate_imgs: continue
            print(f"Iterating & Cropping  {make_progress_bar(indx,num_pages)}", end="\r")
            if image.width == banner_width:
                crop_count += 1
                image = image.crop((0,0,image.width,image.height-banner_height))
                fname = stored_page_paths[indx]
                image.save(fname)
            image.close()
        print(f"\nCropped {crop_count} images!")
    else:
        for image,_ in images:
            image.close()
        print("Nothing to crop...")


    print("Now creating pdf")

    pdf = FPDF("P", "mm", (200, 300)) #basically any numbers that end up with 3:2 ratio
    page_num = 0
    for i in range(0,len(stored_page_paths)):
        image = stored_page_paths[i]
        print(
            f"Adding page {str(page_num).rjust(4)}/{str(num_pages).ljust(4)} "
            + make_progress_bar(page_num, num_pages),
            end="\r",
        )
        if(i in to_rotate_imgs):
            if DEBUG: print(i)
            pdf.add_page(orientation="L")
            pdf.image(
            name=image, x=0, y=0, h=200
        ) 
        else:
            pdf.add_page()
            pdf.image(
                name=image, x=0, y=0, h=300
            ) 
        page_num += 1
    print("\nFinishing up...",end="\r")
    pdf.output(f"pdfs/{name}.pdf")

    print(f"{name} complete!".ljust(20))


if __name__ == "__main__":
    main()
