#!/bin/sh

# debug https://github.com/spinalcordtoolbox/spinalcordtoolbox/blob/974e1ab1e4c381421189afee7d8ba75dd7c654ff/batch_processing.sh#L79
# this is pretty fragile: call it as ./isolate2.sh from the root of SCT's git repo

if [ -z "$1" ]; then
  #
  for i in `seq 1`; do
    mkdir -p sink-$i
    ( cd sink-$i 
    # recurse into ourselves, so we can have script(1) record the output
    script -c "../$0 sink-$i" log.txt
    find -type f -name "*.gz" | while read nifti; do gunzip "$nifti" && gzip -1n "${nifti%%.gz}"; done # normalize .gz timestamps to 0
    );
  done
else
   time sct_register_to_template -i ../source/t2.nii.gz -s ../source/t2_seg.nii.gz -l ../source/labels_vert.nii.gz -c t2
fi

