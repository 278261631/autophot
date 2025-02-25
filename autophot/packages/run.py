#!/usr/bin/env python3
# -*- coding: utf-8 -*-
def run_autophot(autophot_input):
    '''
    Function to run on image dataset and setup list of files for use in AutoPHOT.
    This function performs the following tasks:
    
    1. Searches through a given file path and makes list of acceptable images to
    use.  This script will look for files with the following extension:
    
    
    1. *.fist*
    2. *.fit*
    3. *.fts* 
    4. *fits.fz*
    
    Science images must not include the following in their filepath as these
    filenames are used later on in AutoPHOT (and will end with the same extension
    as the input image) and may cause errors:
    
    1. *subtraction*
    2. *template*
    3. *.wcs.* 
    4. *footprint*
    5. *PSF_model_*
    6. *sources_*
    
    2. Run through this filelist and check if the correct information is available
    in the *telescope.yml file using the *checkteledata* function.
    
    3. If a Transient Name Server (TNS) bot isavailable, return the latest
    coordinates of a given target.
    
    4. Search though the file list and remove any file that has an *IMAGETYP* of
    *bias*, *zero*, *flat*, *WAVE* , or *LAMP*  or an *OBS_MODE* of
    *spectroscopy*.
    
    5. Run the final file list through the AutoPHoT pipeline
    
    
    See `here
    <https://github.com/Astro-Sean/autophot/blob/master/example_notebooks/basic_example.ipynb>`_
    for an example.
    
    :param autophot_input: AutoPHOT input dictionary
    :type autophot_input: dict
    :return: Creates a csv file containing photometric data for transient indataset
    :rtype: Dataframe saved to work directory

    '''

    from autophot.packages.functions import getheader
    from autophot.packages.check_tns import get_coords
    from autophot.packages.call_yaml import yaml_autophot_input as cs
    from autophot.packages.call_datacheck import checkteledata
    from autophot.packages.main import main

    import os
    import sys
    import pathlib
    import pandas as pd
    import numpy as np
    from functools import reduce
    import logging
    from autophot.packages.functions import border_msg


    logger = logging.getLogger(__name__)


    flist_new = []
    files_removed = 0
    filter_removed = 0
    wrong_file_removed = 0

    # Create new directory within working directory

    # Remove backslash if it is given
    if autophot_input['fits_dir'].endswith('/'):
        autophot_input['fits_dir'] = autophot_input['fits_dir'][:-1]


    if not autophot_input['template_subtraction']['prepare_templates']:

        flist = []

        new_dir = '_' + autophot_input['outdir_name']
        base_dir = os.path.basename(autophot_input['fits_dir']).replace(new_dir,'')
        work_loc = base_dir + new_dir

        work_fpath = os.path.join(autophot_input['fits_dir'],work_loc)
        pathlib.Path(os.path.dirname(work_fpath)).mkdir(parents = True, exist_ok=True)
        os.chdir(os.path.dirname(work_fpath))

        # Search for .fits files with template or subtraction in it
        # TODO: What a silly bit of code - clean this up
        for root, dirs, files in os.walk(autophot_input['fits_dir']):
            for fname in files:
                if fname.endswith((".fits",'.fit','.fts','fits.fz')):
                    if 'templates' not in root and 'template' not in autophot_input['fits_dir']:
                        if 'template' not in fname and 'template' not in autophot_input['fits_dir'] :
                            if 'subtraction' not in fname:
                                if '.wcs' not in fname:
                                    if 'PSF_model' not in fname:
                                        if 'footprint' not in fname:
                                            if 'sources_' not in fname:
                                                flist.append(os.path.join(root, fname))
    else:
        flist = []
        new_dir = '_' + autophot_input['outdir_name']
        base_dir = os.path.basename(autophot_input['fits_dir']).replace(new_dir,'')
        work_loc = base_dir + new_dir

        template_loc = os.path.join(autophot_input['fits_dir'],'templates')
        for root, dirs, files in os.walk(template_loc):
            for fname in files:
                if fname.endswith((".fits",'.fit','.fts','fits.fz')):
                    if 'PSF_model' not in fname and '.wcs' not in fname:
                        flist.append(os.path.join(root, fname))


    files_completed = False

    if autophot_input['restart'] and not autophot_input['template_subtraction']['prepare_templates']:

        # Pick up where left out in output folder
        flist_before = []

        for i in flist:

            path, file = os.path.split(i)

            file_nodots,file_ext = os.path.splitext(file)

            # remove dots and replace with underscores while ignoring extension
            file_nodots = file_nodots.replace('.','_')

            file = file_nodots + file_ext

            clean_path = os.path.join(path, file).replace('_APT','').replace(' ','_').replace('_'+autophot_input['outdir_name'],'')

            clean_path_split = list(clean_path.split('/'))

            sub_dirs = list(dict.fromkeys([i.replace(file_ext,'') for i in clean_path_split]))
            clean_path = '/'.join(sub_dirs)
            clean_fpath = os.path.join(clean_path,file.replace('_APT',''))

            flist_before.append(clean_fpath)


        len_before = len(flist)

        print('\nRestarting - checking for files already completed in:\n%s' % (autophot_input['fits_dir']+'_'+autophot_input['outdir_name']).replace(' ',''))

        flist_restart = []

        ending = '_'+autophot_input['outdir_name']

        output_folder = autophot_input['fits_dir']+ending

         #Look in output directory e..g REDUCED folder
        for root, dirs, files in os.walk(output_folder.replace(' ','')):

            for fname in files:

                if '_APT.f' in fname:

                    if os.path.isfile(os.path.join(root, fname)) and os.path.isfile(os.path.join(root,'out.csv')):


                        dirpath_clean_up = os.path.join(root, fname).replace(ending,'')

                        path,file = os.path.split(dirpath_clean_up)

                        clean_path = path.split('/')

                        clean_path_new = '/'.join(clean_path) + '/'+file


                        flist_restart.append(clean_path_new.replace('_APT','').replace(' ','_').replace('_'+autophot_input['outdir_name'],''))

        if len(flist_before) == 0:

            print('No ouput files found - skipping ')

        else:

            flist_bool = [False if f in flist_restart else True for f in flist_before]

            flist = list(np.array(flist)[np.array(flist_bool)])

            len_after = len(flist)

            print('\nTotal Files: %d' % len_before)

            files_completed = len_before - len_after

            print('\nFiles already done: %d' %  files_completed)

            files_removed += len_before - len_after

    # Go through files, check if I have their details
    available_filters = []

    # =============================================================================
    #   Check that we have all the needed information
    # =============================================================================
    
    checkteledata(autophot_input,flist)

    # =============================================================================
    # Import catalog specific naming conventions installed during autophot installation
    # For new catalog: please email sean.brennan2@ucdconnect.ie
    # =============================================================================
    
    
    filepath ='/'.join(os.path.os.path.dirname(os.path.abspath(__file__)).split('/')[0:-1])
    catalog_autophot_input_yml = 'catalog.yml'
    
    
    catalog_autophot_input = cs(os.path.join(filepath+'/databases',catalog_autophot_input_yml),
                                autophot_input['catalog']['use_catalog']).load_vars()


    #  If catalog set to cutsom
    if autophot_input['catalog']['use_catalog'] == 'custom':
        target = autophot_input['target_name']
        fname = str(target) + '_RAD_' + str(float(autophot_input['catalog']['catalog_radius']))

        if not autophot_input['catalog']['catalog_custom_fpath']:
            logger.critical('Custom catalog selected but "catalog_custom_fpath" not defined')
            exit()
        else:
            fname = autophot_input['catalog']['catalog_custom_fpath']

        custom_table_data = pd.read_csv(fname)
        
        available_filters = [i for i,_ in catalog_autophot_input.items() if i in list(custom_table_data.columns)]
    else:
        
        
        available_filters = [i for i,_ in catalog_autophot_input.items()]


    # =============================================================================
    # Include IR sequence points
    # =============================================================================
    
    if autophot_input['catalog']['include_IR_sequence_data']:
        available_filters+=['J','H','K']
        available_filters = list(set(available_filters))


    # =============================================================================
    # load telescope data - User shoud include this in setup
    # =============================================================================

    tele_autophot_input_yml = 'telescope.yml'
    tele_autophot_input = cs(os.path.join(autophot_input['wdir'],tele_autophot_input_yml)).load_vars()

    # =============================================================================
    # Checking for target information
    # =============================================================================


    target_name = autophot_input['target_name']

    pathlib.Path(os.path.join(autophot_input['wdir'],'tns_objects')).mkdir(parents = True, exist_ok=True)

    if autophot_input['target_name'] != None and autophot_input['wcs']['TNS_BOT_ID'] != None:

        transient_path = reduce(os.path.join,[autophot_input['wdir'],'tns_objects',(target_name)+'.yml'])

        if os.path.isfile(transient_path):
            print('\nFound TNS information for  %s' % autophot_input['target_name'])


            TNS_response = cs(transient_path,target_name).load_vars()

        else:
            try:
                print('\nChecking TNS for %s information' % autophot_input['target_name'])


                # Retreive the data
                TNS_response = get_coords(objname = target_name,
                                          TNS_BOT_ID = autophot_input['wcs']['TNS_BOT_ID'],
                                          TNS_BOT_NAME = autophot_input['wcs']['TNS_BOT_NAME'],
                                          TNS_BOT_API = autophot_input['wcs']['TNS_BOT_API'])

                # create a yaml file with object information
                cs.create_yaml(transient_path,TNS_response)

            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname1 = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname1, exc_tb.tb_lineno,e)
                sys.exit("Can't reach Server - Check Internet Connection!")

    elif autophot_input['target_ra'] != None and autophot_input['target_dec'] != None:

        TNS_response = {}
        TNS_response['ra'] = autophot_input['target_ra']
        TNS_response['dec'] = autophot_input['target_dec']


    else:
        continue_response = (input('No access to TNS and no RA/DEC given - do you wish to continue? [y/[n]]') or 'n')

        if continue_response != 'y':
            raise Exception('No target information given and user wants to quit')
        else:
            TNS_response = {}

    # =============================================================================
    # Checking that selected catalog has appropiate filters - if not remove
    # =============================================================================

    print('\nChecking Filter information for each image')

    no_filter_list = []


    for name in flist:

        root = os.path.dirname(name)

        fname = os.path.basename(name)

        if autophot_input['template_subtraction']['prepare_templates'] and 'PSF_model' in fname:
            continue

        try:
            headinfo = getheader(name)

            try:
                tele = str(headinfo['TELESCOP'])
                inst_key = 'INSTRUME'
                inst = str(headinfo[inst_key])
            except:
                if autophot_input['ignore_no_telescop']:
                    tele = 'UNKNOWN'
                    print('Telescope name not given - setting to UNKNOWN')
                else:
                    print('Available TELESCOP:\n%s' % tele_autophot_input.keys())
                    tele = input('TELESCOP NOT FOUND; Enter telescope name: ')

            if tele.strip() == '':
                tele = 'UNKNOWN'
                headinfo['TELESCOP'] = tele



            # Default filter key name
            filter_header = 'filter_key_0'

            '''
            Go through filter keywords filter_key_[1..2..3..etc] looking for one that works
            '''
            avoid_keys = ['clear','open']
            open_filter = False
            found_correct_key = False

            filter_keys = [i for i in list(tele_autophot_input[tele][inst_key][inst]) if i.startswith('filter_key_')]

            for filter_header_key in filter_keys:
                # find the correct filter ket per image

                if tele_autophot_input[tele][inst_key][inst][filter_header_key] not in list(headinfo.keys()):
                    continue

                if headinfo[tele_autophot_input[tele][inst_key][inst][filter_header_key]].lower() in avoid_keys:
                    open_filter = True
                    continue

                if headinfo[tele_autophot_input[tele][inst_key][inst][filter_header_key]] in tele_autophot_input[tele][inst_key][inst]:
                    found_correct_key = True
                    break


            if autophot_input['ignore_no_filter']:
                if open_filter and not found_correct_key:
                    print('no filter ')
                    continue

            try:
                fits_filter = headinfo[tele_autophot_input[tele][inst_key][inst][filter_header_key]]
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname1 = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname1, exc_tb.tb_lineno,e)
                print('''***Filter filter header not found***''' )
                fits_filter = 'no_filter'

            try:
                filter_name = tele_autophot_input[tele][inst_key][inst][str(fits_filter)]
            except:
                filter_name = str(fits_filter)

            if 'IMAGETYP' in  headinfo:
                for i in ['bias','zero','flat','WAVE','LAMP']:

                    if i in  headinfo['IMAGETYP'].lower():
                        wrong_file_removed+=1
                        files_removed+=1
                        continue

            if 'OBS_MODE' in  headinfo:
                for i in ['SPECTROSCOPY']:
                    if i in  headinfo['IMAGETYP'].lower():
                        wrong_file_removed+=1
                        files_removed+=1
                        continue

            if not filter_name in available_filters and not autophot_input['template_subtraction']['prepare_templates'] :
                files_removed+=1
                filter_removed+=1
                no_filter_list.append(filter_name)
                continue

            if autophot_input['select_filter'] and not autophot_input['template_subtraction']['prepare_templates']:

                if str(tele_autophot_input[tele][inst_key][inst][str(fits_filter)]) not in autophot_input['do_filter']:
                    files_removed+=1
                    filter_removed+=1
                    no_filter_list.append(filter_name)
                    continue


            flist_new.append(name)

        except Exception as e:

            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname1 = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname1, exc_tb.tb_lineno,e)

            # print([tele,inst_key,inst])
            continue

    flist = flist_new

    print('\nFiles removed - Wrong Image Type: %d' % wrong_file_removed)

    print('\nFiles removed - No/Wrong filter(s): %d\nFilters not included: %s\n' % (filter_removed,str(list(set(no_filter_list))).replace("'","")))

    print('\nFiles removed: %d' % files_removed)

    if files_completed:
        print('\nFiles already done: %d' % files_completed)

    if len(flist) > 1000:
        ans = str(input('> More than 1000 .fits files [%s] -  do you want to continue? [[y]/n]: ' % len(flist)) or 'y')
        if  ans == 'n':
            raise Exception('Exited AutoPHoT - file number size issue')


