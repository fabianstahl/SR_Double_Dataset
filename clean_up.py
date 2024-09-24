import configparser
from datetime import datetime as dt
import json
import numpy as np
import os
import tqdm


class Cleaner:

    def __init__(self, configs):
        self.configs        = configs
        self.excluded_dir   = self.configs['DEFAULT'].get('ExclusionDirectory')


    def exclude_no_date(self):
        excl_dir = os.path.join(self.excluded_dir, 'stage1')
        if not os.path.exists(excl_dir):
            os.makedirs(excl_dir)

        with open(self.configs['S2'].get('ReferenceDateBuffer'), 'r') as f:
            ref_file_to_date = json.load(f)

        dop_data_dir = self.configs['S2'].get('ReferenceDatasetDirectory')
        for file in sorted(os.listdir(dop_data_dir)):
            file_path = os.path.join(dop_data_dir, file)
            if not file_path in ref_file_to_date:
                print("Stage 1: File '{}' has no acquisition date!".format(file))
                shutil.move(file_path, excl_dir)


    def exclude_currupted(self):
        excl_dir = os.path.join(self.excluded_dir, 'stage2')
        if not os.path.exists(excl_dir):
            os.makedirs(excl_dir)

        dop_root    = self.configs['S2'].get('ReferenceDatasetDirectory')
        s2_root     = self.configs['S2'].get('DatasetDirectory')
        s2_bands    = self.configs['S2'].get('BandsToExport').replace(" ", "").split(',')

        ids_to_remove = set()
        for img_path in tqdm.tqdm(sorted(os.listdir(s2_root))):
            full_path   = os.path.join(s2_root, img_path)
            img         = np.load(full_path)

            # Image cannot be opened
            if img is None:
                print("Stage 2: File '{}' could not be opened!".format(img_path))
                ids_to_remove.add(img_path)

            # Image has wrong shape or NaN values
            elif img.shape != (len(s2_bands), 100, 100) or np.isnan(img).any():
                print("Stage 2: File '{}' has the wrong shape or conatins NaN values!".format(img_path))
                ids_to_remove.add(img_path)

        # Move to exluded folder
        for id_ in ids_to_remove:
            shutil.move(os.path.join(s2_root, id_), excl_dir)
            shutil.move(os.path.join(dop_root, id_.replace('.npy', '.jpg')), excl_dir)


    def info(self):

        # 1) Number of samples
        dop_root    = self.configs['S2'].get('ReferenceDatasetDirectory')
        s2_root     = self.configs['S2'].get('DatasetDirectory')
        assert len(os.listdir(dop_root)) == len(os.listdir(s2_root))
        print("Number of HR-LR pairs:\n\t'{}'".format(len(os.listdir(dop_root))))

        # 2) Date Range
        with open(self.configs['S2'].get('ReferenceDateBuffer'), 'r') as f:
            ref_file_to_date = json.load(f)
        dates = set([dt.strptime(v, "%d.%m.%Y") for v in ref_file_to_date.values()])
        print("Date Range of HR pairs:\n\t'{}' - '{}'".format(min(dates), max(dates)))



if __name__ == "__main__":

    parser = configparser.ConfigParser()
    parser.read("configs.ini")

    cleaner = Cleaner(parser)

    print("\n== Stage 1/2:\tRemove DOP-20 tiles without acquisition date ==")
    cleaner.exclude_no_date()

    print("\n== Stage 2/2:\tRemove pairs with corrupted S2 data ==")
    cleaner.exclude_currupted()

    print("\n== Final Dataset Information ==")
    cleaner.info()

    print("\n== Done! ==")
