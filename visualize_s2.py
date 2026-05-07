import configparser
import numpy as np
import os
import cv2


def normalization(s2_image):
    min_value = 0.
    max_values = np.array([0.2, 0.3, 0.3, 0.3, 0.4, 0.4, 0.4, 0.5, 0.5, 0.2, 0.1, 0.3, 0.3])
    s2_image /= 10000
    s2_image = (s2_image - min_value) / (max_values - min_value)

    s2_image[s2_image < 0.] = 0.
    s2_image[s2_image > 1.] = 1.

    return s2_image


configs = configparser.ConfigParser()
configs.read("configs.ini")

no_samples      = 5
s2_rgb_channels = [1, 2, 3]
new_size        = 500

dop_root    = configs['S2'].get('ReferenceDatasetDirectory')
s2_root     = configs['S2'].get('DatasetDirectory')

# Load the images respectively
dop_files   = sorted(os.listdir(dop_root))
s2_files    = sorted(os.listdir(s2_root))
dop_imgs    = [cv2.imread(os.path.join(dop_root, dop_files[i])) for i in range(no_samples)]
s2_imgs     = [np.load(os.path.join(s2_root, s2_files[i])) for i in range(no_samples)]

# Bring S2 in the same shape as DOP20 and extract RGB channels
s2_imgs     = [s2_imgs[i][s2_rgb_channels].transpose(1, 2, 0) for i in range(no_samples)]

# Normalize S2 data and store as int
s2_imgs     = [(np.clip(img, 0, 2000) / 2000 * 255).astype(np.uint8) for img in s2_imgs]

# Resize Images
dop_imgs    = [cv2.resize(img, (new_size, new_size)) for img in dop_imgs]
s2_imgs     = [cv2.resize(img, (new_size, new_size)) for img in s2_imgs]

# Combine them
dop_imgs    = np.hstack(dop_imgs)
s2_imgs     = np.hstack(s2_imgs)
plot        = np.vstack([dop_imgs, s2_imgs])

cv2.imwrite("spoiler.png", plot)
