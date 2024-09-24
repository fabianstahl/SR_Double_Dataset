import configparser
import ee
import json
import numpy as np
import os
import requests
import tqdm
from datetime import datetime, timedelta
from tika import parser as pdf_parser


class Crawler():

    def __init__(self, configs):
        self.configs            = configs
        self.ref_data_dir       = self.configs.get('ReferenceDatasetDirectory')
        self.ref_metadata       = self.configs.get('MetaDataFileName')
        self.ref_date_buffer    = self.configs.get('ReferenceDateBuffer')

    def autheticate(self):
        if os.path.exists(ee.oauth.get_credentials_path()) is False:
            ee.Autenticate()
        else:
            print("Previous Authentication Token found on system!")
        ee.Initialize(project = configs.get('EarthEngineProject'))


    def load_reference_acquisition_dates(self):

        if os.path.exists(self.ref_date_buffer):
            print("Found an existing date buffer under '{}' -> Skipping Parsing".format(self.ref_date_buffer))
            return

        # Get a list of all tiles on disk
        ref_samples = [os.path.join(self.ref_data_dir, f) for f in sorted(os.listdir(self.ref_data_dir))]

        # Parse the metadata PDF and search matching dates
        raw         = pdf_parser.from_file(self.ref_metadata)
        lines       = list(filter(lambda x: x.startswith('DOP20'), raw['content'].split('\n')))

        id_to_date  = {}
        for l in lines:
            # Note: Device name may or may not contain spaces
            id_, date       = l.split()[:2]
            id_             = "{}.jpg".format(id_.lower())
            id_to_date[id_] = date

        file_to_date = {}
        for i, file in enumerate(os.listdir(self.ref_data_dir)):
            if file in id_to_date:
                file_to_date[os.path.join(self.ref_data_dir, file)] = id_to_date[file]
            else:
                print("WARNING: No acquisition date found for file '{}' -> Skipping!".format(file))

        # Dict format:          {file_name: date}
        with open(self.ref_date_buffer, 'w') as f:
            json.dump(file_to_date, f, indent=4, ensure_ascii=False)



    def download_data(self):
        dataset_dir     = self.configs.get('DatasetDirectory')
        if not os.path.exists(dataset_dir):
            os.makedirs(dataset_dir)

        delta_weeks     = self.configs.getint('MaxDeltaWeeks')
        src_proj        = self.configs.get('ReferenceEPSG')
        bands_to_export = self.configs.get('BandsToExport').replace(" ", "").split(',')

        with open(self.ref_date_buffer, 'r') as f:
            ref_file_to_date = json.load(f)

        ref_files       = sorted(ref_file_to_date.keys())
        for ref_file in tqdm.tqdm(ref_files):
            ref_base_name   = os.path.basename(ref_file)
            target_path     = os.path.join(dataset_dir, ref_base_name.replace('.jpg', '.npy'))

            if os.path.exists(target_path):
                continue

            # Define ROI based on EPSG:25832 coordinates
            coords = list(map(float, ref_base_name.split('_')[2:4]))
            tr  = [1000 * coords[0], 1000 * coords[1]]
            tl  = [tr[0], tr[1] + 1000]
            bl  = [tr[0] + 1000, tr[1] + 1000]
            br  = [tr[0] + 1000, tr[1]]
            roi = ee.Geometry.Polygon([tl, tr, br, bl], proj=src_proj, evenOdd=False)

            # Filter Sentinel-2 collection by acquisition time
            date_obj    = datetime.strptime(ref_file_to_date[ref_file], "%d.%m.%Y")
            start_date  = (date_obj - timedelta(weeks=delta_weeks)).strftime("%Y-%m-%d")
            end_date    = (date_obj + timedelta(weeks=delta_weeks)).strftime("%Y-%m-%d")

            sentinel_image = ee.ImageCollection('COPERNICUS/S2_HARMONIZED')\
                .filterBounds(roi)\
                .filterDate(start_date, end_date)\
                .filter(ee.Filter.contains('.geo', roi))\
                .sort('CLOUDY_PIXEL_PERCENTAGE', True)\
                .first()\
                .select(bands_to_export)

            # Reproject the image to EPSG 25832
            projected_image = sentinel_image.reproject(crs=src_proj, scale=10)

            url = projected_image.getDownloadUrl({
                'format': 'NPY',
                'region': roi,
                'crs': src_proj,
                'scale': 10
            })

            response = requests.get(url)

            with open(target_path, 'wb') as fd:
                if response.status_code != 200:
                    print(response.status_code)
                fd.write(response.content)

            img = np.load(target_path)
            img = np.stack([img[b] for b in bands_to_export]).astype(np.float32)
            np.save(target_path, img)



if __name__ == "__main__":

    parser = configparser.ConfigParser()
    parser.read("configs.ini")
    configs = parser['S2']

    crawler = Crawler(configs)

    print("\n== Stage 1/3:\tAuthenticate to Earth Engine ==")
    crawler.autheticate()

    print("\n== Stage 2/3:\tLoad Acquisition Dates of the DOP-20 reference images ==")
    crawler.load_reference_acquisition_dates()

    print("\n== Stage 3/3:\tDownloading Data ==")
    crawler.download_data()

    print("\n== Done! ==")
