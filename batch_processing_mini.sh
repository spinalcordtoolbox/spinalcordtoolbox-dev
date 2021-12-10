#!/bin/bash
#
# Example of commands to process multi-parametric data of the spinal cord.
#
# Please note that this batch script has a lot of redundancy and should not
# be used as a pipeline for regular processing. For example, there is no need
# to process both t1 and t2 to extract CSA values.
#
# For information about acquisition parameters, see: https://osf.io/wkdym/
# N.B. The parameters are set for these type of data. With your data, parameters
# might be slightly different.
#
# Usage:
#
#   [option] $SCT_DIR/batch_processing.sh
#
#   Prevent (re-)downloading sct_example_data:
#   SCT_BP_DOWNLOAD=0 $SCT_DIR/batch_processing.sh
#
#   Specify quality control (QC) folder (Default is ~/qc_batch_processing):
#   SCT_BP_QC_FOLDER=/user/toto/my_qc_folder $SCT_DIR/batch_processing.sh

# Abort on error
set -ve

# For full verbose, uncomment the next line
# set -x

# Fetch OS type
if uname -a | grep -i  darwin > /dev/null 2>&1; then
  # OSX
  open_command="open"
elif uname -a | grep -i  linux > /dev/null 2>&1; then
  # Linux
  open_command="xdg-open"
fi

# Check if users wants to use his own data
if [[ -z "$SCT_BP_DOWNLOAD" ]]; then
	SCT_BP_DOWNLOAD=1
fi

# QC folder
if [[ -z "$SCT_BP_QC_FOLDER" ]]; then
	SCT_BP_QC_FOLDER=`pwd`/"qc_example_data"
fi

# Remove QC folder
if [ -z "$SCT_BP_NO_REMOVE_QC" -a -d "$SCT_BP_QC_FOLDER" ]; then
  echo "Removing $SCT_BP_QC_FOLDER folder."
  rm -rf "$SCT_BP_QC_FOLDER"
fi

# get starting time:
start=`date +%s`

# download example data
if [[ "$SCT_BP_DOWNLOAD" == "1" ]]; then
  sct_download_data -d sct_example_data
fi
cd sct_example_data

# T2
###############################################################################
# Register T2 image to template (used to initialize MT and DMRI registrations)
cd t2
sct_deepseg_sc -i t2.nii.gz -c t2 -qc "$SCT_BP_QC_FOLDER"
sct_label_vertebrae -i t2.nii.gz -s t2_seg.nii.gz -c t2 -qc "$SCT_BP_QC_FOLDER"
sct_label_utils -i t2_seg_labeled.nii.gz -vert-body 2,5 -o labels_vert.nii.gz
sct_register_to_template -i t2.nii.gz -s t2_seg.nii.gz -l labels_vert.nii.gz -c t2 -qc "$SCT_BP_QC_FOLDER"
sct_warp_template -d t2.nii.gz -w warp_template2anat.nii.gz -a 0

