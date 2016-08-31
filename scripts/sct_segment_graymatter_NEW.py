#!/usr/bin/env python
########################################################################################################################
#
#
# Gray matter segmentation - new implementation
#
# ----------------------------------------------------------------------------------------------------------------------
# Copyright (c) 2014 Polytechnique Montreal <www.neuro.polymtl.ca>
# Author: Sara Dupont
# Modified: 2016-06-14
#
# About the license: see the file LICENSE.TXT
########################################################################################################################
from msct_multiatlas_seg_NEW import Param, ParamData, ParamModel, Model
from msct_gmseg_utils_NEW import pre_processing, register_data, apply_transfo, normalize_slice, average_gm_wm
from sct_utils import printv, tmp_create, extract_fname, add_suffix
from sct_image import set_orientation
from msct_image import Image
from msct_parser import *
from math import exp
import numpy as np
import shutil, os, sys


def get_parser():
    # Initialize the parser
    parser = Parser(__file__)
    parser.usage.set_description('Segmentation of the white and gray matter.'
                                 ' The segmentation is based on a multi-atlas method that uses a dictionary of pre-segmented gray matter images (already included in SCT) and finds the most similar images for identifying the gray matter using label fusion approach. The model used by this method contains: a template of the white/gray matter segmentation along the cervical spinal cord, and a PCA reduced space to describe the variability of intensity in that template.'
                                 ' This method was inspired from [Asman et al., Medical Image Analysis 2014] and features the following additions:\n'
                                 '- possibility to add information from vertebral levels for improved accuracy\n'
                                 '- intensity normalization of the image to segment (allows the segmentation of any kind of contrast)\n'
                                 '- pre-registration based on non-linear transformations')
    parser.add_option(name="-i",
                      type_value="file",
                      description="Image to segment",
                      mandatory=True,
                      example='t2star.nii.gz')
    parser.add_option(name="-s",
                      type_value="file",
                      description="Spinal cord segmentation",
                      mandatory=True,
                      example='sc_seg.nii.gz')
    parser.add_option(name="-vertfile",
                      type_value="file",
                      description='Labels of vertebral levels. This could either be an image (e.g., label/template/PAM50_levels.nii.gz) or a text file that specifies "slice,level" at each line. Example:\n'
                      "0,3\n"
                      "1,3\n"
                      "2,4\n"
                      "3,4\n"
                      "4,4",
                      mandatory=False,
                      example='label/template/PAM50_levels.nii.gz')
    parser.add_option(name="-vert",
                      mandatory=False,
                      deprecated_by='-vertfile')
    parser.add_option(name="-l",
                      mandatory=False,
                      deprecated_by='-vertfile')

    parser.usage.addSection('SEGMENTATION OPTIONS')
    parser.add_option(name="-denoising",
                      type_value='multiple_choice',
                      description="1: Adaptative denoising from F. Coupe algorithm, 0: no  WARNING: It affects the model you should use (if denoising is applied to the target, the model should have been coputed with denoising too",
                      mandatory=False,
                      default_value=int(ParamData().denoising),
                      example=['0', '1'])
    parser.add_option(name="-normalization",
                      type_value='multiple_choice',
                      description="Normalization of the target image's intensity using median intensity values of the WM and the GM, recomended with MT images or other types of contrast than T2*",
                      mandatory=False,
                      default_value=int(ParamData().normalization),
                      example=['0', '1'])
    # parser.add_option(name="-medians",
    #                   type_value=[[','], 'float'],
    #                   description="Median intensity values in the target white matter and gray matter (separated by a comma without white space)\n"
    #                               "If not specified, the mean intensity values of the target WM and GM  are estimated automatically using the dictionary average segmentation by level.\n"
    #                               "Only if the -normalize flag is used",
    #                   mandatory=False,
    #                   default_value=None,
    #                   example=["450,540"])
    parser.add_option(name="-w-levels",
                      type_value='float',
                      description="weight parameter on the level differences to compute the similarities",
                      mandatory=False,
                      default_value=ParamSeg().weight_level,
                      example=2.0)
    parser.add_option(name="-w-coordi",
                      type_value='float',
                      description="weight parameter on the euclidean distance (based on images coordinates in the reduced sapce) to compute the similarities ",
                      mandatory=False,
                      default_value=ParamSeg().weight_coord,
                      example=0.005)
    parser.add_option(name="-thr-sim",
                      type_value='float',
                      description="Threshold to select the dictionary slices most similar to the slice to segment (similarities are normalized to 1)",
                      mandatory=False,
                      default_value=ParamSeg().thr_similarity,
                      example=0.6)
    parser.add_option(name="-model",
                      type_value="folder",
                      description="Path to the computed model",
                      mandatory=False,
                      example='/home/jdoe/gm_seg_model/')
    parser.usage.addSection('\nOUTPUT OTIONS')
    parser.add_option(name="-res-type",
                      type_value='multiple_choice',
                      description="Type of result segmentation : binary or probabilistic",
                      mandatory=False,
                      default_value=ParamSeg().type_seg,
                      example=['bin', 'prob'])
    # parser.add_option(name="-ratio",
    #                   type_value='multiple_choice',
    #                   description="Compute GM/WM ratio by slice or by vertebral level (average across levels)",
    #                   mandatory=False,
    #                   default_value='0',
    #                   example=['0', 'slice', 'level'])
    parser.add_option(name="-ofolder",
                      type_value="folder_creation",
                      description="Output folder",
                      mandatory=False,
                      default_value=ParamSeg().path_results,
                      example='gm_segmentation_results/')
    # parser.add_option(name="-ref",
    #                   type_value="file",
    #                   description="Reference segmentation of the gray matter for segmentation validation (outputs Dice coefficient and Hausdoorff's distance)",
    #                   mandatory=False,
    #                   example='manual_gm_seg.nii.gz')
    parser.usage.addSection('MISC')
    # parser.add_option(name='-qc',
    #                   type_value='multiple_choice',
    #                   description='Output images for quality control.',
    #                   mandatory=False,
    #                   example=['0', '1'],
    #                   default_value='1')
    parser.add_option(name="-r",
                      type_value="multiple_choice",
                      description='Remove temporary files.',
                      mandatory=False,
                      default_value=str(int(Param().rm_tmp)),
                      example=['0', '1'])
    parser.add_option(name="-v",
                      type_value='multiple_choice',
                      description="verbose: 0 = nothing, 1 = classic, 2 = expended",
                      mandatory=False,
                      example=['0', '1', '2'],
                      default_value=str(Param().verbose))

    return parser




