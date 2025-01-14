def prepare_templates(fpath, tele_autophot_input ,
                      get_fwhm = True,redo_wcs = True,
                      build_psf = True, clean_cosmic = True,
                      solve_field_exe_loc = None, use_lacosmic = False,
                      use_filter = None,  target_ra = None,
                      target_dec = None, search_radius = 0.5, cpu_limit= 180,
                      downsample = 2, threshold_value = 25, ap_size = 1.7,
                      inf_ap_size = 2.5, r_in_size = 2, r_out_size = 3,
                      use_moffat = True, psf_source_no = 10, fitting_method = 'least_sqaure',
                      regrid_size = 10, fitting_radius = 1.3
                      ):
    r'''
    The purpose of this function is specifically tailored towards template
    images and preparing them for use in a dataset. The function deals with the following:

    #. Cosmic Rays cleaning

    #. World Coordinate System (WCS) correction using Astrometry.net

    #. Full Width Half Maximum

    #. Building the Point Spread Function and saving the PSF model.

    The function should used before photometry is performed on a dataset


    :param fpath: Filepath towards *fits* image containing 2D array with overlap with science data.
    :type fpath: str
    :param tele_autophot_input: Telescope infomation. This is a dictionary version of the *telescope.yml*
    :type tele_autophot_input: dict
    :param get_fwhm: Find the FWHM of the template image, defaults to True
    :type get_fwhm: bool, optional
    :param build_psf: Build the PSF function of the template image and save the PSF model, defaults to True
    :type build_psf: bool, optional
    :param clean_cosmic: Perform cosmic ray cleaning on the template image, defaults to True
    :type clean_cosmic: bool, optional
    :param redo_wcs: Redo the WCS values of the image, this is always recommended, defaults to True
    :type redo_wcs: bool, optional
    :param solve_field_exe_loc: Location of *solve-field* executable from astrometry.net, defaults to None
    :type solve_field_exe_loc: str, optional
    :param use_lacosmic: use LaCosmic rather than astroscrappy for cosmic ray cleaning, defaults to False
    :type use_lacosmic: bool, optional
    :param use_filter: Filter of observation of image, defaults to None
    :type use_filter: str, optional
    :param target_ra: Right Asscention of target in degress. This is use to help solve for astrometry, defaults to None
    :type target_ra: float, optional
    :param target_dec: Declination of target in degress. This is use to help solve for astrometry, defaults to None
    :type target_dec: float, optional
    :param search_radius: Search radius around *target_ra* and *target_dec*. This is use to help solve for astrometry defaults to 0.5
    :type search_radius: float, optional
    :param downsample: If working with verty large image arrays, when can pass this value to astrometry.net to downsample the image before runnign through astrometry.net, defaults to 2
    :type downsample: int, optional
    :param threshold_value: Inital threshold value for source detection, defaults to 25
    :type threshold_value: float, optional
    :param ap_size: Multiple of FWHM to be used as standard aperture size, defaults to 1.7
    :type ap_size: float, optional
    :param inf_ap_size: Multiple of FWHM to be used as larger, :math:`\mathit{infinite}` aperture size, defaults to 2.5
    :type inf_ap_size: float, optional
    :param r_in_size: Multiple of FWHM to be used as inner radius of background annulus, defaults to 1.9
    :type r_in_size: float, optional
    :param r_out_size: Multiple of FWHM to be used as outer radius of background annulus, defaults to 2.2
    :type r_out_size: float, optional
    :param use_moffat: If True, use a moffat function as the analytical function, else use a gaussian, defaults to True
    :type use_moffat: bool, optional
    :param psf_source_no: Number of sources used to build PSF model, defaults to 10
    :type psf_source_no: int, optional
    :param fitting_method: Fitting method when fitting the PSF model, defaults to 'least_square'
    :type fitting_method: str, optional
    :param regrid_size: When expanding to larger pseudo-resolution, what zoom factor to use, defaults to 10
    :type regrid_size: int, optional
    :param fitting_radius: zoomed region around location of best fit to focus fitting. This allows for the fitting to be concentrated on high S/N areas and not fit the low S/N wings of the PSF, defaults to 1.3
    :type fitting_radius: float, optional
    :return: This function *OVERWRITES* the given template files and cleans/calibrates this files and saves the for use on science data.
    '''

    import os
    import logging
    from astropy.io import fits
    from autophot.packages.functions import getheader,getimage
    from autophot.packages import psf
    from autophot.packages.aperture import do_aperture_photometry
    from autophot.packages.call_astrometry_net import AstrometryNetLOCAL
    from autophot.packages.check_wcs import updatewcs,removewcs
    from autophot.packages.find import get_fwhm
    from autophot.packages.functions import border_msg

    base = os.path.basename(fpath)
    write_dir = os.path.dirname(fpath)
    base = os.path.splitext(base)[0]

    logger = logging.getLogger(__name__)

    border_msg('Preparing templates files')
    logger.info('Write Directory: %s' % write_dir )


    if base.startswith('PSF_model'):
        logger.info('ignoring PSF_MODEL in file: %s' % base)
        return

    dirpath = os.path.dirname(fpath)

    image = getimage(fpath)
    headinfo = getheader(fpath)

    try:
        telescope = headinfo['TELESCOP']
    except:
        telescope  = 'UNKNOWN'
        headinfo['TELESCOP'] = 'UNKNOWN'

    if telescope  == '':
        telescope  = 'UNKNOWN'
        headinfo['TELESCOP'] = 'UNKNOWN'

    inst_key = 'INSTRUME'
    inst = headinfo[inst_key]



    if 'rdnoise' in tele_autophot_input[telescope][inst_key][inst]:

        rdnoise_key = tele_autophot_input[telescope][inst_key][inst]['rdnoise']

        if rdnoise_key is None:
            rdnoise = 0
        elif rdnoise_key in headinfo:
            rdnoise = headinfo[rdnoise_key]
        else:
            rdnoise = 0

    else:

        logging.info('Read noise key not found for template file')
        rdnoise = 0

    logging.info('Read Noise: %.1f [e^- /pixel]' % rdnoise)


    if 'GAIN' in tele_autophot_input[telescope][inst_key][inst]:

        GAIN_key = tele_autophot_input[telescope][inst_key][inst]['GAIN']

        if GAIN_key is None:
            GAIN = 1
        elif GAIN_key in headinfo:
            GAIN = headinfo[GAIN_key]
        else:
            GAIN=1


    logging.info('Template GAIN: %.1f [e^- /count]' % GAIN)


    # print(list(headinfo.keys()))
    # try:
    for i in ['EXPTIME','EXP_TIME','TIME-INT']:
        if i in list(headinfo.keys()):
            template_exp_time = headinfo[i]
            break

    if isinstance(template_exp_time, str):
       template_exp_time_split = template_exp_time.split('/')
       if len(template_exp_time_split)>1:
           template_exp_time = float(template_exp_time_split[0])
       else:
           template_exp_time = float(template_exp_time)


    logging.info('Template Exposure Time: %.1f [s]' % template_exp_time)

    if telescope == 'MPI-2.2' and not (use_filter is None) :
        if use_filter in ['J','H','K']:
            logging.info('Detected GROND IR - setting pixel scale to 0.3')
            pixel_scale = 0.3
        else:
            logging.info('Detected GROND Optical - setting pixel scale to 0.16')
            pixel_scale = 0.16
    else:

        pixel_scale   = tele_autophot_input[telescope][inst_key][inst]['pixel_scale']



    # Write new header
    updated_header = getheader(fpath)
    updated_header['GAIN'] = GAIN

    updated_header['exp_time'] = template_exp_time
    updated_header['GAIN'] = GAIN
    updated_header['RDNOISE'] = rdnoise

    fits.writeto(fpath,
                 image,
                 updated_header,
                 overwrite = True,
                 output_verify = 'silentfix+ignore')





    if clean_cosmic:

        # if 'CRAY_RM'  not in header:

        from autophot.packages.call_crayremoval import remove_cosmic_rays

        if 'CRAY_RM'  not in updated_header:
            headinfo = getheader(fpath)
            # image with cosmic rays
            image_old = fits.PrimaryHDU(image)

            image = remove_cosmic_rays(image_old,
                                       gain = GAIN,
                                       use_lacosmic = use_lacosmic)

            # Update header and write to new file
            updated_header['CRAY_RM'] = ('T', 'Comsic rays w/astroscrappy ')
            fits.writeto(fpath,
                         image,
                         updated_header,
                         overwrite = True,
                         output_verify = 'silentfix+ignore')
            logging.info('Cosmic rays removed - image updated')

        else:

            logging.info('Cosmic sources pre-cleaned - skipping!')


    if redo_wcs:


        # Run local instance of Astrometry.net - returns filepath of wcs file
        astro_check = AstrometryNetLOCAL(fpath,
                                        solve_field_exe_loc = solve_field_exe_loc,
                                        pixel_scale = pixel_scale,
                                        # ignore_pointing = False,
                                        target_ra = target_ra,
                                        target_dec = target_dec,
                                        search_radius = search_radius,
                                        downsample = downsample,
                                        cpulimit = cpu_limit)

        old_header = getheader(fpath)

        try:
            old_header = removewcs(headinfo,delete_keys = True)

            # Open wcs fits file with wcs values
            new_wcs  = fits.open(astro_check,ignore_missing_end = True)[0].header

            # script used to update per-existing header file with new wcs values
            header_updated = updatewcs(old_header,new_wcs)

            # update header to show wcs has been checked
            header_updated['UPWCS'] = ('T', 'WCS by APT')


            os.remove(astro_check)

            # Write new header
            fits.writeto(fpath,image,
                         header_updated,
                         overwrite = True,
                         output_verify = 'silentfix+ignore')

        except Exception as e:

            logger.info('Error with template WCS: %s' % e)





    if get_fwhm or build_psf:



        template_fwhm,df,scale,image_params = get_fwhm(image,
                                                   write_dir,
                                                   base,
                                                   threshold_value = threshold_value,
                                                   # fwhm_guess = autophot_input['source_detection']['fwhm_guess,
                                                   # bkg_level = autophot_input['fitting']['bkg_level'],
                                                   # max_source_lim = autophot_input['source_detection']['max_source_lim'],
                                                   # min_source_lim = autophot_input['source_detection']['min_source_lim'],
                                                   # int_scale = autophot_input['source_detection']['int_scale'],
                                                   # fudge_factor = autophot_input['source_detection']['fudge_factor'],
                                                   # fine_fudge_factor = autophot_input['source_detection']['fine_fudge_factor'],
                                                   # source_max_iter = autophot_input['source_detection']['source_max_iter'],
                                                   # sat_lvl = autophot_input['sat_lvl'],
                                                   # lim_SNR = autophot_input['limiting_magnitude']['lim_SNR'],
                                                   # scale_multipler = autophot_input['source_detection']['scale_multipler'],
                                                   # sigmaclip_FWHM = autophot_input['source_detection']['sigmaclip_FWHM'],
                                                   # sigmaclip_FWHM_sigma = autophot_input['source_detection']['sigmaclip_FWHM_sigma'],
                                                   # sigmaclip_median = autophot_input['source_detection']['sigmaclip_median'],
                                                   # isolate_sources = autophot_input['source_detection']['isolate_sources'],
                                                   # isolate_sources_fwhm_sep = autophot_input['source_detection']['isolate_sources_fwhm_sep'],
                                                   # init_iso_scale = autophot_input['source_detection']['init_iso_scale'],
                                                   # remove_boundary_sources = autophot_input['source_detection']['remove_boundary_sources'],
                                                   # pix_bound = autophot_input['source_detection']['pix_bound'],
                                                   # sigmaclip_median_sigma = autophot_input['source_detection']['sigmaclip_median_sigma'],
                                                   # save_FWHM_plot = autophot_input['source_detection']['save_FWHM_plot'],
                                                   # plot_image_analysis = autophot_input['source_detection']['plot_image_analysis'],
                                                   # save_image_analysis = autophot_input['source_detection']['save_image_analysis'],
                                                   # use_local_stars_for_FWHM = autophot_input['photometry']['use_local_stars_for_FWHM'],
                                                    prepare_templates = True,
                                                   # image_filter = autophot_input['image_filter'],
                                                   # target_name = autophot_input['target_name'],
                                                   # target_x_pix = None,
                                                   # target_y_pix = None,
                                                   # local_radius = autophot_input['photometry']['local_radius'],
                                                   # mask_sources = autophot_input['preprocessing']['mask_sources'],
                                                   # mask_sources_XY_R = None,
                                                   # remove_sat = autophot_input['source_detection']['remove_sat'],
                                                    use_moffat = use_moffat ,
                                                   # default_moff_beta = autophot_input['fitting']['default_moff_beta'],
                                                   # vary_moff_beta = autophot_input['fitting']['vary_moff_beta'],
                                                   # max_fit_fwhm = autophot_input['source_detection']['max_fit_fwhm'],
                                                   # fitting_method = autophot_input['fitting']['fitting_method']
                                                   )
        # autophot_input['fwhm'] = image_fwhm
        # autophot_input['scale'] = scale
        # autophot_input['image_params'] = image_params
        # header['FWHM'] = image_fwhm



        df.to_csv(os.path.join(dirpath,'calib_template.csv'),index = False)



    if build_psf:

        df_PSF = do_aperture_photometry(image = image,
                                        dataframe = df,
                                        fwhm = template_fwhm,
                                        ap_size = ap_size,
                                        inf_ap_size =inf_ap_size,
                                        r_in_size =r_in_size,
                                        r_out_size = r_out_size)

        psf.build_r_table(base_image = image,
                            selected_sources = df_PSF,
                            fwhm = template_fwhm,
                            exp_time = template_exp_time,
                            image_params = image_params,
                            fpath = fpath,
                            GAIN = GAIN,
                            rdnoise = rdnoise,
                            use_moffat = use_moffat,
                            # vary_moff_beta = False,
                            fitting_radius = fitting_radius,
                            regrid_size = regrid_size,
                            # use_PSF_starlist = autophot_input['psf']['use_PSF_starlist'],
                            use_local_stars_for_PSF = False,
                            prepare_templates = True,
                            scale = scale,
                            ap_size = ap_size,
                            r_in_size = r_in_size,
                            r_out_size = r_out_size,
                            # local_radius = autophot_input['photometry']['local_radius'],
                            # bkg_level = autophot_input['fitting']['bkg_level'],
                            psf_source_no = psf_source_no,
                            # min_psf_source_no = autophot_input['psf']['min_psf_source_no'],
                            construction_SNR = 5,
                            remove_bkg_local = True,
                            remove_bkg_surface = False,
                            remove_bkg_poly = False,
                            remove_bkg_poly_degree = 1,
                            # fit_PSF_FWHM = autophot_input['psf']['fit_PSF_FWHM'],
                            # max_fit_fwhm = autophot_input['source_detection']['max_fit_fwhm'],
                            fitting_method = fitting_method,
                            save_PSF_stars = False,
                            # plot_PSF_model_residuals = autophot_input['psf']['plot_PSF_model_residuals'],
                            save_PSF_models_fits = True)


        pass


    return


