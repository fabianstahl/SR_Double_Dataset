This repository helps creating a dataset intended for **super resolution** on landscape images. The region
It consists of two sources:

- **DOP-20 Images**: Digital Ortho-Photos with a 20 cm resolution covering the state of Hessia
- **S2 Images**: 13-band frequency data from the Sentinel 2 satellite with a 10 meter resolution


# Prerequisites
Install all dependencies using the following command:
```
pip install -r requirements
```
Note that you will need approximately **200 GB** of free disk space!


# Configuration
Crawler Parameters can be changed within the configuration file **configs.ini**


# Download DOP-20 Data
While there is a dedicated WMS service to get DOP-2 tiles, it seems to be broken. Instead, a crawler can be started, to iterate over all reagions and their respective municipalities within the data download center. It can be executed using the following command:
```
python crawler_dop20.py
```
The crawling is divided into several stages:
- Stage 1: Fetch download links to all regions and their respective municipalities
- Stage 2: Download data for all municipalities
- Stage 3: Aggregate all images within a single folder


# Download S2 Data
```
python crawler_s2.py
```
