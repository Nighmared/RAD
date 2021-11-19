from enum import Enum

class Status(Enum):
    DOWNLOADING = "Downloading"
    CROPPING = "Cropping"
    ADDING_PAGES = "Adding Pages"
    EXPORTING = "Exporting PDF"
    COMPLETE = "Complete!"

def get_status_length():
    res = 0
    for s in Status:
        res = max(res,len(s.value))
    return res

    