# =============================================================================
# Single processing chain
# =============================================================================
    if autophot_input['template_subtraction']['prepare_templates']:

        # TNS_response = {}

        print('\n------------------------')
        print('Preparing Template Files')
        print('------------------------')



    if autophot_input['method'] == 'sp':
        import gc

        # single process output list
        sp_output = []
        n=0
        for i in (flist):

            n+=1

            border_msg('File: %s / %s' % (n,len(flist)))

            # Enter into AutoPhOT
            out = main(TNS_response,autophot_input,i)
            gc.collect()

            # Append to output list
            sp_output.append(out)

        if not autophot_input['template_subtraction']['prepare_templates']:
            # Create new output csv file
            with open(str(autophot_input['outcsv_name'])+'.csv', 'a'): pass

            # Successful files
            sp_output_data = [x[0] for x in sp_output if x[0] is not None]

            # Files that failed
            output_total_fail = [x[1] for x in sp_output if x[0] is None]

            print('\n---')
            print('\nFiles that failed :',output_total_fail)

            # failurefile = os.path.join(autophot_input['write_dir'],)

            if len(output_total_fail)!=0:
                with open('FailedFiles.dat', 'w') as f:
                    for fail in output_total_fail:
                        f.write('> %s\n' % fail)

            '''
            Dataframe of output parameters from recent instance of AutoPhOT

            - will be concatinated with any previous excuted output files
            '''
            new_entry = pd.DataFrame(sp_output_data)
            new_entry = new_entry.applymap(lambda x: x if isinstance(x, list) else x )

        else:

            print('\n------------------------------------------------------------')
            print('Templates ready - Please check to make sure they are correct')
            print("set 'prepare_templates' to False and execute")
            print('------------------------------------------------------------')

        if not autophot_input['template_subtraction']['prepare_templates']:
            # Try to open an pre-existing data, if not make a new one
            try:
                data = pd.read_csv(str(autophot_input['outcsv_name']+'.csv'))
                update_data = pd.concat([data,new_entry],axis = 0,sort = False,ignore_index = True)
            except:
                update_data = new_entry


            update_data.to_csv(autophot_input['outcsv_name']+'.csv',index = False)


        print('\nDONE')

        return

    # =============================================================================
    #  Parallelism execution - work in progress - doesn't work right now
    # =============================================================================

    if autophot_input['method'] == 'mp':
        raise Exception('This is untested - please using method == sp for the time ebing')

        import multiprocessing

        import os
        import signal
        from functools import partial
        from tqdm import tqdm

        def main_mp():



            original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)

            pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())

            signal.signal(signal.SIGINT, original_sigint_handler)

            func = partial(main, TNS_response, autophot_input)

            chunksize, extra = divmod(len(flist) , 4 * multiprocessing.cpu_count())
            if extra:
                chunksize += 1

            print('\n'+'Chunksize:' ,chunksize)

            mp_output = []
            try:
                try:
                    for n in tqdm(pool.imap_unordered(func, flist,chunksize = chunksize), total=len(flist)):
                        mp_output.append(n)
                        pass

                except KeyboardInterrupt:
                    print('Early Termination')
                    print(pool._pool)
                    pool.terminate()

                    for p in pool._pool:
                       if p.exitcode is None:
                           p.terminate()
            except Exception as e:

                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname1 = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname1, exc_tb.tb_lineno,e)

            pool.close()
            pool.join()

            for p in pool._pool:
               if p.exitcode is None:
                   p.terminate()

            with open(str(autophot_input['outcsv_name'])+'.csv', 'a'):
                    pass

            mp_output_data = [x[0] for x in mp_output if x[0] is not None]

            output_total_fail = [[x[1] for x in mp_output if x[0] is None]]

            print('\nTotal failure :',output_total_fail)

            new_entry = pd.DataFrame(mp_output_data)
            new_entry = new_entry.applymap(lambda x: x if isinstance(x, list) else x )

            try:
                data = pd.read_csv(str(autophot_input['outcsv_name']+'.csv'),error_bad_lines=False)
                update_data = pd.concat([data,new_entry],axis = 0,sort = False,ignore_index = True)
            except pd.io.common.EmptyDataError:
                update_data = new_entry
                pass


            try:
                update_data.to_csv(str(autophot_input['outcsv_name']+'.csv'),index = False)
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname1 = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname1, exc_tb.tb_lineno,e)
                print('CANNOT UPDATE OUTPUT CSV')

            print()
            print('DONE')
            return
        main_mp()






