#!/usr/bin/env python3

import numpy as np

def print_(name, array):
    import os
    print(f"{name} =", array)
    if isinstance(array, np.ndarray):
        print(f"{name}.shape =", array.shape)
        print(f"{name}.dtype =", array.dtype)
        np.save(f"{name}.npy", array)
        os.system(f"sha256sum {name}.npy")
        import sys, time
        sys.stdout.flush()
        time.sleep(0.1)


to_vox2from_vox_1 = np.load('to_vox2from_vox_1.npy')
print_("to_vox2from_vox_1", to_vox2from_vox_1)

a_to_affine = np.load('a_to_affine.npy')
print_("a_to_affine", a_to_affine)

to_vox2from_vox = to_vox2from_vox_1.dot(a_to_affine)
print_("to_vox2from_vox", to_vox2from_vox)

