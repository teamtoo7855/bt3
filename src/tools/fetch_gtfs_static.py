import requests
import zipfile
import io

def fetch_gtfs_static(dir):
    gtfs_link = 'https://gtfs-static.translink.ca/gtfs/google_transit.zip'
    r = requests.get(gtfs_link)  

    with zipfile.ZipFile(io.BytesIO(r.content)) as zipped_data:
        zipped_data.extractall(dir)