## MT
################################################################################
#cd ../mt
## Preprocess MT1 image
#sct_get_centerline -i mt1.nii.gz -c t2
#sct_create_mask -i mt1.nii.gz -p centerline,mt1_centerline.nii.gz -size 45mm
#sct_crop_image -i mt1.nii.gz -m mask_mt1.nii.gz -o mt1_crop.nii.gz
#sct_deepseg_sc -i mt1_crop.nii.gz -c t2 -qc "$SCT_BP_QC_FOLDER"
## Register MT0 to MT1 and get MTR image
#sct_register_multimodal -i mt0.nii.gz -d mt1_crop.nii.gz -dseg mt1_crop_seg.nii.gz -param step=1,type=im,algo=rigid,slicewise=1,metric=CC -x spline -qc "$SCT_BP_QC_FOLDER"
#sct_compute_mtr -mt0 mt0_reg.nii.gz -mt1 mt1_crop.nii.gz
## Register template to MT (using T2 reg to initialize) then get MTR in registered WM
#sct_register_multimodal -i $SCT_DIR/data/PAM50/template/PAM50_t2.nii.gz -iseg $SCT_DIR/data/PAM50/template/PAM50_cord.nii.gz -d mt1_crop.nii.gz -dseg mt1_crop_seg.nii.gz -param step=1,type=seg,algo=slicereg,smooth=3:step=2,type=seg,algo=bsplinesyn,slicewise=1,iter=3 -initwarp ../t2/warp_template2anat.nii.gz -initwarpinv ../t2/warp_anat2template.nii.gz -owarp warp_template2mt.nii.gz -owarpinv warp_mt2template.nii.gz
#sct_warp_template -d mt1_crop.nii.gz -w warp_template2mt.nii.gz -qc "$SCT_BP_QC_FOLDER"
## Compute MTR in WM
#sct_extract_metric -i mtr.nii.gz -method map -o mtr_in_wm.csv -l 51 -vert 2:5
#
## DMRI
################################################################################
#cd ../dmri
## Preprocess DMRI image
#sct_maths -i dmri.nii.gz -mean t -o dmri_mean.nii.gz
#sct_register_multimodal -i ../t2/t2_seg.nii.gz -d dmri_mean.nii.gz -identity 1 -x nn
#sct_create_mask -i dmri_mean.nii.gz -p centerline,t2_seg_reg.nii.gz -size 35mm
#sct_crop_image -i dmri.nii.gz -m mask_dmri_mean.nii.gz -o dmri_crop.nii.gz
#sct_dmri_moco -i dmri_crop.nii.gz -bvec bvecs.txt
#sct_deepseg_sc -i dmri_crop_moco_dwi_mean.nii.gz -c dwi -qc "$SCT_BP_QC_FOLDER"
## Register template to DMRI image
#sct_register_multimodal -i $SCT_DIR/data/PAM50/template/PAM50_t1.nii.gz -iseg $SCT_DIR/data/PAM50/template/PAM50_cord.nii.gz -d dmri_crop_moco_dwi_mean.nii.gz -dseg dmri_crop_moco_dwi_mean_seg.nii.gz -param step=1,type=seg,algo=centermass:step=2,type=seg,algo=bsplinesyn,metric=MeanSquares,smooth=1,iter=3 -initwarp ../t2/warp_template2anat.nii.gz -initwarpinv ../t2/warp_anat2template.nii.gz -qc "$SCT_BP_QC_FOLDER" -owarp warp_template2dmri.nii.gz -owarpinv warp_dmri2template.nii.gz
#sct_warp_template -d dmri_crop_moco_dwi_mean.nii.gz -w warp_template2dmri.nii.gz -qc "$SCT_BP_QC_FOLDER"
## Compute FA in CST
#sct_dmri_compute_dti -i dmri_crop_moco.nii.gz -bval bvals.txt -bvec bvecs.txt
#sct_extract_metric -i dti_FA.nii.gz -z 2:14 -method wa -l 4,5 -o fa_in_cst.csv
#
#
## Display results (to easily compare integrity across SCT versions)
## ===========================================================================================
#set +v
#end=`date +%s`
#runtime=$((end-start))
#echo "~~~"  # these are used to format as code when copy/pasting in github's markdown
#echo "Version:         `sct_version`"
#echo "Ran on:          `uname -nsr`"
#echo "Duration:        $(($runtime / 3600))hrs $((($runtime / 60) % 60))min $(($runtime % 60))sec"
#echo "---"
## The file `test_batch_processing.py` will output tested values when run as a script
#"$SCT_DIR"/python/envs/venv_sct/bin/python "$SCT_DIR"/testing/batch_processing/test_batch_processing.py
#echo "~~~"
#
## Display syntax to open QC report on web browser
#echo "To open Quality Control (QC) report on a web-browser, run the following:"
#echo "$open_command $SCT_BP_QC_FOLDER/index.html"