# =============================================================================
# Get template from PS1 server
# =============================================================================
def get_pstars(ra, dec, size, filters="grizy"):

    '''
    Attempt to download a templte image from the PS1 image cutout server.

    :param ra: Right Ascension of the target in degrees
    :type ra: float
    :param dec: Declination of the target in degrees
    :type dec: float
    :param size: Pixel size of image
    :type size: int
    :param filters: Name of filters we need, defaults to "grizy"
    :type filters: str, optional
    :return: Filepath of template file from PS1 webiste
    :rtype: str

    '''


    import numpy as np
    from astropy.table import Table
    import requests
    import pandas as pd
    import sys,os

    try:

        format='fits'
        delimiter = ','

        service = "https://ps1images.stsci.edu/cgi-bin/ps1filenames.py"
        url = ("{service}?ra={ra}&dec={dec}&size={size}&format={format}&sep={delimiter}"
               "&filters={filters}").format(**locals())

        with requests.Session() as s:
            myfile = s.get(url)
            s.close()

        text = np.array([line.decode('utf-8') for line in myfile.iter_lines()])

        text = [text[i].split(',') for i in range(len(text))]

        df = pd.DataFrame(text)
        df.columns = df.loc[0].values
        table =Table.from_pandas( df.reindex(df.index.drop(0)).reset_index())


        url = ("https://ps1images.stsci.edu/cgi-bin/fitscut.cgi?"
               "ra={ra}&dec={dec}&size={size}&format={format}").format(**locals())



        # sort filters from red to blue
        flist = ["yzirg".find(x) for x in table['filter']]

        table = table[np.argsort(flist)]

        # if color:
        #     if len(table) > 5:
        #         # pick 3 filters
        #         table = table[[0,len(table)//2,len(table)-1]]
        #     for i, param in enumerate(["red","green","blue"]):
        #         url = url + "&{}={}".format(param,table['filename'][i])
        # else:
        urlbase = url + "&red="
        url = []
        for filename in table['filename']:
            url.append(urlbase+filename)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname1 = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname1, exc_tb.tb_lineno,e)
        url = None

    return url



