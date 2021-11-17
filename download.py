import requests
from fpdf import FPDF
from bs4 import BeautifulSoup as BS
from os import makedirs


def main():
    with open("links.txt","r") as file:
        for entry in file.readlines():
            name,link = entry.split(";")

            handle_entry(url=link, name=name)



def make_progress_bar(current, max):
    perc = (100*current)//max
    return f"[{('|'*perc).ljust(100)}]"



def handle_entry(url:str, name:str):
    url = url.strip()
    name = name.strip()
    print(f"Starting {name}")
    makedirs(f"imgs/{name}", exist_ok=True)
    base = requests.get(url)

    soup = BS(base.content, "html.parser")

    pages = soup.find_all("img",{"width":"1000px"})
    num_pages = len(pages)-1
    page_num = 0
    stored_page_paths = []
    for page in pages:
        print(f"Downloading {str(page_num).rjust(4)}/{str(num_pages).ljust(4)} "+make_progress_bar(page_num,num_pages), end="\r")
        response = requests.get(page["src"])
        fname = f"imgs/{name}/{page_num}.jpg"
        page_file = open(fname,"wb")
        page_file.write(response.content)
        page_file.close()
        stored_page_paths.append(fname)
        page_num += 1

    print()

    print("Now creating pdf")
    pdf = FPDF()
    page_num = 0
    for image in stored_page_paths:
        print(f"Adding page {str(page_num).rjust(4)}/{str(num_pages).ljust(4)} " + make_progress_bar(page_num,num_pages), end="\r")
        pdf.add_page()
        pdf.image(name=image, x=6, y=0,h=297) # 6 is the offset needed to center the image with weird image dimensions provided
        page_num +=1

    print("\n Finishing up...")

    pdf.output(f"pdfs/{name}.pdf")
    print(f"{name} done!")



if( __name__ == "__main__"):
    main()