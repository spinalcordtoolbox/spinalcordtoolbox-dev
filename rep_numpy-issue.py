#!/usr/bin/env python3

import sys, numpy; print(numpy.__version__, sys.version)

import numpy as np

array1 = np.load('array1.npy')
array2 = np.load('array2.npy')
array_dot = array1.dot(array2)

# Test against the "failing" dot product
array_fail = np.load('result-fail.npy')
print(f"Matches cached 'fail' array: {np.array_equal(array_dot, array_fail)}")

# Test against the "passing" dot product
array_pass = np.load('result-pass.npy')
print(f"Matches cached 'pass' array: {np.array_equal(array_dot, array_pass)}")

# On Xeon(R) Platinum 8370C, array_dot should match array_fail, so the tests will fail
# On Xeon(R) Platinum 8171M, array_dot should match array_pass, so the tests will pass