# =============================================================================
# Perform image subtraction
# =============================================================================
def subtract(file,template,image_fwhm,use_zogy = False,hotpants_exe_loc = None,
             hotpants_timeout=45, template_dir = None,footprint = None, remove_sat = False,
             zogy_use_pixel = False):
    '''

    Perform image subtraction using either Hotpants or Zogy

    :param file: Filepath of science image containing suspected transient flux
    :type file: str
    :param template: Filepath of science image without any transient flux
    :type template: str
    :param image_fwhm: Full Width Half Maximum (FWHM) of science image
    :type image_fwhm: float
    :param use_zogy: Use Zogy rather that HOTPANTS. If zogy is not available, the code will revert to HOTPANTS, defaults to False
    :type use_zogy: bool, optional
    :param hotpants_exe_loc: Path to *hotpants* executable, defaults to None
    :type hotpants_exe_loc: str, optional
    :param hotpants_timeout: Maximum allowed time for Hotpant. If the time taken exceeds an error is raise, defaults to 45
    :type hotpants_timeout: float, optional
    :param template_dir: Parent Directory of template files. This should contain the PSF file which should begin with 'PSF_model'. If None, use the parent directory of the *template* filepath, defaults to None
    :type template_dir: str, optional
    :param footprint: DESCRIPTION, defaults to None
    :type footprint: TYPE, optional
    :param remove_sat: If True, set the maximum to the saturation level, rather than the image maximum, defaults to False
    :type remove_sat: bool, optional
    :param zogy_use_pixel: If True, use pixel values for gain matching when using zogy, else source matching is used for image matching, defaults to False
    :type zogy_use_pixel: bool, optional
    :return: Retruns filepath of image after template subtraction
    :rtype: str

    '''

    import subprocess
    import os
    import sys
    import numpy as np
    from pathlib import Path
    import signal
    import time
    from autophot.packages.functions import getimage,getheader
    from astropy.io import fits
    import logging
    import warnings
    from astropy.wcs import WCS

    logger = logging.getLogger(__name__)

    base = os.path.basename(file)
    write_dir = os.path.dirname(file)
    base = os.path.splitext(base)[0]


    logger.info('\nImage subtracion')
    if hotpants_exe_loc is None and not use_zogy:
        use_zogy = True

        logger.info('HOTPANTS selected but exe file location not found, trying PyZogy')
        hotpants_exe_loc = True

    if use_zogy: # Check if zogy is available

        try:
            from PyZOGY.subtract import run_subtraction
            use_zogy = True
        except ImportError as e:
            logger.info('PyZogy selected but not installed: %s' % e)
            use_zogy = False

    if use_zogy and not hotpants_exe_loc:
        warnings.warn('No suitable template subtraction package found/nPlease check installation instructions!,/n returning original image')
        return np.nan


    try:

        # convolve_image = False
        # smooth_template = False

        # Get file extension and template data
        fname_ext = Path(file).suffix

        # Open image and template
        file_image     = getimage(file)

        image_header = getheader(file)

        original_wcs = WCS(image_header)

        # header = getheader(file)
        template_image = getimage(template)

        if template_dir is None:
            template_dir = os.path.dirname(template)
        # template_header = getheader(template)

        # Where the subtraction will be written
        output_fpath = str(file.replace(fname_ext,'_subtraction'+fname_ext))

        # Create footprint
        footprint = np.zeros(file_image.shape).astype(bool)

        # footprint_template = np.zeros(template_image.shape).astype(bool)

        footprint[ ( np.isnan(file_image)) | np.isnan(template_image) ] = 1


        hdu = fits.PrimaryHDU(footprint.astype(int))
        hdul = fits.HDUList([hdu])

        footprint_loc = os.path.join(write_dir,'footprint_'+base+fname_ext)

        hdul.writeto(footprint_loc,
                      overwrite=True,
                      output_verify = 'silentfix+ignore')

        check_values_image = file_image[~footprint]

        check_values_template = template_image[~footprint]

        if  remove_sat  :

            image_max = [np.nanmax(check_values_image) if np.nanmax(check_values_image) < 2**16 else  + 2**16][0]

            template_max = [np.nanmax(check_values_template) if np.nanmax(check_values_template) < 2**16 else  2**16][0]

        else:

            image_max = np.nanmax(check_values_image)

            template_max = np.nanmax(np.nanmax(check_values_template))





        if use_zogy:
            try:

                # Get filename for saving
                base = os.path.splitext(os.path.basename(file))[0]

                logger.info('Performing image subtraction using PyZOGY')

                # PyZOGY_log = write_dir + base + '_ZOGY.txt'
                # original_stdout = sys.stdout # Save a reference to the original standard output


                image_psf = os.path.join(write_dir,'PSF_model_'+base.replace('_image_cutout','')+'.fits')

                from glob import glob
                template_psf = glob(os.path.join(template_dir,'PSF_model_*'))[0]

                logger.info('Using Image : %s' % file)
                logger.info('Using Image PSF: %s' % image_psf)
                logger.info('Using Template : %s' % template)
                logger.info('Using Template PSF: %s' % template_psf)

                logger.info('\nRunning Zogy...\n')

                # logger.info(image_max,template_max)

                diff = run_subtraction(science_image = file,
                                       reference_image = template,
                                       science_psf = image_psf,
                                       reference_psf = template_psf,
                                       reference_mask = footprint,
                                       science_mask = footprint,
                                       show = False,
                                       # sigma_cut = 3,
                                       normalization = "science",
                                       science_saturation = 10+image_max,
                                       reference_saturation = 10+template_max,
                                       n_stamps = 1,
                                       max_iterations = 10,
                                       use_pixels  = zogy_use_pixel
                                        # size_cut = True
                                        )

                hdu = fits.PrimaryHDU(diff[0])
                hdul = fits.HDUList([hdu])
                hdul.writeto(str(file.replace(fname_ext,'_subtraction'+fname_ext)),
                             overwrite = True,
                             output_verify = 'silentfix+ignore')
            except Exception as e:
                logger.info('Pyzogy Failed [%s] - trying HOTPANTS' % e)
                use_zogy = False



        if not use_zogy :

            logger.info('Performing image subtraction using HOTPANTS')

            # Get filename for saving
            base = os.path.splitext(os.path.basename(file))[0]

            # Location of executable for hotpants
            exe = hotpants_exe_loc

            # =============================================================================
            # Argurments to send to HOTPANTS process - list of tuples
            # =============================================================================

            # Arguments to pass to HOTPANTS

            include_args = [
                    # Input image
                            ('-inim',   str(file)),
                    # Template Image
                            ('-tmplim', str(template)),
                    # Output image name
                            ('-outim',  str(file.replace(fname_ext,'_subtraction'+fname_ext))),
                    # Image lower limits
                            ('-il',     str(np.nanmin(check_values_image))),
                    # Template lower limits
                            ('-tl',     str(np.nanmin(check_values_template))),
                    # Template upper limits
                            ('-tu',     str(template_max+10)),
                    # Image upper limits
                            ('-iu',     str(image_max+10)),
                    # Image mask
                            ('-imi',    str(footprint_loc)),
                    # Template mask
                            ('-tmi',    str(footprint_loc)),
                    # Image gain
                            # ('-ig',     str(autophot_input['GAIN'])),
                    # Template gain
                            # ('-tg',     str(t_header['gain'])),
                    # Normalise to image[i]
                            ('-n',  'i'),
                    # spatial order of kernel variation within region
                            ('-ko', '1'),
                    # Verbosity - set to as output is sent to file
                            ('-v' , ' 0') ,
                    # number of each region's stamps in x dimension
                            ('-nsx' , '11') ,
                    # number of each re5ion's stamps in y dimension
                            ('-nsy' , '11'),
                    # number of each region's stamps in x dimension
                    # RMS threshold forgood centroid in kernel fit
                            ('-ft' , '20') ,
                    # threshold for sigma clipping statistics
                            ('-ssig' , '5.0') ,
                    # high sigma rejection for bad stamps in kernel fit
                            ('-ks' , '3.0'),
                    # convolution kernel half width
                            # ('-r' , str(1.5*image_FWHM)) ,
                    # number of centroids to use for each stamp
                            # ('-nss' , str(5))

                            ]

            args= [str(exe)]

            for i in include_args:
                args[0] += ' ' + i[0] + ' ' + i[1]
            # =============================================================================
            # Call subprocess using executable location and option prasers
            # =============================================================================

            start = time.time()

            HOTPANTS_log = write_dir + base + '_HOTterPANTS.txt'

            # logger.info(args, file=open(HOTPANTS_log, 'w'))


            with  open(HOTPANTS_log, 'w')  as FNULL:

                pro = subprocess.Popen(args,shell=True, stdout=FNULL, stderr=FNULL)
                print('ARGUMENTS:', args, file=FNULL)

                # Timeout
                pro.wait(hotpants_timeout)

                try:
                    # Try to kill process to avoid memory errors / hanging process
                    os.killpg(os.getpgid(pro.pid), signal.SIGTERM)
                    logger.info('HOTPANTS PID killed')
                    logger.info(args)
                except:
                    pass

            logger.info('HOTPANTS finished: %ss' % round(time.time() - start) )

        # =============================================================================
        # Check that subtraction file has been created
        # =============================================================================
        if os.path.isfile(output_fpath):

            file_size = os.path.getsize(str(file.replace(fname_ext,'_subtraction'+fname_ext)))

            if file_size == 0:

                logger.info('File was created but nothing written')

                return np.nan

            else:

                logger.info('Subtraction saved as %s' % os.path.splitext(os.path.basename(file.replace(fname_ext,'_subtraction'+fname_ext)))[0])

                original_wcs

                template_header = getheader(output_fpath)
                template_image = getimage(output_fpath)
                template_header.update(original_wcs.to_header())

                fits.writeto(output_fpath,
                            template_image,
                            template_header,
                            overwrite = True,
                             output_verify = 'silentfix+ignore')


                return output_fpath

        if not os.path.isfile(output_fpath):

            logger.info('File was not created')

            return np.nan

    except Exception as e:

        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logger.info(exc_type, fname, exc_tb.tb_lineno,e)

        try:
                # Try to kill process to avoid memory errors / hanging process
            os.killpg(os.getpgid(pro.pid), signal.SIGTERM)
            logger.info('HOTPANTS PID killed')
        except:
            pass

        return np.nan
