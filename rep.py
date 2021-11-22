#!/usr/bin/env python3

import os

os.system("python --version")
os.system("pip freeze")

from numpy import array
import numpy as np
import nibabel
from nibabel.processing import resample_from_to

img = nibabel.load('source/data.nii')

shape_r = (51, 256, 256)

# Generate 3d affine transformation: R
affine = img.affine[:4, :4]
affine[3, :] = np.array([0, 0, 0, 1])  # satisfy to nifti convention. Otherwise it grabs the temporal

R = np.eye(4)
for i in range(3):
    R[i, i] = img.shape[i] / float(shape_r[i])
affine_r = np.dot(affine, R)

np.save('affine.npy', affine_r)
os.system('sha256sum affine.npy')
reference = (shape_r, affine_r)

img_r = resample_from_to(img, to_vox_map=reference, order=1, mode='nearest', cval=0.0, out_class=None)

from pprint import pprint
pprint(list(img_r.get_data().reshape((-1,)))[:1000])
