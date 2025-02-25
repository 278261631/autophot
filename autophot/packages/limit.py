def ranks(sample):

    """Return the ranks of each element in an integer sample.

    :param sample: sample of intergers
    :type sample: array-like

    :return: Return the ranks of each element in an integer sample
    :rtype: sorted list
    """
    indices = sorted(range(len(sample)), key=lambda i: sample[i])
    return sorted(indices, key=lambda i: indices[i])

def sample_with_minimum_distance(n=[0,40], k=4, d=10):

    """Sample of k elements from range(n), with a minimum distance d.

    :param n: range of  values
    :type n: tuple

    :param k: number of points
    :type k: int

    :param d: distance between each points
    :type d: float

    :return: list of tuples containing (x,y) location of points seperated by distance(d)
    :rtype: list of tuples
    
    """
    import random

    sample_x = random.sample(range(int(n[0]),int(n[1])-(k-1)*(d-1)), k)

    sample_y = random.sample(range(int(n[0]),int(n[1])-(k-1)*(d-1)), k)

    return [(x + (d-1)*rx,y + (d-1)*ry) for x,y, rx,ry in zip(sample_x,sample_y,ranks(sample_x),ranks(sample_y))]

def PointsInCircum(r,shape,n=8):
    
    '''
    Generate series of x,y coordinates a distance r from the center of the image
    
    :param r: Distance from center of image 
    :type r: Float

    :param shape: Image shape
    :type shape: Tuple
    
    :param n: Number of points, defaults to 8
    :type n: Integer, optional
    
    :return: List of x,y coorindates placed around the center of the image  at angles 2*pi/n * i for each ith sources in the n sample size
    :rtype: List of tuples

    '''
    import numpy as np
    
    return [(np.cos(2*np.pi/n*x)*r + shape[1]/2 ,np.sin(2*np.pi/n*x)*r + shape[0]/2) for x in range(0,n)]
    

def flatten_dict(d):
    '''
    
    Flatten nested dictionary into single dictionary with keys:values
    
    :param d: Nested Dictionary
    :type d: dict
    
    :return: Singular dictionary
    :rtype: dict

    '''
    def expand(key, value):
        if isinstance(value, dict):
            return [ (key + '.' + k, v) for k, v in flatten_dict(value).items() ]
        else:
            return [ (key, value) ]

    items = [ item for k, v in d.items() for item in expand(k, v) ]

    return dict(items)


