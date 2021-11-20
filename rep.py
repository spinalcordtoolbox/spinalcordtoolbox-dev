#!/usr/bin/env python3

import os
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


_affine_r = array([[ 1.00357811e+00,  1.28000002e-13, -2.61769351e-02,
        -1.94520493e+01],
       [ 1.80669852e-16,  1.00000001e+00,  4.89700023e-12,
        -1.15151794e+02],
       [ 2.62796037e-02, -4.89500042e-12,  9.99657363e-01,
        -1.22996811e+02],
       [ 0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
         1.00000000e+00]])


np.save('affine.npy', affine_r)
os.system('sha256sum affine.npy')
reference = (shape_r, affine_r)

img_r = resample_from_to(img, to_vox_map=reference, order=1, mode='nearest', cval=0.0, out_class=None)

#from pprint import pprint
#pprint(list(img_r.get_data().reshape((-1,)))[:1000])