class ParamSeg:
    def __init__(self):
        self.fname_im = None
        self.fname_seg = None
        self.fname_level = None
        self.path_results = './'

        # param to compute similarities:
        self.weight_level = 2.5 # gamma
        self.weight_coord = 0.0065 # tau --> need to be validated for specific dataset
        self.thr_similarity = 0.8 # epsilon but on normalized to 1 similarities (by slice of dic and slice of target)
        # TODO = find the best thr

        self.type_seg = 'prob' # 'prob' or 'bin'


class SegmentGM:
    def __init__(self, param_seg=None, param_model=None, param_data=None, param=None):
        self.param_seg = param_seg if param_seg is not None else ParamSeg()
        self.param_model = param_model if param_model is not None else ParamModel()
        self.param_data = param_data if param_data is not None else ParamData()
        self.param = param if param is not None else Param()

        # create model:
        self.model = Model(param_model=self.param_model, param_data=self.param_data, param=self.param)

        # create tmp directory
        self.tmp_dir = tmp_create(verbose=self.param.verbose) # path to tmp directory

        self.target_im = None # list of slices
        self.info_preprocessing = None # dic containing {'orientation': 'xxx', 'im_sc_seg_rpi': im, 'interpolated_images': [list of im = interpolated image data per slice]}

        self.projected_target = None


    def segment(self):
        self.copy_data_to_tmp()
        # go to tmp directory
        os.chdir(self.tmp_dir)
        # load model
        self.model.load_model()

        printv('\nPre-processing target image ...', self.param.verbose, 'normal')
        self.target_im, self.info_preprocessing = pre_processing(self.param_seg.fname_im, self.param_seg.fname_seg, self.param_seg.fname_level, new_res=self.param_data.axial_res, square_size_size_mm=self.param_data.square_size_size_mm, denoising=self.param_data.denoising, verbose=self.param.verbose, rm_tmp=self.param.rm_tmp)

        printv('\nRegistering target image to model data ...', self.param.verbose, 'normal')
        # register target image to model dictionary space
        path_warp = self.register_target()

        printv('\nNormalizing intensity of target image ...', self.param.verbose, 'normal')
        self.normalize_target()

        printv('\nProjecting target image into the model reduced space ...', self.param.verbose, 'normal')
        self.project_target()

        printv('\nComputing similarities between target slices and model slices using model reduced space ...', self.param.verbose, 'normal')
        list_dic_indexes_by_slice = self.compute_similarities()

        printv('\nDoing label fusion of model slices most similar to target slices ...', self.param.verbose, 'normal')
        self.label_fusion(list_dic_indexes_by_slice)

        printv('\nWarping back segmentation into image space...', self.param.verbose, 'normal')
        self.warp_back_seg(path_warp)
        im_res_gmseg, im_res_wmseg = self.post_processing()

        # go back to original directory
        os.chdir('..')
        printv('\nSaving result GM and WM segmentation...', self.param.verbose, 'normal')
        fname_res_gmseg = self.param_seg.path_results+add_suffix(''.join(extract_fname(self.param_seg.fname_im)[1:]), '_gmseg')
        fname_res_wmseg = self.param_seg.path_results+add_suffix(''.join(extract_fname(self.param_seg.fname_im)[1:]), '_wmseg')

        im_res_gmseg.setFileName(fname_res_gmseg)
        im_res_wmseg.setFileName(fname_res_wmseg)

        im_res_gmseg.save()
        im_res_wmseg.save()

        printv('\n--> To visualize the results, write:\n'
               'fslview '+self.param_seg.fname_im+' '+fname_res_gmseg+' -b 0.4,1 -l Red-Yellow '+fname_res_wmseg+' -b 0.4,1 -l Blue-Lighblue ', self.param.verbose, 'info')


    def copy_data_to_tmp(self):
        # copy input image
        if self.param_seg.fname_im is not None:
            shutil.copy(self.param_seg.fname_im, self.tmp_dir)
            self.param_seg.fname_im = ''.join(extract_fname(self.param_seg.fname_im)[1:])
        else:
            printv('ERROR: No input image', self.param.verbose, 'error')

        # copy sc seg image
        if self.param_seg.fname_seg is not None:
            shutil.copy(self.param_seg.fname_seg, self.tmp_dir)
            self.param_seg.fname_seg = ''.join(extract_fname(self.param_seg.fname_seg)[1:])
        else:
            printv('ERROR: No SC segmentation image', self.param.verbose, 'error')

        # copy level file
        if self.param_seg.fname_level is not None:
            shutil.copy(self.param_seg.fname_level, self.tmp_dir)
            self.param_seg.fname_level = ''.join(extract_fname(self.param_seg.fname_level)[1:])

    def register_target(self):
        # create dir to store warping fields
        path_warping_fields = 'warp_target/'
        if not os.path.exists(path_warping_fields):
            os.mkdir(path_warping_fields)

        # get destination image
        im_dest = Image(self.model.mean_image)

        for target_slice in self.target_im:
            im_src = Image(target_slice.im)
            # register slice image to mean dictionary image
            im_src_reg, fname_src2dest, fname_dest2src = register_data(im_src, im_dest, param_reg=self.param_data.register_param, path_copy_warp=path_warping_fields, rm_tmp=self.param.rm_tmp)

            # rename warping fields
            fname_src2dest_slice = 'warp_target_slice'+str(target_slice.id)+'2dic.nii.gz'
            fname_dest2src_slice = 'warp_dic2target_slice' + str(target_slice.id) + '.nii.gz'
            shutil.move(path_warping_fields+fname_src2dest, path_warping_fields+fname_src2dest_slice)
            shutil.move(path_warping_fields+fname_dest2src, path_warping_fields+fname_dest2src_slice)

            # set moved image
            target_slice.set(im_m=im_src_reg.data)

        return path_warping_fields

    def normalize_target(self):
        # get gm seg from model by level
        gm_seg_model, wm_seg_model = self.model.get_gm_wm_by_level()

        # for each target slice: normalize
        for target_slice in self.target_im:
            level_int = int(round(target_slice.level))
            norm_im_M = normalize_slice(target_slice.im_M, gm_seg_model[level_int], wm_seg_model[level_int], self.model.intensities['GM'][level_int], self.model.intensities['WM'][level_int],min=self.model.intensities['MIN'][level_int], max=self.model.intensities['MAX'][level_int])
            target_slice.set(im_m=norm_im_M)

    def project_target(self):
        projected_target_slices = []
        for target_slice in self.target_im:
            # get slice data in the good shape
            slice_data = target_slice.im_M.flatten()
            slice_data = slice_data.reshape(1, -1) # data with single sample
            # project slice data into the model
            slice_data_projected = self.model.fitted_model.transform(slice_data)
            projected_target_slices.append(slice_data_projected)
        # store projected target slices
        self.projected_target = projected_target_slices

    def compute_similarities(self):
        list_dic_indexes_by_slice = []
        for i, target_coord in enumerate(self.projected_target):
            list_dic_similarities = []
            for j, dic_coord in enumerate(self.model.fitted_data):
                # compute square norm using coordinates in the model space
                square_norm = np.linalg.norm((target_coord - dic_coord), 2)
                # compute similarity with or without levels
                if self.param_seg.fname_level is not None:
                    # EQUATION WITH LEVELS
                    similarity = exp(-self.param_seg.weight_level * abs(self.target_im[i].level - self.model.slices[j].level)) * exp(-self.param_seg.weight_coord * square_norm)
                else:
                    # EQUATION WITHOUT LEVELS
                    similarity = exp(-self.param_seg.weight_coord * square_norm)
                # add similarity to list
                list_dic_similarities.append(similarity)
            list_norm_similarities =  [float(s)/sum(list_dic_similarities) for s in list_dic_similarities]
            # select indexes of most similar slices
            list_dic_indexes = []
            for j, norm_sim in enumerate(list_norm_similarities):
                if norm_sim >= self.param_seg.thr_similarity:
                    list_dic_indexes.append(j)
            # save list of indexes into list by slice
            list_dic_indexes_by_slice.append(list_dic_indexes)

        return list_dic_indexes_by_slice

    def label_fusion(self, list_dic_indexes_by_slice):
        for target_slice in self.target_im:
            # get list of slices corresponding to the indexes
            list_dic_slices = [self.model.slices[j] for j in list_dic_indexes_by_slice[target_slice.id]]
            # average slices GM and WM
            data_mean_gm, data_mean_wm = average_gm_wm(list_dic_slices)
            if self.param_seg.type_seg == 'bin':
                # binarize GM seg
                data_mean_gm[data_mean_gm >= 0.5] = 1
                data_mean_gm[data_mean_gm < 0.5] = 0
                # binarize WM seg
                data_mean_wm[data_mean_wm >= 0.5] = 1
                data_mean_wm[data_mean_wm < 0.5] = 0
            # store segmentation into target_im
            target_slice.set(gm_seg_m=data_mean_gm, wm_seg_m=data_mean_wm)

    def warp_back_seg(self, path_warp):
        for target_slice in self.target_im:
            fname_dic_space2slice_space = path_warp+'/warp_dic2target_slice' + str(target_slice.id) + '.nii.gz'
            im_dest = Image(target_slice.im)
            interpolation = 'nn' if self.param_seg.type_seg == 'bin' else 'linear'
            # warp GM
            im_src_gm = Image(target_slice.gm_seg_M)
            im_src_gm_reg = apply_transfo(im_src_gm, im_dest, fname_dic_space2slice_space, interp=interpolation, rm_tmp=self.param.rm_tmp)
            # warp WM
            im_src_wm = Image(target_slice.wm_seg_M)
            im_src_wm_reg = apply_transfo(im_src_wm, im_dest, fname_dic_space2slice_space, interp=interpolation, rm_tmp=self.param.rm_tmp)
            # set slice attributes
            target_slice.set(gm_seg=im_src_gm_reg.data, wm_seg=im_src_wm_reg.data)

    def post_processing(self):
        ## DO INTERPOLATION BACK TO ORIGINAL IMAGE
        # get original SC segmentation oriented in RPI
        im_sc_seg_original_rpi = self.info_preprocessing['im_sc_seg_rpi'].copy()
        # create res GM seg image
        im_res_gmseg = im_sc_seg_original_rpi.copy()
        im_res_gmseg.data = np.zeros(im_res_gmseg.data.shape)
        # create res WM seg image
        im_res_wmseg = im_sc_seg_original_rpi.copy()
        im_res_wmseg.data = np.zeros(im_res_wmseg.data.shape)

        for iz, im_iz_preprocessed in enumerate(self.info_preprocessing['interpolated_images']):
            # im gmseg for slice iz
            im_gmseg = im_iz_preprocessed.copy()
            im_gmseg.data = np.zeros(im_gmseg.data.shape)
            im_gmseg.data = self.target_im[iz].gm_seg

            # im wmseg for slice iz
            im_wmseg = im_iz_preprocessed.copy()
            im_wmseg.data = np.zeros(im_wmseg.data.shape)
            im_wmseg.data = self.target_im[iz].wm_seg

            for im_res_slice, im_res_tot in [(im_gmseg, im_res_gmseg), (im_wmseg, im_res_wmseg)]:
                # get physical coordinates of center of square
                sq_size_pix = int(self.param_data.square_size_size_mm/self.param_data.axial_res)
                [[x_square_center_phys, y_square_center_phys, z_square_center_phys]] = im_res_slice.transfo_pix2phys(
                    coordi=[[int(sq_size_pix / 2), int(sq_size_pix / 2), 0]])
                # get physicl coordinates of center of sc
                x_seg, y_seg = (im_sc_seg_original_rpi.data[:, :, iz] > 0).nonzero()
                x_center, y_center = np.mean(x_seg), np.mean(y_seg)
                [[x_center_phys, y_center_phys, z_center_phys]] = im_sc_seg_original_rpi.transfo_pix2phys(
                    coordi=[[x_center, y_center, iz]])
                # set res slice header
                im_res_slice.hdr.as_analyze_map()['qoffset_x'] = im_sc_seg_original_rpi.hdr.as_analyze_map()['qoffset_x'] + x_center_phys - x_square_center_phys
                im_res_slice.hdr.as_analyze_map()['qoffset_y'] = im_sc_seg_original_rpi.hdr.as_analyze_map()['qoffset_y'] + y_center_phys - y_square_center_phys
                im_res_slice.hdr.as_analyze_map()['qoffset_z'] = im_sc_seg_original_rpi.hdr.as_analyze_map()['qoffset_z'] + z_center_phys
                im_res_slice.hdr.set_sform(im_res_slice.hdr.get_qform())
                im_res_slice.hdr.set_qform(im_res_slice.hdr.get_qform())
                # reshape data
                im_res_slice.data = im_res_slice.data.reshape((sq_size_pix, sq_size_pix, 1))
                # interpolate to reference image
                interp = 0 if self.param_seg.type_seg == 'bin' else 1
                im_res_slice_interp = im_res_slice.interpolate_from_image(im_sc_seg_original_rpi, interpolation_mode=interp, border='nearest')
                # set correct slice of total image with this slice
                im_res_tot.data[:, :, iz] = im_res_slice_interp.data[:, :, iz]

        ## PUT RES BACK IN ORIGINAL ORIENTATION
        im_res_gmseg.setFileName('res_gmseg.nii.gz')
        im_res_gmseg.save()
        im_res_gmseg = set_orientation(im_res_gmseg, self.info_preprocessing['orientation'])

        im_res_wmseg.setFileName('res_wmseg.nii.gz')
        im_res_wmseg.save()
        im_res_wmseg = set_orientation(im_res_wmseg, self.info_preprocessing['orientation'])

        return im_res_gmseg, im_res_wmseg