def limiting_magnitude_prob(image,fpath, detection_limit=3, bkg_level=3, fwhm = 7,
                            ap_size=1.7, exp_time = 1, gain = 1, image_params = None,
                            regrid_size=10, fitting_radius = 1.3, beta = 0.75,
                            inject_source_sources_no = 6, inject_source_location = 3, 
                            inject_source_on_target = False, inject_source_random = False,
                            inject_source_add_noise = False, use_moffat= True, 
                            unity_PSF_counts = None, model = None,r_table = None,
                            print_progress = True , remove_bkg_local = True,
                            remove_bkg_surface = False, remove_bkg_poly = False,
                            remove_bkg_poly_degree = 1, subtraction_ready = False,
                            injected_sources_use_beta = True, plot_probable_limit = True):
    '''
        
    Package to employ the same error technique as in the `SNOOPY
    <https://sngroup.oapd.inaf.it/snoopy.html>`_ code. In brief, error
    estimates from the transient measurement are obtained through artificial
    star experiment in which a fake star of magnitude equal to that of the SN,
    is placed in the PSF-fit residual image 
    in a position close to, but not coincident with that of the real source.
    The artifically injects ource is then recovered in an identical manner to
    the original transient magnitude. This is repeated several times. The
    dispersion of these recoevred measurements is then taken as the error on
    the transient measurement and added in quadrature. 
    
    :param image: Image containing transietnf flux
    :type image: 2D array
    :param fwhm: Full Width Half Maximum of image. This is used to constrain the position of the injected sources
    :type fwhm: float
    :param PSF_model: PSF model that is used to fit transient flux, this will also be used to inject the artifical sources
    :type PSF_model: callable function
    :param image_params: Dictionary containing analytical model params. If a moffat is used, this dictionary should containing *alpha* and *beta* and their respective values, else if a gaussian is used, this dictionary should include *sigma* and its value.
    :type image_params: dict
    :param exp_time: Exposure time ins seconds of an image. This is used to calculate the S/N of a potential source.
    :type exp_time: float
    :param unity_PSF_counts: Number of counts under a PSF model with amplitude equal to 1, defaults to None
    :type unity_PSF_counts: float, optional
    :param target_error_compute_multilocation_number: Number of times the psuedo-transient PSF will be reinjected at locations radially around the original SN site, defaults to 5
    :type target_error_compute_multilocation_number: int, optional
    :param target_error_compute_multilocation_position: Multipl of FWHM with which to place the psuedo-transient PSF away from the original site of best fit. Set to -1 to perform sub pixel injection and recovery, defaults to 1
    :type target_error_compute_multilocation_position: float, optional
    :param use_moffat: If True, use a moffat function for FWHM fitting defaults to True
    :type use_moffat: bool, optional
    :param fitting_method: Fitting method when fitting the PSF model, defaults to 'least_square'
    :type fitting_method: str, optional
    :param ap_size: Multiple of FWHM to be used as standard aperture size, defaults to 1.7
    :type ap_size: float, optional
    :param fitting_radius: zoomed region around location of best fit to focus fitting. This allows for the fitting to be concentrated on high S/N areas and not fit the low S/N wings of the PSF, defaults to 1.3
    :type fitting_radius: float, optional
    :param regrid_size: When expanding to larger pseudo-resolution, what zoom factor to use, defaults to 10
    :type regrid_size: int, optional
    :param xfit: X pixel location of best fit for the transient psf in the image, defaults to None
    :type xfit: float, optional
    :param yfit: y pixel location of best fit for the transient psf in the image, defaults to None
    :type yfit: float, optional
    :param Hfit: PSF amplitude of best fit for the transient psf in the image, defaults to None, defaults to None
    :type Hfit: float, optional
    :param r_table: Resiudal table, normailised to unity that is the same shape as the base analytical function
    :type r_table: 2D array
    :param remove_bkg_local: If True, use the local median of the image and subtract this to produce a background free image, see above, defaults to True
    :type remove_bkg_local: Boolean, optional
    :param remove_bkg_surface: If True, use the background fitted surface of the image and subtract this to produce a background free image, see above, defaults to False
    :type remove_bkg_surface: Boolean, optional
    :type remove_bkg_poly: If True, use the background polynomial surface of the image and subtract this to produce a background free image, see above, optional
    :param remove_bkg_poly_degree: If remove_bkg_poly is True, this is the degree of the polynomial fitted to the image, 1 = flat surface, 2 = 2nd order polynomial etc, defaults to 1
    :param bkg_level: The number of standard deviations, below which is assumed to be due to the background noise distribution, defaults to 3
    :type bkg_level: float, optional
    :return: Returns the standard deviation of the recovered magnitudes of the artifically injection pseudo-transient PSFs
    :rtype: float

    '''
                       
    
    import os
    import random
    import logging
    import warnings
    import numpy as np
    
    import matplotlib.pyplot as plt
    from scipy.optimize import curve_fit
    from photutils import CircularAperture
    from matplotlib.gridspec import  GridSpec
    from mpl_toolkits.axes_grid1 import make_axes_locatable

    from photutils import DAOStarFinder
    from astropy.visualization import  ZScaleInterval
    from photutils.datasets import make_noise_image
    
    from autophot.packages.background import remove_background
    from autophot.packages.functions import set_size,calc_mag
    from autophot.packages.functions import gauss_2d, moffat_2d,f_ul
    from autophot.packages.functions import gauss_1d,border_msg
    
    dir_path = os.path.dirname(os.path.realpath(__file__))
    plt.style.use(os.path.join(dir_path,'autophot.mplstyle'))

    logger = logging.getLogger(__name__)
    
    base = os.path.basename(fpath)
    write_dir = os.path.dirname(fpath)
    base = os.path.splitext(base)[0]
    

    
    try:
        if print_progress:
            border_msg('Measuring probable magnitude limit')        
            logger.info('Limiting threshold: %d sigma' % detection_limit)
            
        
        
        image_no_surface,surface,surface_media,noise = remove_background(image,
                                                                         remove_bkg_local = remove_bkg_local, 
                                                                         remove_bkg_surface = remove_bkg_surface,
                                                                         remove_bkg_poly   = remove_bkg_poly,
                                                                         remove_bkg_poly_degree = remove_bkg_poly_degree,
                                                                         bkg_level = bkg_level
                                                                         )


              
        
        if not subtraction_ready:
            

            daofind = DAOStarFinder(fwhm    = fwhm,
                                    threshold = bkg_level*noise,
                                    sharplo   =  0.2,sharphi = 1.0,
                                    roundlo   = -1.0,roundhi = 1.0)
    
    
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                # ignore no sources warning
                sources = daofind(image_no_surface)
    
            if sources != None:

                positions = list(zip(np.array(sources['xcentroid']),np.array(sources['ycentroid'])))
    
                # Add center of image
                positions.append((image.shape[0]/2,image.shape[1]/2))
    
            else:
    
                positions = [(image.shape[0]/2,image.shape[1]/2)]
        else:
                
                positions = [(image.shape[0]/2,image.shape[1]/2)]

        # "size" of source, set to the aperture size
        source_size =  ap_size*fwhm
        
        aperture_area = int(np.pi*source_size**2)

        # Mask out target region
        mask_ap  = CircularAperture(positions,r = source_size)
        mask = mask_ap.to_mask(method='center')
        mask_sumed = [i.to_image(image.shape) for i in mask]
        

        if len(mask_sumed) !=1:
            mask_sumed = sum(mask_sumed)
        else:
            mask_sumed = mask_sumed[0]

        mask_sumed[mask_sumed>0] = 1
        
        if print_progress:
            logging.info('Number of pixels in source: %d [ pixels ]' % aperture_area)

        # Mask out center region
        mask_image  = (image_no_surface) * (1-mask_sumed)
        
        #Used for plotting, get vmin\vmin from aperture are to highlight source
        vmin,vmax = (ZScaleInterval(nsamples = 500)).get_limits(mask_image)

    
        # get pixels that are excluded and included
        excluded_points = np.where(mask_image == 0)

        exclud_x = excluded_points[1]
        exclud_y = excluded_points[0]

        exclud_zip = list(zip(exclud_x,exclud_y))

        included_points = np.where(mask_image != 0)

        includ_x = list(included_points[1])
        includ_y = list(included_points[0])

        includ_zip = list(zip(includ_x,includ_y))

        number_of_points = 150

        fake_points = {}

        # Failsafe - if there isn't enough pixels just use everything
        if len(includ_zip) < aperture_area:

            includ_zip=includ_zip+exclud_zip

        # get random sample of pixels and sum them up
        for i in range(number_of_points):

            fake_points[i] = []

            random_pixels = random.sample(includ_zip,aperture_area)

            xp_ran = [i[0] for i in random_pixels]
            yp_ran = [i[1] for i in random_pixels]

            fake_points[i].append([xp_ran,yp_ran])

        fake_sum = {}

        for i in range(number_of_points):

            fake_sum[i] = []

            for j in fake_points[i]:

                for k in range(len(j[0])):

                    fake_sum[i].append(image_no_surface[j[0][k]][j[1][k]])


        fake_mags = {}

        for f in fake_sum.keys():

            fake_mags[f] = np.sum(fake_sum[f])

        # Fit histogram and get mean and std of distribution
        hist, bins = np.histogram(list(fake_mags.values()),
                                  bins = len(list(fake_mags.values())),
                                  density = True)

        center = (bins[:-1] + bins[1:]) / 2

        sigma_guess = np.nanstd(list(fake_mags.values()))
        mean_guess = np.nanmean(list(fake_mags.values()))
        A_guess = np.nanmax(hist)

        popt,pcov = curve_fit(gauss_1d,center,hist,
                              p0=[A_guess,mean_guess,sigma_guess],
                              absolute_sigma = True )

        mean = popt[1]
        std  = abs(popt[2])
        
        if injected_sources_use_beta:

            f_ul_beta = f_ul(n = detection_limit, beta_p = beta, sigma = std)
        
            count_ul = f_ul_beta
        else:
            
            count_ul = detection_limit*std
            

        flux  = count_ul / exp_time

        mag_level = calc_mag(flux,gain,0)
        
        if print_progress:
            logging.info('Mean: %s - std: %s' % (round(mean,3),round(std,3)))
            logging.info('Detection at %s std: %.3f [counts]' % (detection_limit,count_ul))
        
        

        # =============================================================================
        # Plot histogram of background values
        # =============================================================================
        
        if plot_probable_limit:
            
            plt.ioff()
            
            limiting_mag_figure = plt.figure(figsize = set_size(250,aspect = 2))
    
            ncols = 2
            nrows = 2
    
            heights = [0.75,1]
            # widths = []
    
            gs = GridSpec(nrows, ncols ,
                          wspace=0.4 ,
                          hspace=0.5,
                          height_ratios=heights,
                           # width_ratios = widths
                           )
            
            ax0 = limiting_mag_figure.add_subplot(gs[0, :])
            ax1 = limiting_mag_figure.add_subplot(gs[1, 0])
            ax2 = limiting_mag_figure.add_subplot(gs[1, 1])
            

            ax1.scatter(exclud_x,exclud_y,
                        color ='red',
                        marker = 'x',
                        alpha = 0.1,
                        label = 'Encluded areas',
                        zorder = 2)
    
            # the histogram of the data
            n, bins, patches = ax0.hist(list(fake_mags.values()),
                                        density=True,
                                        bins = 'auto',
                                        facecolor='blue',
                                        histtype = 'step',
                                        align = 'mid',
                                        alpha=1,
                                        label = 'Pseudo-Counts\nDistribution')
            
            line_kwargs = dict(ymin = 0,ymax = 0.75, alpha=0.5,color='black',ls = '--')
    
            ax0.axvline(mean, alpha=0.5,color='black',ls = '--')
            
            ax0.axvline(mean + 1*std,**line_kwargs)
            ax0.text(mean + 1*std,np.max(n),r'$1\sigma_{bkg}$',
                     rotation = -90,va = 'top',ha = 'center')
            
            ax0.axvline(mean + 2*std,**line_kwargs)
            ax0.text(mean + 2*std,np.max(n),r'$2\sigma_{bkg}$',
                     rotation = -90,va = 'top',ha = 'center')
    
            ax0.axvline(mean + detection_limit*std,**line_kwargs)
            ax0.text(mean + detection_limit*std,np.max(n),r'$'+str(detection_limit)+r'\sigma_{bkg}$',
                     rotation = -90,va = 'top',ha = 'center')
            
            if injected_sources_use_beta:
                ax0.axvline(mean+f_ul_beta,ymin = 0,ymax = 0.65, alpha=0.5,
                            color='black',ls = '--')
                ax0.text(mean+f_ul_beta,np.max(n),r'$F_{UL,\beta=%.2f}$ '%beta,
                         rotation = -90,va = 'top',ha = 'center')
            
    
    
            x_fit = np.linspace(ax0.get_xlim()[0], ax0.get_xlim()[1], 250)
           
            ax0.plot(x_fit, gauss_1d(x_fit,*popt),
                     label = 'Gaussian Fit',
                     color = 'red')
    
    
            ax0.set_xlabel('Pseudo-Counts [counts]')
            ax0.set_ylabel('Probability Distribution')
    
            im2 = ax1.imshow(image_no_surface,origin='lower',
                             aspect = 'auto',
                             interpolation = 'nearest')
    
            divider = make_axes_locatable(ax2)
            cax = divider.append_axes("right", size="5%", pad=0.05)
            cb = limiting_mag_figure.colorbar(im2, cax=cax)
            cb.ax.set_ylabel('Counts', rotation=270,labelpad = 5)
            cb.update_ticks()
    
            ax1.set_title('Image - Surface')
            
  
    
            # =============================================================================
            # We now have an upper and lower estimate of the the limiting magnitude
            # =============================================================================
    
            fake_sources = np.zeros(image.shape)
            
            # PSF_avaiable = True
            
            try:
                
                if unity_PSF_counts is None or r_table is None:
                    raise Exception ('PSF model not available\n- Using Gaussian for probable limiting magnitude')
    
                model_label = 'PSF'
    
                def mag2image(m):
                    '''
                    Convert magnitude to height of PSF
                    '''
                    Amplitude  = (exp_time/(unity_PSF_counts))*(10**(m/-2.5))
    
                    return Amplitude
                
                # PSF model that matches close-up shape around target
                def input_model(x,y,H):
                    return model(x, y, 0, H, r_table, fwhm, image_params,use_moffat = use_moffat, fitting_radius = fitting_radius,regrid_size = regrid_size,pad_shape = image.shape)        
    
            except:
                
                # PSF_avaiable = False
    
                '''
                if PSF model isn't available - use Gaussian instead
    
                '''
                # logging.info('PSF model not available\n- Using Gaussian for probable limiting magnitude')
                
                model_label = 'Gaussian'
    
                sigma = fwhm / 2*np.sqrt(2*np.log(2))
                
       
    
                def mag2image(m):
                    '''
                    Convert magnitude to height of Gaussian
                    '''
    
                    #  Volumne/counts under 2d gaussian for a magnitude m
                    volume =  (10**(m/-2.5)) * exp_time
    
                    # https://en.wikipedia.org/wiki/Gaussian_function
                    Amplitude =  volume/(2*np.pi*sigma**2)
    
                    return Amplitude
    
                def input_model(x,y,A):
    
                    # x = np.arange(0,image.shape[0])
                    xx,yy= np.meshgrid(np.arange(0,image.shape[1]),np.arange(0,image.shape[0]))
    
    
    
                    if use_moffat:
                        model = moffat_2d((xx,yy),x,y,0,A,image_params)
    
                    else:
                        model = gauss_2d((xx,yy),x,y,0,A,image_params)
                        
                    return model.reshape(image.shape)
                
            # =============================================================================
            #  What magnitude do you want this target to be?
            # =============================================================================
    
            inject_source_mag = mag2image(mag_level)
    
            # Number of sources
            source_no =inject_source_sources_no
            
            random_sources = PointsInCircum(inject_source_location*fwhm,
                                            image.shape,n=source_no)
            
            xran = [abs(i[0]) for i in random_sources]
            yran = [abs(i[1]) for i in random_sources]
    
            # =============================================================================
            # Inject sources
            # =============================================================================
            
            try:
                
                if inject_source_random:
    
                    for i in range(0,len(random_sources)):
                        
    
                        fake_source_i = input_model(xran[i], yran[i],inject_source_mag)
    
                        if inject_source_add_noise:
    
                            nan_idx = np.isnan(fake_source_i)
                            fake_source_i[nan_idx] = 0
    
                            fake_source_i[fake_source_i<0] = 0
    
                            fake_source_i = make_noise_image(fake_source_i.shape,
                                                            distribution = 'poisson',
                                                            mean = fake_source_i,
                                                            seed = np.random.randint(0,1e3))
                            
                        fake_sources += fake_source_i
                        
                        ax2.scatter(xran[i],yran[i],
                                    marker = 'o',
                                    s=150,
                                    facecolors='none',
                                    edgecolors='r',
                                    # label = 'Masked area',
                                    alpha = 0.25
                                    )
                        ax2.scatter([],[],
                                    marker = 'o',
                                    facecolors='none',
                                    edgecolors='r',
                                    alpha = 0.1,
                                    label = 'Injected Source')
    
                if inject_source_on_target:
    
                    fake_source_on_target = input_model(image.shape[1]/2,image.shape[0]/2,inject_source_mag)
    
                    if inject_source_add_noise:
                        
                        nan_idx = np.isnan(fake_source_on_target)
                        fake_source_on_target[nan_idx] = 1e-6
                        fake_source_on_target[fake_source_on_target<0] = 0
    
                        fake_source_on_target = make_noise_image(fake_source_on_target.shape,
                                                        distribution = 'poisson',
                                                        mean = fake_source_on_target,
                                                        seed = np.random.randint(0,1e3))
    
                    fake_sources += fake_source_on_target
                    
                    ax2.scatter(image.shape[1]/2,image.shape[0]/2,
                                marker = 'o',s=150,
                                facecolors='none',
                                edgecolors='black',
                                alpha = 0.5)
                    
                    ax2.annotate('On\nTarget', (image.shape[1]/2, -1+image.shape[0]/2),
                                 color='black',
                                 alpha = 0.5,
                                 ha='center')
    
    
                im1 = ax2.imshow(image_no_surface + fake_sources,
                                  aspect = 'auto',
                                  origin = 'lower',
                                 interpolation = 'nearest')
                ax2.set_title(' Injected %s Sources ' % model_label)
                
             
    
            except Exception as e:
                
                logging.exception(e)
                im1=ax2.imshow(image - surface , origin='lower',aspect = 'auto',)
                ax2.set_title('[ERROR] Fake Sources [%s]' % model_label)
    
    
            divider = make_axes_locatable(ax1)
            cax = divider.append_axes("right", size="5%", pad=0.05)
            cb = limiting_mag_figure.colorbar(im1, cax=cax)
            cb.ax.set_ylabel('Counts', rotation=270,labelpad = 5)
          
            cb.ax.yaxis.set_offset_position('left')
    
    
    
            lines_labels = [ax.get_legend_handles_labels() for ax in limiting_mag_figure.axes]
            handles,labels = [sum(i, []) for i in zip(*lines_labels)]
    
            by_label = dict(zip(labels, handles))
    
            leg = limiting_mag_figure.legend(by_label.values(), by_label.keys(),
                                             bbox_to_anchor=(0.5, 0.87 ),
                                             loc='lower center',
                                             ncol = 4,
                                             frameon=False)
            
            for lh in leg.legendHandles: 
                lh.set_alpha(1)
    
            save_loc = os.path.join(write_dir,'limiting_mag_prob_'+base+'.pdf')
            limiting_mag_figure.savefig(save_loc,
                                            bbox_inches='tight',
                                            format = 'pdf')
            plt.close(limiting_mag_figure)

    # master try/except
    except Exception as e:
        print('limit issue')
        logging.exception(e)
        mean = np.nan
        std = np.nan
        mag_level = np.nan




    return mag_level




