# Overview
This repository helps to create a dataset intended for **super resolution** on landscape images. The area of interest covers the German state of Hessia.
The dataset consists of image pairs, respectively with a High Resolution (HR) and a Low Resolution (LR) version, both covering the same area:

- **DOP-20 Images**: Digital Ortho-Photos with a 20 cm resolution covering the state of Hessia, provided by the [HVBG](https://hvbg.hessen.de/) (Hessische Verwaltung für Bodenmanagement und Geoinformation )
- **S2 Images**: 13-band frequency data from the Sentinel 2 satellite with a 10 meter resolution, provided via the Earth Engine API

This plot shows a row of DOP-20 images and their according S2 images below (for visualization only RGB bands).
![image missing](spoiler.png "Sample Data")

# Prerequisites
Install all dependencies using the following command:
```bash
pip install -r requirements
```
Note that you will need approximately **200 GB** of free disk space!


# Configuration
Crawler Parameters can be changed within the configuration file **configs.ini**.
Note that the Sentinel-2 dataset requires a free **[Earth Engine Account](https://code.earthengine.google.com/register)**. Details needs to be assigned in the configuration file before executing the crawler!


# 1) Download DOP-20 Data
While there is a dedicated WMS API to get DOP-2 tiles, it seems to be broken. Instead, a crawler can be started, to iterate over all regions and their respective municipalities within the [data download center](https://gds.hessen.de/INTERSHOP/web/WFS/HLBG-Geodaten-Site/de_DE/-/EUR/ViewDownloadcenter-Start?path=Luftbildinformationen). It can be executed using the following command:
```bash
python crawler_dop20.py
```

The crawling is divided into several stages:
- Stage 1: Fetch download links to all regions and their respective municipalities. Results are stored to a file, by default called *dop20_download_links.json*. Subsequent crawler executions then use this stored buffer.
- Stage 2: Download data for all municipalities. A folder structure containing the downloaded data is created, by default under *download_data_dop20/*. Note that this step may take several hours!
- Stage 3: Aggregating all images within a single folder, defaults to *dataset_dop20/*.
- Stage 4: Download the according metadata PDF file in order to get acquisition dates for each image, so that matching Sentinal images can be found.


# 2) Download S2 Data
The S2 crawler uses Earth Engine, and therefore requires access via a **free account**. Furthermore, the crawler needs to be executed **AFTER** the DOP-20 crawler, since the DOP metadata file is required to filter satellite images by date. This is done in order to minimize the temporal difference between both images.
```bash
python crawler_s2.py
```

Again, crawling is split into several stages:
- Stage 1: Earth Engine Authentication
- Stage 2: Parsing the DOP-20 metadata file to get acquisition dates
- Stage 3: Download matching S2 tiles, by default to *dataset_s2/*


# 3) Clean Up Data
Finally, the following script can be used to clean up the data to ensure uncorrupted HR-LR pairs.
Faulty data is moved to a folder, per default *excluded/*
```bash
python clean_up.py
```

- Stage 1: Remove data without a reference date in the DOP-20 metadata file
- Stage 2: Remove all data pairs with corrupted S2 data