########################################################################################################################
# ------------------------------------------------------  MAIN ------------------------------------------------------- #
########################################################################################################################
if __name__ == "__main__":
    # create param objects
    param_seg = ParamSeg()
    param_data = ParamData()
    param_model = ParamModel()
    param = Param()

    # get parser
    parser = get_parser()
    arguments = parser.parse(sys.argv[1:])

    # set param arguments ad inputted by user
    param_seg.fname_im = arguments["-i"]
    param_seg.fname_seg = arguments["-s"]

    if '-vertfile' in arguments:
        param_seg.fname_level = arguments['-vertfile']
    if '-denoising' in arguments:
        param_data.denoising = arguments['-denoising']
    if '-normalization' in arguments:
        param_data.normalization = arguments['-normalization']
    if '-w-levels' in arguments:
        param_seg.weight_level = arguments['-w-levels']
    if '-w-coordi' in arguments:
        param_seg.weight_coord = arguments['-w-coordi']
    if '-thr-sim' in arguments:
        param_seg.thr_similarity = arguments['-thr-sim']
    if '-model' in arguments:
        param_model.path_model_to_load = arguments['-model']
    if '-res-type' in arguments:
        param_seg.type_seg= arguments['-res-type']
    if '-ofolder' in arguments:
        param_seg.path_results= arguments['-ofolder']
    if '-r' in arguments:
        param.rm_tmp= arguments['-r']
    if '-v' in arguments:
        param.verbose= arguments['-v']

    seg_gm = SegmentGM()
    seg_gm.segment()