def recover(fits_dir,outdir_name='REDUCED',outcsv_name='REDUCED',
            infile_name = 'out.csv',update_fpath = True,print_msg = True):
    '''
    
            Iterate through output folder given by *fits_dir* and *outdir_name*, search for files corresponding to *outfile_name* and concatenate into a single file named *outcsv_name*
    
    :param fits_dir: Location of original directory containing *FITS* images
    :type fits_dir: str
    :param outdir_name: Name of output directory concatenation i.e. what is the name concatenated onto the parent directory from *fits_dir*, defaults to 'REDUCED'
    :type outdir_name: ste, optional
    :param outcsv_name: Name of file to save data which will be saved in *outdir_name*, defaults to 'REDUCED'
    :type outcsv_name: str, optional
    :param infile_name: Name of output file which contains photometric information on each image, defaults to 'out.csv'
    :type infile_name: str, optional
    :param update_fpath: If True, make sure the "*fpath*" variable in *outcsv_name* is correct, defaults to True
    :type update_fpath: bool, optional
    :param print_msg: If True print a message saying that the script is working, defaults to True
    :type print_msg: bool, optional
    :return: Produces an output csv file with the name given by *outcsv_name* in the directory given by *fits_dir* with *outdir_name* appended onto it.
    :rtype: TYPE
    

    '''



    import pandas as pd
    import os,sys
    from autophot.packages.functions import border_msg
    
    if print_msg:
        border_msg('Recovering output files')


    if fits_dir.endswith('/'):
        fits_dir = fits_dir[:-1]

    recover_dir = fits_dir + '_' + outdir_name

    csv_recover = []
    
    if not  os.path.isdir(recover_dir):
        print('%s not found !' % recover_dir)
        
        recover_dir = fits_dir
        
        print('Looking in %s ' % recover_dir)
        
    if print_msg:
        print('Recovering Output from %s...' % recover_dir)
    
    for root, dirs, files in os.walk(recover_dir):
        for fname in files:
            if fname.endswith((".fits",'.fit','.fts','fits.fz')):


                if os.path.isfile(os.path.join(root, infile_name)):
                    csv = pd.read_csv(os.path.join(root, infile_name))
                    
                    if update_fpath:
                        old_fpath = csv['fname'].values[0]
                        image_fname = os.path.basename(old_fpath)
                        new_fpath = os.path.join(root,image_fname)
                        csv['fname'] = new_fpath
                        
                    csv_recover.append(csv)
                

                else:
                    # print('No output found for: %s' % fname)
                    pass
    try:

        data = pd.concat(csv_recover,axis = 0,sort = False,ignore_index = True)

        data.drop_duplicates(subset='fname', keep="last",inplace = True)

        for col in data.columns:
            if 'Unnamed' in col:
                del data[col]

        output_file = os.path.join(recover_dir, str(outcsv_name) + '.csv')

        data.round(6).to_csv(output_file,index = False)

        print('\nData recovered :: Output File:\n%s' % output_file)


    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno,e)
        print('> Data not saved <')
        
        
        