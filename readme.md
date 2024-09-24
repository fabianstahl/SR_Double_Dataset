# Overview
This repository helps creating a dataset intended for **super resolution** on landscape images. The region
It consists of two sources:

- **DOP-20 Images**: Digital Ortho-Photos with a 20 cm resolution covering the state of Hessia, provided by the [HVBG](https://hvbg.hessen.de/) (Hessische Verwaltung für Bodenmanagement und Geoinformation )
- **S2 Images**: 13-band frequency data from the Sentinel 2 satellite with a 10 meter resolution, provided via the Earth Engine API


# Prerequisites
Install all dependencies using the following command:
```bash
pip install -r requirements
```
Note that you will need approximately **200 GB** of free disk space!


# Configuration
Crawler Parameters can be changed within the configuration file **configs.ini**.


# Download DOP-20 Data
While there is a dedicated WMS API to get DOP-2 tiles, it seems to be broken. Instead, a crawler can be started, to iterate over all regions and their respective municipalities within the [data download center](https://gds.hessen.de/INTERSHOP/web/WFS/HLBG-Geodaten-Site/de_DE/-/EUR/ViewDownloadcenter-Start?path=Luftbildinformationen). It can be executed using the following command:
```bash
python crawler_dop20.py
```
The crawling is divided into several stages:
- Stage 1: Fetch download links to all regions and their respective municipalities. Results are stored to a file, by default called *dop20_regions_metadata.json*. Subsequent crawler executions then use this stored buffer.
- Stage 2: Download data for all municipalities. A folder structure containing the downloaded data is created, by default under *download_data_dop20/*. Note that this step may take several hours!
- Stage 3: Aggregate all images within a single folder


# Download S2 Data
```bash
python crawler_s2.py
```