def inject_sources(image, fwhm, fpath, exp_time, ap_size = 1.7, scale = 25, 
                   zeropoint = 0, r_in_size = 2, r_out_size = 3, explore = False,
                   injected_sources_use_beta=True, beta_limit = 0.75, gain = 1,
                   rdnoise = 0, inject_lmag_use_ap_phot = True, use_moffat = True,
                   image_params = None, fitting_radius = 1.3, regrid_size = 10, 
                   detection_limit = 3,bkg_level = 3, inject_source_recover_dmag = 0.5,
                   inject_source_recover_fine_dmag = 0.05, inject_source_mag = 21, 
                   inject_source_recover_nsteps = 50, inject_source_recover_dmag_redo = 3,
                   inject_source_sources_no = 10, inject_source_cutoff_limit = 0.8,
                   subtraction_ready = False, unity_PSF_counts = None, 
                   inject_source_add_noise = False, inject_source_location = 3,
                   injected_sources_additional_sources_position = 1,
                   injected_sources_additional_sources_number = 3, plot_injected_sources_randomly = True,
                   injected_sources_save_output = False, model = None, 
                   r_table = None, plot_steps = False, save_cutouts = False,
                   lmag_guess= None, print_progress = True, save_plot = True,
                   save_plot_to_folder = False,fitting_method = 'least_sqaure',
                   remove_bkg_local = True, remove_bkg_surface = False, 
                   remove_bkg_poly = False, remove_bkg_poly_degree = 1):
    '''
    
    Package to find limiting magnitude using artifical source injection. This is
    the most rebust package available to find a meaningful limiting magnitude for a
    location on an image. Given a image (perhaps a image with a suspected tranaient
    in the image center), the code will the perform the following tasks to find the
    limiting magnitude or the briggest a source can be an be confidently assumed to
    be *not* apart of the background noise distribution:
    
    #.  Setup locations around the transient site (i.e. the center of the image).
    For convergence reasons these area should *fail* the detection criteria e.g.
    have a S/N < 3 or :math:`\\beta\\prime<0.5`. If selected, these source posiiton
    may be extended to include subpixel positions.
    
    #.  Beginning with an initial guess (either given in the function or assumed),
    find the detection details (e.g S/N >3 or :math:`\\beta\\prime>0.75`) for an
    intial round of artifical sources. If Selected these sources may have random
    noise added to them, to fully explore the probability of a certain magnitude
    being recovered.
    
    #.  *If the initial sources are detected*, decrease the magnitude by a large
    step size until the sources are no longer detected. In this scenario we expect
    to overshoot the limiting magnitude. We will then increase the magnitude by a
    smaller amount until the sources are the recovered to a significant level.
    
    #.  *If the initial sources are not detected*: In this scenario the initial
    guess at the limiting magnitude is too faint. The injected magnitude is
    increased (i.e. gets brighter) by a large step size until a significant number
    of sources are detected. Again we expect to overshoot the limiting magnitude.
    The injected sources are then decreased in magnitude until a significant number
    of sources are lost. 
    
    #. The penultimate injected magnitude is set at the limiting magnitude.
    
    This can be a very robust function that can fully sample the surrounding
    location of a suspected transient. *However* if the transient has significant
    flux, i.e. it is severly present in the image or the location is severly
    contaminated by background galaxy contamination, this is due to the possibility
    of one side of the image being *more* contaminated then the other. Further work
    will better account for this issue.
    
    
    :param image: 2D image with transient location at its center
    :type image: 2D array
    :param fwhm: Full Wdith Half Maximum of image, this is used to space sources significantly away from the transient site
    :type fwhm: float
    :param fpath: Filepath of image- this is used to save any plots and name them accordingly
    :type fpath: str
    :param exp_time: Expsure time in seconds. Use doe Signal to noise calculations
    :type exp_time: float
    :param ap_size: Multiple of FWHM to be used as standard aperture size, defaults to 1.7
    :type ap_size: float, optional
    :param zeropoint: Zeropoint offset for image, used to convert given limiting magnitude guess to instrumental magnitude, defaults to 0
    :type zeropoint: float, optional
    :param r_in_size: Multiple of FWHM to be used as inner radius of background annulus, defaults to 1.9
    :type r_in_size: float, optional
    :param r_out_size: Multiple of FWHM to be used as outer radius of background annulus, defaults to 2.2
    :type r_out_size: float, optional
    :param explore: DESCRIPTION, defaults to False
    :type explore: TYPE, optional
    :param injected_sources_use_beta: If True, use the :math:`\beta` citeria, else use the more traditional detection limit., defaults to False
    :type injected_sources_use_beta: bool, optional
    :param beta_limit: Probability limit below which a source is deemed lost, defaults to 0.75
    :type beta_limit: float, optional
    :param gain: GAIN on CCD in :math:`e^{-} /  ADU` , defaults to 1.
    :type gain: float, optiona
    :param rdnoise: Read noise of CCD in :math:`e^{-} /  pixel`, defaults to 0.
    :type rdnoise: float, optional
    :param inject_lmag_use_ap_phot: If True, recover injected sources using aperture photometry. This is typically faster that recovering the sources using PSF photometry, defaults to True
    :type inject_lmag_use_ap_phot: bool, optional
    :param use_moffat: If True, use a moffat function for FWHM fitting defaults to True
    :type use_moffat: bool, optional
    :param fitting_radius: zoomed region around location of best fit to focus fitting. This allows for the fitting to be concentrated on high S/N areas and not fit the low S/N wings of the PSF, defaults to 1.3
    :type fitting_radius: float, optional
    :param regrid_size: When expanding to larger pseudo-resolution, what zoom factor to use, defaults to 10
    :type regrid_size: int, optional
    :param detection_limit: Detection significance level, defaults to 3
    :type detection_limit: float, optional
    :param bkg_level: The number of standard deviations, below which is assumed to be due to the background noise distribution, defaults to 3
    :type bkg_level: float, optional
    :param inject_source_recover_dmag: Large magnitude step size , defaults to 0.5
    :type inject_source_recover_dmag: float, optional
    :param inject_source_recover_fine_dmag: Fine magnitude step size, which needs to be smaller than *inject_source_recover_dmag*. This value defines the percision of the limiting magnitude, defaults to 0.05
    :type inject_source_recover_fine_dmag: float, optional
    :param inject_source_mag: if No guess is given, use this magnitude as a start point. Needs *zeropoint* to be defined, defaults to 21
    :type inject_source_mag: float, optional
    :param inject_source_recover_nsteps: Maximum allowed number of steps, defaults to 50
    :type inject_source_recover_nsteps: int, optional
    :param inject_source_recover_dmag_redo: When adding noise, how many times do you wish to add a source, each time with a different noise added onto it, defaults to 3
    :type inject_source_recover_dmag_redo: int, optional
    :param inject_source_sources_no: DESCRIPTION, defaults to 10
    :type iinject_source_sources_no: no, optional
    :param inject_source_cutoff_limit: Fraction of sources needed to be *lost* to determine the limiting magnitude, defaults to 0.8
    :type inject_source_cutoff_limit: float, optional
    :param subtraction_ready: If True, image is template subtracted and the noise floor is assumed to be set to zero, defaults to False
    :type subtraction_ready: bool, optional
    :param unity_PSF_counts: Number of counts under a PSF with amlpitude equal to 1, defaults to None
    :type unity_PSF_counts: float, optional
    :param inject_source_add_noise: If True add noise to any injected artifical sources, defaults to False
    :type inject_source_add_noise: bool, optional
    :param inject_source_location: Multiple of FWHM which defines the distance from the center of time image where to place the artifical sources, defaults to 3
    :type inject_source_location: float, optional
    :param injected_sources_additional_sources_position: Multiple of FWHM around predefined sites where to inject additional sources, set to -1 to perform subpiel movements, defaults to 1
    :type injected_sources_additional_sources_position: TYPE, optional
    :param injected_sources_additional_sources_number: Number of additional sources to inject around predefined sites, defaults to 3
    :type injected_sources_additional_sources_number: int, optional
    :param plot_injected_sources_randomly: If True, inject sources randomly around the image to demostrate the limiting magnitude, if False, plot sources radialy around image center, defaults to True
    :type plot_injected_sources_randomly: bool, optional
    :param injected_sources_save_output: If True, produce plot of limiting magnitude iterative search and save csv file containing the plotted information, defaults to False
    :type injected_sources_save_output: bool, optional
    :param model: PSF model to be used for artifial source inject, if None using a gaussian model, defaults to None
    :type model: function, optional
    :param r_table: Resiudal table, normailised to unity that is the same shape as the base analytical function
    :type r_table: 2D array
    :param lmag_guess: Inital guess at the limting magnitude, zeropooiunt needs to be defined , defaults to None
    :type lmag_guess: float, optional
    :param print_progress: If True, print the status of the limiting magnitude search to screen, defaults to True
    :type print_progress: bool, optional
    :param fitting_method: Fitting method when fitting the PSF model, defaults to 'least_square'
    :type fitting_method: str, optional
    :param remove_bkg_local: If True, use the local median of the image and subtract this to produce a background free image, see above, defaults to True
    :type remove_bkg_local: Boolean, optional
    :param remove_bkg_surface: If True, use the background fitted surface of the image and subtract this to produce a background free image, see above, defaults to False
    :type remove_bkg_surface: Boolean, optional
    :type remove_bkg_poly: If True, use the background polynomial surface of the image and subtract this to produce a background free image, see above, optional
    :param remove_bkg_poly_degree: If remove_bkg_poly is True, this is the degree of the polynomial fitted to the image, 1 = flat surface, 2 = 2nd order polynomial etc, defaults to 1
    :return: Returns the limiting magnitude found via artifical sour injection
    :rtype: float
    '''
    

  
    import os
    import logging
    import numpy as np
    
    import pandas as pd
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    import matplotlib.ticker as ticker
    from matplotlib.lines import Line2D   
    
    from autophot.packages import psf
    from autophot.packages.functions import calc_mag
    from autophot.packages.functions import SNR
    from autophot.packages.functions import set_size
    from autophot.packages.functions import get_distinct_colors

    from photutils.datasets.make import apply_poisson_noise
    from autophot.packages.aperture import measure_aperture_photometry
    from autophot.packages.functions import beta_value,f_ul,border_msg
    from autophot.packages.functions import gauss_2d,moffat_2d
    
    base = os.path.basename(fpath)
    write_dir = os.path.dirname(fpath)
    base = os.path.splitext(base)[0]

    # Get location of this file
    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    plt.style.use(os.path.join(dir_path,'autophot.mplstyle'))

    logger = logging.getLogger(__name__)
    
    PSF_available = True
    
    try:
        if r_table is  None or unity_PSF_counts is None:
            PSF_available = False
            # Check if the PSF model is available
            raise Exception('PSF model not available for artifical source injection, using Gaussian function')
            
        
        def mag2image(m):
            '''
            Convert magnitude to height of PSF
            '''
            Amplitude  = (exp_time/(unity_PSF_counts))*(10**(m/-2.5))

            return Amplitude
         
        # PSF model that matches close-up shape around target
        def input_model(x,y,H):
            
            return model(x, y, 0, H, r_table, fwhm, image_params,use_moffat = use_moffat, 
                         fitting_radius = fitting_radius,regrid_size = regrid_size,
                         pad_shape = image.shape)        


    except Exception as e:
        print(e)
        
        #if PSF model isn't available - use Gaussian instead

        # model_label = 'Gaussian'
    
        sigma = fwhm / 2*np.sqrt(2*np.log(2))
        
        r_table = np.zeros((int(2*scale),int(2*scale)))
            
            
        def mag2image(m):
            
            '''
            Convert instrumental magnitude of to the amplitude of analytical model
            
            :param m: Instrumental magnitude
            :type m: float
            :return: Amplitude of source in counts
            :rtype: float

            '''
            #  Volumne/counts under 2d gaussian for a magnitude m
            volume =  (10**(m/-2.5)) * exp_time
    
            # https://en.wikipedia.org/wiki/Gaussian_function
            Amplitude =  volume/(2*np.pi*sigma**2)
    
            return Amplitude
    
        #  Set up grid
    
        def input_model(x,y,A):

            xx,yy= np.meshgrid(np.arange(0,image.shape[1]),np.arange(0,image.shape[0]))
            
            if use_moffat:
                
                model = moffat_2d((xx,yy),x,y,0,A,image_params)
    
            else:
                
                model = gauss_2d((xx,yy),x,y,0,A,image_params)

    
            return model.reshape(image.shape)
        
        
    if print_progress:
        border_msg('Performing full magnitude recovery test using injected sources')
    
    # Dictionaries to track sources 
    inserted_magnitude = {}
    injected_f_source = {}
    recovered_f_source = {}
    recovered_magnitude = {}
    recovered_magnitude_e = {}
    location_noise = {}
    recovered_fwhm = {}
    recovered_fwhm_e = {}
    recovered_sigma_detection = {}
    recovered_max_flux = {}
    recovered_sources_list  = {}
    recovered_pos = {}
    recovered_SNR={}
    delta_recovered_SNR={}
    SNR_gradient_change = {}
    beta_gradient_change = {}
    beta_probability = {}
    
    if (lmag_guess is None):
        # Start with this magnitude as an initiall guess
        # print('using user given value')
        user_mag_level = inject_source_mag - zeropoint
    else:
        
        user_mag_level = lmag_guess - zeropoint
            
    # Used for debugging
    # user_mag_level = inject_source_mag - zeropoint
    
    start_mag = user_mag_level

    # List containing detections criteria
    recovered_criteria = {}
    
    # Number of steps - this should be quite large to avoid timeing out
    nsteps = inject_source_recover_nsteps
    
    # Large magnitude step
    dmag   = inject_source_recover_dmag
    
    # Finer magnitude magnitude step
    fine_dmag = inject_source_recover_fine_dmag
    
    # If random possion noise is added, how many time is this repeated
    redo   = inject_source_recover_dmag_redo
    
    # Number of sources
    source_no = inject_source_sources_no
    
    # Percentage of sources needed to be 'lost' to define the limiting magnitude
    detection_cutout = inject_source_cutoff_limit
    
    
    # make sure correct version is selected
    if detection_cutout > 1:
        detection_cutout = 0.8
        print('Detection limit cannot be > 1 - setting to 0.8')
        
    # No need to inject sources multiple time if not adding poission noise
    if not inject_source_add_noise:
        redo = 1
    
    # Backstop criteria - this will check that the limiting magnitude is consistent beyond "iter_stop_limit" number of steps
    iter_stop_limit = 5
    iter_stop = 0
    
    
    # Choose locations to inject sources - default is around source loaction
    random_sources = PointsInCircum(inject_source_location*fwhm,image.shape,n=source_no)
    
    xran = [abs(i[0]) for i in random_sources]
    yran = [abs(i[1]) for i in random_sources]
    
    if injected_sources_additional_sources_number>0:
        
        if injected_sources_additional_sources_position == -1:
                    # Move around by one pixel
                    injected_sources_additional_sources_position = 1/fwhm/2
                    
        elif injected_sources_additional_sources_position<=0:
            print('Source possition offset not set correctly [%1.f], setting to -1' % injected_sources_additional_sources_position)
            injected_sources_additional_sources_position = -1
        
        from random import uniform
        
        for k in range(len(xran)):
            
            for j in range(int(injected_sources_additional_sources_number)):

                dx = injected_sources_additional_sources_position * fwhm/2 * uniform(-1,1)
                dy = injected_sources_additional_sources_position * fwhm/2 * uniform(-1,1)
                
                x_dx = np.array(xran)[k] + dx
                y_dy = np.array(yran)[k] + dy
                
                xran.append(x_dx)
                yran.append(y_dy)
            
    
    injection_df = pd.DataFrame([list(xran),list(yran)])
    injection_df = injection_df.transpose()
    injection_df.columns = ['x_pix','y_pix']
    injection_df.reset_index(inplace = True,drop = True)
    
    
    if print_progress:
        print('Starting Magnitude: %.3f [ mag ]' % (start_mag + zeropoint))
    
    hold_psf_position =  False
    
    # Measure flux at each point proir than adding any fake sources - to account for an irregular SNR at a specific location
    if not inject_lmag_use_ap_phot and PSF_available:
        
        psf_fit  = psf.fit(image = image,
                        sources = injection_df,
                        residual_table = r_table,
                        fwhm = fwhm,
                        fpath = fpath,
                        fitting_radius = fitting_radius,
                        regrid_size = regrid_size,
                        use_moffat = use_moffat,
                        image_params = image_params,
                        fitting_method = fitting_method,
                        hold_pos = hold_psf_position,
                        return_fwhm = True,
                        remove_bkg_local = remove_bkg_local, 
                        remove_bkg_surface = remove_bkg_surface,
                        remove_bkg_poly   = remove_bkg_poly,
                        remove_bkg_poly_degree = remove_bkg_poly_degree,
                        bkg_level = bkg_level)
       
        
  
        psf_params = psf.do(df = psf_fit,
                            residual_image = r_table,
                            ap_size = ap_size,
                            fwhm = fwhm,
                            unity_PSF_counts = unity_PSF_counts,
                            use_moffat = use_moffat,
                            image_params = image_params)
        
        psf_flux = psf_params['psf_counts'].values/exp_time
        psf_flux_err = psf_params['psf_counts_err'].values/exp_time
        psf_bkg_flux = psf_params['bkg'].values/exp_time
        psf_bkg_std_flux = psf_params['noise'].values/exp_time
        psf_heights_flux = psf_params['max_pixel'].values/exp_time
        
    else:
                   
        positions  = list(zip(injection_df.x_pix.values,injection_df.y_pix.values))
    
        psf_counts,psf_counts_err, psf_heights, psf_bkg_counts, psf_bkg_std = measure_aperture_photometry(positions,
                                                      image ,
                                                      ap_size = ap_size    * fwhm,
                                                      r_in   = r_in_size  * fwhm,
                                                      r_out  = r_out_size * fwhm)
            
        psf_flux = psf_counts/exp_time
        psf_flux_err = psf_counts_err/exp_time
        psf_bkg_flux = psf_bkg_counts/exp_time
        psf_bkg_std_flux = psf_bkg_std/exp_time
        psf_heights_flux = psf_heights/exp_time
    

    
    SNR_source = []
    
    for i in range(len(psf_bkg_flux)):
        if psf_bkg_flux[i]>0:
            SNR_source.append(SNR(flux_star = psf_flux[i],
                                 flux_sky = psf_bkg_flux[i],
                                 exp_t = exp_time,
                                 radius = ap_size*fwhm ,
                                 G  = gain,
                                 RN =  rdnoise,
                                 DC = 0 ))
        else:
            SNR_source.append(psf_heights_flux[i]/psf_bkg_std_flux[i])
            
            
    fake_sources_beta = beta_value(n = detection_limit,
                                   sigma = psf_bkg_std_flux,
                                   f_ul  = psf_heights_flux)
    
    SNR_source = np.array([round(num, 1) for num in SNR_source])
    
    # if SNR at a position is greater than detection limit - set the SNR limit at this position to this (higher) limit.
    # SNR_source[(SNR_source < detection_limit) | (np.isnan(SNR_source))] = detection_limit
    
    injection_df['limit_SNR'] = SNR_source
    injection_df['initial_beta'] = fake_sources_beta
    injection_df['initial_noise'] = psf_bkg_std_flux
    injection_df['initial_peak_flux'] = psf_heights_flux
    injection_df['f_ul'] = f_ul(detection_limit,beta_limit,psf_bkg_std_flux)
    


    if not inject_lmag_use_ap_phot:
        
        # update to new positions
        injection_df.rename(columns={"x_pix": "x_pix_OLD",
                                     "y_pix": "y_pix_OLD"})
        
        injection_df['x_pix'] = psf_params['x_pix'].values
        injection_df['y_pix'] = psf_params['y_pix'].values
    
    # check locations with high SNR (due to random noise spikes) and ignore them
    position_SNR_limit = 2
    position_beta_limit = 0.5
    
    if not injected_sources_use_beta :
        print('Checking for suitable SNR [SNR < %.2f]' %  position_SNR_limit)
        good_pos = injection_df.limit_SNR <= position_SNR_limit 
    else:
        
        print('Checking for suitable locations [beta < %.2f]' %  position_beta_limit)
        good_pos = injection_df.initial_beta < position_beta_limit
    
    if np.sum(~good_pos)>0:
        
        if print_progress:
            print('Ignoring %d / %d sources with unsuitable enviroments' % (np.sum(~good_pos),len(good_pos)))
            
        injection_df = injection_df[good_pos]
        
    # SNR_source[(SNR_source < detection_limit) | (np.isnan(SNR_source))] = detection_limit
    
    injection_df.at[injection_df['limit_SNR'].values < detection_limit, 'limit_SNR'] = detection_limit
    
    if np.sum(~good_pos) == len(good_pos):
        
        warning_msg = """\nCould not find any suitable area to testing artifical source injection
        Suggestions:
        1. Increase number of sources
        2. Increase detection threshold
        3. Change injection position
        
        Returning 999
        
        """
        print(warning_msg)
        return 999
        

    cols = get_distinct_colors(len(injection_df))

    # Begin each list for each source - used in plotting
    for k in range(len(injection_df)):
        
        inserted_magnitude [k] = {}
        recovered_magnitude[k] = {}
        recovered_magnitude_e[k] = {}
        injected_f_source[k] = {}
        location_noise[k] = {}
        recovered_f_source[k] = {}
        recovered_fwhm[k] = {}
        recovered_fwhm_e[k] = {}
        recovered_sigma_detection[k] = {}
        recovered_max_flux[k] = {}
        recovered_sources_list[k] = []
        recovered_SNR[k]={}
        delta_recovered_SNR[k]={}
        
        recovered_pos[k] = {}
        SNR_gradient_change[k]={}
        beta_gradient_change[k]={}
        
        beta_probability[k]={}
        
    # magnitude increments - inital set to make sources fainter
    dmag_range = np.linspace(0,dmag*nsteps,int(nsteps+1))

    # Are sources getting brighter or fainter - start off with fainter - swap to negative gradient if sources are initial not detected
    gradient = 1

    # criteria to decide it sources are to be detected or not to find limiting magnitude
    citeria = False

    # initialise limiting magnitude
    inject_lmag = None
    lmag_found = False

    # dmag fine scale - inital parameters
    use_dmag_fine = False
    fine_dmag_range = None
    discrepancy_count = 1
    discrepancy_limit = 3
    
    
    # Inital counter
    ith = 0 
    
    # Initial detection for display purposes
    detect_percentage = 100

    while True:
        try:
        
            if use_dmag_fine and not explore:
                
                # Use small magnitude step size
                dmag_step = gradient*fine_dmag_range[ith]
                 
            else:
                # Use larger step size
                dmag_step =  gradient*dmag_range[ith]
                
            # step labels to keep track of everything
            step_name = round(start_mag+dmag_step+zeropoint,3)

            # Sources are put in one at a time to avoid contamination
            for k in range(len(injection_df)):
                
                inserted_magnitude[k][step_name] = []
                recovered_magnitude[k][step_name] = []
                recovered_magnitude_e[k][step_name] = []
                recovered_fwhm[k][step_name] = []
                
                recovered_fwhm_e[k][step_name] = []
                location_noise[k][step_name] = []
                injected_f_source[k][step_name] = []
                recovered_f_source[k][step_name] = []
                recovered_max_flux[k][step_name] = []
                
                recovered_SNR[k][step_name] = []

                beta_probability[k][step_name] = []
                
                for j in range(redo):
                    
                    if print_progress:
                        print('\rStep: %d / %d :: Source %d / %d :: Iteration  %d / %d :: Mag %.3f :: Sources detected: %d%%' % (ith+1,nsteps,k+1,len(injection_df),j+1,redo,start_mag+dmag_step+zeropoint,detect_percentage),
                               end = '',
                               flush = True)
                    
                    fake_source_on_target = input_model(injection_df['x_pix'].values[k],
                                                        injection_df['y_pix'].values[k],
                                                        mag2image(start_mag+dmag_step))
                    
                   
                   
                    if inject_source_add_noise:
                        
                        # add random possion noise to artifical star
                        nan_idx = np.isnan(fake_source_on_target)
                        neg_idx = fake_source_on_target < 0
            
                        fake_source_on_target[nan_idx] = 0
                        fake_source_on_target[neg_idx] = 0
            
                        fake_source_on_target = apply_poisson_noise(fake_source_on_target)

                    f_injected_source = np.nanmax(fake_source_on_target)/exp_time
                    
                    if not inject_lmag_use_ap_phot and PSF_available:
                                           
                        psf_fit  = psf.fit(image = image + fake_source_on_target,
                                        sources = injection_df.iloc[[k]],
                                        residual_table = r_table,
                                        fwhm = fwhm,
                                        fpath = fpath,
                                        fitting_radius = fitting_radius,
                                        regrid_size = regrid_size,
                                        no_print = True,
                                        use_moffat = use_moffat,
                                        image_params = image_params,
                                        fitting_method = fitting_method,
                                        hold_pos = hold_psf_position,
                                        return_fwhm = True,
                                        remove_bkg_local = remove_bkg_local, 
                                        remove_bkg_surface = remove_bkg_surface,
                                        remove_bkg_poly   = remove_bkg_poly,
                                        remove_bkg_poly_degree = remove_bkg_poly_degree,
                                        bkg_level = bkg_level)
                       
                        
                  
                        psf_params = psf.do(df = psf_fit,
                                            residual_image = r_table,
                                            ap_size = ap_size,
                                            fwhm = fwhm,
                                            unity_PSF_counts =unity_PSF_counts,
                                            use_moffat = use_moffat,
                                            image_params = image_params)
                        
                        psf_counts = psf_params['psf_counts'].values
                        psf_counts_err = psf_params['psf_counts_err'].values
                        psf_bkg_counts = psf_params['bkg'].values
                        psf_bkg_std = psf_params['noise'].values
                        psf_height =  psf_params['max_pixel'].values
                        
                    else:
                    
                        positions  = list(zip(injection_df.iloc[[k]].x_pix.values,injection_df.iloc[[k]].y_pix.values))
                        
                        # print(np.nanmedian(image))
    
                        psf_counts,psf_counts_error,psf_height,psf_bkg_counts,psf_bkg_std = measure_aperture_photometry(positions,
                                                                                                                          image + fake_source_on_target,
                                                                                                                          ap_size = ap_size    * fwhm,
                                                                                                                          r_in   = r_in_size  * fwhm,
                                                                                                                          r_out  = r_out_size * fwhm)
            
                        
                        
                        
                        
                        
                    psf_flux = psf_counts/exp_time
                    
                    psf_flux_err = psf_counts_err/exp_time
                    psf_bkg_flux = psf_bkg_counts/exp_time
                    
                    psf_bkg_std_flux = psf_bkg_std/exp_time
                    psf_height_flux = psf_height/exp_time
                    
             
                    fake_target_beta = beta_value(n=detection_limit,
                                                  sigma = psf_bkg_std_flux,
                                                  f_ul = psf_height_flux)
                
                    
                
                    SNR_source_i = []
                    
                    for i in range(len(psf_bkg_flux)):
                        if psf_bkg_flux[i]>0:
                            SNR_source_i.append(SNR(flux_star = psf_flux[i],
                                                     flux_sky = psf_bkg_flux[i],
                                                     exp_t = exp_time,
                                                     radius = ap_size*fwhm ,
                                                     G  = gain,
                                                     RN =  rdnoise,
                                                     DC = 0 ))
                        else:
                            
                            SNR_source_i.append(psf_heights_flux[i]/psf_bkg_std_flux[i])
                    
                
                    recovered_max_flux[k][step_name].append(psf_height_flux)
                    
                    mag_recovered =  calc_mag(psf_flux)
                    mag_recovered_error = calc_mag(psf_flux) - calc_mag(psf_flux+psf_flux_err)
                    
                    
                    location_noise[k][step_name].append(psf_bkg_std_flux)
                    inserted_magnitude[k][step_name].append(float(start_mag+dmag_step))
                    recovered_magnitude[k][step_name].append(mag_recovered[0])
                    recovered_magnitude_e[k][step_name].append(mag_recovered_error[0])                  
                    recovered_SNR[k][step_name].append(SNR_source_i)
                    beta_probability[k][step_name].append(1-fake_target_beta)
                    injected_f_source[k][step_name].append(f_injected_source)
                    recovered_f_source[k][step_name].append(psf_height_flux)

                   
    
            if subtraction_ready or injected_sources_use_beta:
                
                recovered_sources = np.concatenate([np.array(recovered_max_flux[k][step_name]) >= injection_df['f_ul'].values[k]  for k in range(len(injection_df))])
                
            else:
                
                recovered_sources = np.concatenate([np.array(recovered_SNR[k][step_name]) >= injection_df['limit_SNR'].values[k] for k in range(len(injection_df))])
            
            # For the sources injects - did they pass the recovered test?
            detect_percentage = 100*np.sum(recovered_sources)/len(recovered_sources)
            
            recover_test = np.sum(recovered_sources)/len(recovered_sources) >=  1 - detection_cutout

            recovered_criteria[step_name] = recover_test
    
            # If the first source inject comes back negative on the first interation - flip the dmag steps i.e. fainter -> brighter
            if recovered_criteria[step_name] == citeria and ith == 0 and not use_dmag_fine:
                if print_progress:
                    print('\nInitial injection sources not recovered - injecting brighter sources')
                
                gradient *= -1
                
                citeria = not citeria 
            
            # else if the detection meetings the criteria i.e. sources are (not) detected 
            elif recovered_criteria[step_name] == citeria:
                
                
                if iter_stop == 0 and not use_dmag_fine:
                    if print_progress:
                        print('\n\nApproximate limiting magnitude: %.3f - using finer scale\n' % (zeropoint+start_mag+dmag_step))
                    
                    use_dmag_fine = True
    
                    fine_nsteps = int(1/fine_dmag)+50
                    
                    # reset start magnitude
                    start_mag = start_mag+dmag_step
                    
                    fine_dmag_range =  np.linspace(0,fine_dmag*fine_nsteps,int(fine_nsteps))
                    
                    gradient *= -1
                    
                    citeria = not citeria 
                    
                    # Restart the count
                    ith = 0
                    
                elif iter_stop == 0:
                    
                    if print_progress:
                        print('\n\nLimiting mag found, checking overshoot...\n')
                    
                    # First time finer scale meets criteria, not magnitude
                    inject_lmag = start_mag + dmag_step
                    inject_lmag_minus_1 = start_mag + gradient*fine_dmag_range[ith-1]
                    
                    lmag_found = True
                
                    iter_stop+=1
                    
                else:
                    # print('Resetting...')
                    
                    iter_stop+=1
                
            else:
                
                if lmag_found:
                    if print_progress:
                        print('\n\nOvershoot discrepancy[%d], resetting...\n' % discrepancy_count)
                        discrepancy_count+=1
                if discrepancy_count>discrepancy_limit:
                    pass
                else:
                
                    # didn't meet criteria, keep going
                    lmag_found = False
                    iter_stop = 0
                
            if iter_stop > iter_stop_limit:
                #Done
                if print_progress:
                    print('\nLimiting magnitude: %.3f \n' % ( inject_lmag+zeropoint ))
                    
                
                break
            
            else:
                
                ith = ith + 1
                
                
                
        except Exception as e:
            
            import os,sys
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            # print(exc_type, fname, exc_tb.tb_lineno)
            print('\nInjection failed: ' + str(e) )
            print(exc_type, fname, exc_tb.tb_lineno)
         
            inject_lmag = np.nan
            save_cutouts = False
            
            if ith>nsteps:
                break
            else:
                continue
            # return np.nan

    injection_params = {'inject_mag': inserted_magnitude,
                        'recover_mag': recovered_magnitude,
                        'recover_mag_e': recovered_magnitude_e,
                        'inject_f_source':injected_f_source,
                        'recovered_f_source':recovered_f_source,
                        'recovered_SNR':recovered_SNR,
                        'location_noise':location_noise,
                        'beta':beta_probability}
                 

    if injected_sources_save_output:

        df_dict = {}
        df_dict['source'] = []
    
        for k in range(len(injection_df)):
            
            for param_key, param_values in injection_params.items():
                
                df_dict[param_key] = []
                
                for key,val in param_values.items():

                   val1 = list(val.values())
                   
                   df_dict[param_key]+=[np.mean(i) if not np.isnan(np.mean(i)) else 999 for i in val1 ]
    
            df_dict['source'] += [k] * len(val.values())
            

        # warnings.simplefilter('error', UserWarning)
        recover_df = pd.DataFrame(df_dict)
        saveloc = os.path.join(write_dir,'inject_lmag_'+str(base.split('.')[0])+'.csv')
        recover_df.round(3).to_csv(saveloc)
        


    image_limited = image.copy()



    if save_plot :

        plt.ioff()
        heights = [1,0.5,0.5]
        fig = plt.figure(figsize = set_size(250,2))
        layout = gridspec.GridSpec(ncols=3, 
                                   nrows=3,
                                   figure=fig,
                                   hspace = 0.1,
                                   wspace = 0.1,
                                   
                                   height_ratios=heights,
                                  
                                   )
        # ax1 = fig.add_subplot(layout[0, :])
        ax1 = fig.add_subplot(layout[0, :])
        
        ax2 = fig.add_subplot(layout[1:2, 0:1])
        ax3 = fig.add_subplot(layout[2:3, 0:1])
        
        ax4 = fig.add_subplot(layout[1:2, 1:2])
        
        ax5 = fig.add_subplot(layout[1:2, 2:3])
        ax6 = fig.add_subplot(layout[2:3, 1:2])
        ax7 = fig.add_subplot(layout[2:3, 2:3])
    
    
        x = []
        y = []
        
        cum_detection = {}
            
        ax11 = ax1.twinx()
        
        for i in inserted_magnitude[k].keys():
            
            cum_detection[i] = []
            
            for k in range(len(injection_df)):
            
                # print(subtraction_ready,injected_sources_use_beta)
                if not subtraction_ready and not injected_sources_use_beta:
                    markers, caps, bars = ax1.errorbar(inserted_magnitude[k][i]+zeropoint,
                                                       recovered_SNR[k][i],
                                                      # yerr = recovered_fwhm_e,
                                                       ls = '',
                                                       marker = '.',
                                                       ecolor = 'blue',
                                                       color = cols[k],
                                                       label = r'Recovered SNR')
                    [bar.set_alpha(0.25) for bar in bars]
                    [cap.set_alpha(0.25) for cap in caps]
                    
                    cum_detection[i].append(recovered_SNR[k][i][0])
                    
                else:
                    
        
                    # print('->',inserted_magnitude[k][i],zeropoint)
                    ax1.scatter(inserted_magnitude[k][i]+zeropoint,
                                  1-np.array(beta_probability[k][i]),
                                  marker = '.',
                                  # color = 'cols[k]',
                                  color = 'blue',
                                  label = r"$1-\beta'$")
                    
                    cum_detection[i].append(1-np.array(beta_probability[k][i]))
                    
                    
        for i in inserted_magnitude[k].keys():
            
            if  subtraction_ready or injected_sources_use_beta:
                
                detected_percent = np.sum(np.array(cum_detection[i]) <= beta_limit) / len(cum_detection[i])
                
            else:

                detected_percent = np.sum(np.array(cum_detection[i]) <= detection_limit) / len(cum_detection[i])
                
            
            cum_detection[i] = detected_percent
            
        # print(cum_detection)
        x = np.array(list(cum_detection.keys()))
        idx = np.argsort(x)
        x = x[idx]
        
        y = np.array(list(cum_detection.values()))[idx]/redo
   
        ax11.plot(x,y,
                  color = 'black',
                  marker = 'o',
                  label = 'Cumlative Detections')
                               
        ax11.set_ylim(-0.05,1.05)
        
        # fixing yticks with matplotlib.ticker "FixedLocator"
        ticks_loc = ax11.get_yticks().tolist()
        ax11.yaxis.set_major_locator(ticker.FixedLocator(ticks_loc))
        ax11.set_yticklabels([str(int(x*100))+'%' for x in ticks_loc])

        ax11.hlines(y=detection_cutout,
                    xmin = (inject_lmag+zeropoint),  
                    xmax= ax11.get_xlim()[1],
                    color = 'red',ls = '--')
        
        ax11.vlines(x=(inject_lmag+zeropoint),ymin = -0.05,ymax=detection_cutout ,color = 'red',ls = '--')


        ax11.annotate(r"$M_{lim} \sim %.1f[mag]$" % (inject_lmag+zeropoint),
                      xy=(inject_lmag+zeropoint+0.025,0.025),
            
                           va = 'bottom',
                           ha = 'right',
                          color = 'red',
                           rotation = 90,
                          # fontsize = 5,
                          xycoords = ax11.get_xaxis_transform(),  

                          annotation_clip=False)  
     
        if not subtraction_ready and  not injected_sources_use_beta:
            ax1.axhline(3,
                        color = 'green',
                        ls = '--',
                        label = r'3\\sigma_{bkg}')
            
            ax1.axvline(inject_lmag+zeropoint,
                        color = 'blue',
                        ls = '--',
                        label = r'Detection Limit')
            ax1.set_ylabel(r'Signal to Noise Ratio [$\sigma_{bkg}$]')
            
        else:
            
            ax1.set_ylabel(r"Detection Probability [1-$\beta'$]")
            ax11.set_ylabel(r"Sources lost [%]")
        

        
        ax2.imshow(image,interpolation = None,origin = 'lower') 
        ax2.set_title(r'No fake sources',pad = -0.1,
                      # fontsize = 5
                      )
    
        
        # red_circle = Line2D([0], [0], marker='o',
        #                     # label='Test locations',
        #                     markerfacecolor='none',
        #                     markeredgecolor='black',
        #                     markersize = 3)
        # ax2.legend(handles=[red_circle],
        #            loc = 'upper right',
        #            frameon = False, 
        #            fontsize = 5)
        
        
        for k in range(len(injection_df)):
                
            circle = plt.Circle((injection_df['x_pix'].values[k],injection_df['y_pix'].values[k]),
                                1.3*fwhm, 
                                color=cols[k],
                                ls = '--',
                                lw = 0.25,
                                fill=False)

            ax2.add_patch(circle)
        
        if plot_injected_sources_randomly:
            spaced_sample = sample_with_minimum_distance(n=[int(scale/2),
                                                            int(image.shape[0]-scale/2)
                                                            ], 
                                                         k=4,
                                                         d=int(1.5*fwhm))
            x_spaced = [i[0] for i in spaced_sample]
            y_spaced = [i[1] for i in spaced_sample]

        else:
            x_spaced = injection_df['x_pix'].values[k]
            y_spaced = injection_df['y_pix'].values[k]

    
        for k in range(len(x_spaced)):
            
            fake_source_on_target = input_model(x_spaced[k],
                                                y_spaced[k],
                                                mag2image(inject_lmag))
            
            image_limited+=fake_source_on_target
            
        ax3.imshow(image_limited,
                   interpolation = None,
                   origin = 'lower')

        ax3.set_title('Randomly Injected sources',pad = -0.1)
        
        for ax in [ax3]:
            
            for k in range(len(x_spaced)):
                
                circle = plt.Circle((x_spaced[k],y_spaced[k]),
                                    1.3*fwhm, 
                                    color='black',
                                    ls = '--',
                                    lw = 0.25,
                                    fill=False)
                ax.add_patch(circle)
                
                ax.text(x_spaced[k],y_spaced[k], 
                      str(k), 
                      va = 'center',
                      ha = 'center',
                      # fontsize = 7,
                      color='black',
                      fontsize=5)
                
        closeup_axes = [ax4,ax5,ax6,ax7]
        
        for i in  range(len(closeup_axes)):
            ax = closeup_axes[i]
            fake_source_on_target = input_model(x_spaced[i],
                                                y_spaced[i],
                                                mag2image(inject_lmag))
            
            
            inject_image = image+fake_source_on_target
            
            
            ax.imshow(inject_image[int(y_spaced[i]-scale/2):int(y_spaced[i]+scale/2),
                                   int(x_spaced[i]-scale/2):int(x_spaced[i]+scale/2)],
                      # aspect = 'auto',
                      interpolation = None,
                      origin = 'lower')
            ax.set_title('Position: %d' % i,pad = -0.1)

        ax1.axvline(inject_lmag+zeropoint,color='black',ls=':',alpha=0.5)

        if abs(ax1.get_xlim()[1] - ax1.get_xlim()[0]) <1:
            ax1.xaxis.set_major_locator(ticker.MultipleLocator(fine_dmag))
        else:
            ax1.xaxis.set_major_locator(ticker.MultipleLocator(1))
            ax1.xaxis.set_minor_locator(ticker.MultipleLocator(0.25))
            
        for ax in [ax2,ax4,ax5]:
            pos1 = ax.get_position() # get the original position 
            pos2 = [pos1.x0 , pos1.y0 - 0.1 ,  pos1.width , pos1.height] 
            ax.set_position(pos2) # set a new position
            
        for ax in [ax3,ax6,ax7]:
            pos1 = ax.get_position() # get the original position 
            pos2 = [pos1.x0 , pos1.y0 - 0.15 ,  pos1.width , pos1.height] 
            ax.set_position(pos2) # set a new position
        

       
        if injected_sources_use_beta:
            ax1.set_ylim(-0.05,1.05)
        
        # ax21.set_ylabel(r'$SNR_{i-1} - SNR_{i}$')
        ax1.set_xlabel(r'$M_{Injected}$ [mag]',labelpad = -0.1)
        
        if save_plot_to_folder:
            
            save_loc = os.path.join(write_dir,'lmag_analysis')

            os.makedirs(save_loc, exist_ok=True)
            save_name =  os.path.join(save_loc,'Inject_lmag_'+str(base.split('.')[0])+'_0'+'.pdf' )
            count = 1
            while os.path.exists(save_name):
                fname = 'Inject_lmag_'+str(base.split('.')[0])+'_%d' % count 
                save_name =  os.path.join(save_loc,fname + '.pdf')
                count+=1
            fig.savefig(save_name,bbox_inches = 'tight',format = 'pdf')
        
        
        else:
            
            save_loc = os.path.join(write_dir,'inject_lmag_'+base+'.pdf')
            fig.savefig(save_loc,bbox_inches = 'tight',format = 'pdf')
  
        plt.close(fig)
    


 
    return inject_lmag
    
    
    
    
