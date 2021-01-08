#!/usr/bin/env python
# -*- coding: utf-8
# pytest unit tests for spinalcordtoolbox.reports

import pytest
import numpy as np

from spinalcordtoolbox.image import Image
from spinalcordtoolbox.reports.slice import Sagittal


@pytest.fixture(scope="module")
def im_base(path_in=sct_test_path('t2', 't2.nii.gz')):
    # Base anatomical image
    yield Image(path_in)


@pytest.fixture(scope="module")
def im_seg_labeled(path_seg=sct_test_path('t2', 'labels.nii.gz')):
    # Base labeled segmentation
    im_seg = Image(path_seg)
    assert np.count_nonzero(im_seg.data) >= 2, "Labeled segmentation image has fewer than 2 labels"
    yield im_seg


@pytest.fixture(scope="module")
def im_seg_one_label(im_seg_labeled):
    # Create image with all but one label removed
    im_seg_one_label = im_seg_labeled.copy()
    for x, y, z in np.argwhere(im_seg_one_label.data)[1:]:
        im_seg_one_label.data[x, y, z] = 0
    yield im_seg_one_label


@pytest.fixture(scope="module")
def im_seg_no_labels(im_seg_labeled):
    # Create image with no labels
    im_seg_no_labels = im_seg_labeled.copy()
    for x, y, z in np.argwhere(im_seg_no_labels.data):
        im_seg_no_labels.data[x, y, z] = 0
    yield im_seg_no_labels


def labeled_data_test_params():
    """Generate image/label pairs for various test cases of
    test_sagittal_slice_get_center_spit."""
    return [pytest.param('im_base', 'im_seg_labeled', id='multiple_labels'),
            pytest.param('im_base', 'im_seg_one_label', id='one_label'),
            pytest.param('im_base', 'im_seg_no_labels', id='no_labels')]


@pytest.fixture
def im_in(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def im_seg(request):
    return request.getfixturevalue(request.param)


@pytest.mark.parametrize('im_in,im_seg', labeled_data_test_params(), indirect=True)
def test_sagittal_slice_get_center_spit(im_in, im_seg):
    """Test that get_center_split returns a valid index list."""
    assert im_in.orientation == im_seg.orientation, "im_in and im_seg aren't in the same orientation"
    qcslice = Sagittal([im_in, im_seg], p_resample=None)

    if np.count_nonzero(im_seg.data) == 0:
        # If im_seg contains no labels, get_center_spit should fail
        with pytest.raises(ValueError):
            qcslice.get_center_spit()
    else:
        # Otherwise, index list should be n_SI long. (See issue #3087)
        index = qcslice.get_center_spit()
        for i, axis in enumerate(im_in.orientation):
            if axis in ['S', 'I']:
                assert len(index) == im_in.data.shape[i], "Index list doesn't have expected length (n_SI)"