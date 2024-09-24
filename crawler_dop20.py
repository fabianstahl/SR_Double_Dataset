import configparser
from selenium import webdriver
from bs4 import BeautifulSoup
import tqdm
import requests, zipfile, io
import json
import os

URL_ROOT            = "https://gds.hessen.de/"

class Crawler():

    def __init__(self, configs):
        self.configs        = configs

        self.buffer_path    = self.configs.get('RegionMetaDataBuffer')
        self.download_dir   = self.configs.get('DownloadDirectory')

    def fetch_download_links(self):
        if os.path.exists(self.buffer_path):
            print("Found an existing metadata buffer under '{}' -> Skipping fetching regions".format(self.buffer_path))
        else:
            results = self.fetch_regions()
            with open(self.buffer_path, 'w') as f:
                json.dump(results, f, indent=4, ensure_ascii=False)


    def fetch_regions(self):
        self.driver = webdriver.Chrome()
        self.driver.get(self.configs.get('URLDownloadCenter'))
        soup    = BeautifulSoup(self.driver.page_source, "html.parser")
        elems   = soup.find_all('span', 'subnav__wrapper subnav__wrapper--level-3 subnav__wrapper--sub')

        regions = {}
        for x in elems:
            link_elem       = x.find("a", class_="subnav__link")
            region          = link_elem.get_text()
            link            = link_elem.get('href')
            regions[region] = link

        print("Found '{}' regions".format(len(regions)))
        [print("\t- {}".format(r)) for r in sorted(regions.keys())]

        # For each region find all municipalities
        download_data = {}
        for r_no, region in enumerate(regions.keys()):
            download_data[region] = self.fetch_municipalities(region)
            print("#{}/{}: Found '{}' municipalities in region '{}'".format(r_no, len(regions), len(download_data[region]), region))

        # Dict Format: {'region:' {'municipality': 'municipality_url' }}
        return download_data


    def fetch_municipalities(self, region):
        metadata            = {}
        page_no             = 1
        retries             = 0
        reached_last_page   = False

        while(True):
            full_url = "{}/{}&page={}".format(self.configs.get('URLDownloadCenter'), region, page_no)
            self.driver.get(full_url)

            soup            = BeautifulSoup(self.driver.page_source, "html.parser")
            data_element    = soup.find_all("div", class_="content-box")

            # Case 1: No Data -> Retry up to MAX_RETRIES times
            if len(data_element) == 0:  #
                if retries < self.configs.getint('MaxRetries'):
                    retries += 1
                else:
                    break

            # Case 2: Got a full page -> Get next Page
            elif len(data_element) == self.configs.getint('MunicipalitiesPerPage'):
                page_no     += 1
                retries     = 0

            # Case 3: Not a full page -> Break after parsing current page
            else:
                page_no             = 1
                retries             = 0
                reached_last_page   = True

            for elem in data_element:
                town            = elem.find("h2").get_text().replace('- DOP20\n', '').lstrip().strip()
                link            = configs.get('BaseURL') + elem.find("a").get('href').replace(' ', '%20')
                metadata[town]  = link

            if reached_last_page:
                break

        # Dict Format: {'municipality': 'municipality_url' }
        return metadata


    def download_municipality(self, region, mun, link):
        full_path = os.path.join(self.download_dir, region, mun)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
        else:
            print("Found region '{}': municipality '{}' -> Skipping".format(region, mun))
            return

        r = requests.get(link)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(full_path)


    def download_data(self):

        with open(self.buffer_path, 'r') as f:
            download_data = json.load(f)

        # Download and unzip all municipalities
        for region in sorted(download_data.keys()):
            pbar = tqdm.tqdm(sorted(download_data[region].keys()))
            for mun in pbar:
                pbar.set_description("Downloading '{} : {}'".format(region, mun))
                self.download_municipality(region, mun, download_data[region][mun])


    def aggregate_data(self):
        dataset_dir     = self.configs.get('DatasetDirectory')
        if not os.path.exists(dataset_dir):
            os.makedirs(dataset_dir)

        download_dir    = self.configs.get('DownloadDirectory')
        for region in os.path.listdir(download_dir):
            region_path = os.path.join(download_dir, region)
            for mun in os.path.listdir(region_path):
                mun_path = os.path.join(region_path, mun)
                for file in os.listdir(mun_path):
                    if file.endswith('.jpg'):
                        file_path = os.path.join(mun_path, file)
                        shutil.copy(file_path, dataset_dir)


if __name__ == "__main__":

    parser = configparser.ConfigParser()
    parser.read("configs.ini")
    configs = parser['DOP20']

    crawler = Crawler(configs)

    print("\n== Stage 1/3:\tFetching Regions and their respective Municipality Download Links ==")
    crawler.fetch_download_links()

    print("\n== Stage 2/3:\tDownloading Data ==")
    crawler.download_data()

    print("\n== Stage 3/3:\tAggregate Data ==")
    crawler.aggregate_data()
    #c.start()
