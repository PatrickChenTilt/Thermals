import pandas as pd
import datetime
import equip_loading_tools as eql
import numpy as np
import time

def main(in_psse_folder,in_windP_filepath,MW_max):

    # Script reads the measured wind power and adjusts the generaor MW accordingly for each psse snapshots time
    # Revision date:        2022-10-11
    # Revisiion details:    sometimes the windseries gap is too big so the extrapulated results would exceed the maximum WF, set this to max and investigate
    # Inputs:
    # make sure the input wind power us a csv and have 2 columns,
    # Col1 =  Format: datetime (dd/mm/yyyy hh:mm), title can be anything
    # Col2 =  Power (MW), format: float, title can be anything
    # make sure the wind Power data only has 1 year worth of data, 365 days, unique datetime


    # input folder name = directory where the psse snapshots stored
    # in_windP_filepath = points directly to the windpower datetime series csv file
    Ts = time.time()

    rawfile_dir = eql.find_files('.raw', in_psse_folder)[0]
    rawfilenames = eql.find_files('.raw', in_psse_folder)[1]
    psse_list = psse_list_datetime(rawfilenames) # extract the psse model time from filename
    psse_list = pd.DataFrame(psse_list, columns=['Datetime']) # make new dataframe
    psse_list['Datetime'] = pd.to_datetime(psse_list['Datetime'], format='%Y%m%d-%H%M%S') # convert to datetime format
    psse_list["Datetime"] = psse_list["Datetime"].apply(lambda x: x.replace(year=2020)) # resset the years so year mismtach is not a problem

    windP = pd.read_csv(in_windP_filepath)  #
    windP[windP.columns[0]] = pd.to_datetime(windP[windP.columns[0]], format='%d/%m/%Y %H:%M', dayfirst=True)
    windP[windP.columns[0]] = windP[windP.columns[0]].apply(lambda x: x.replace(year=2020)) # resset the years so year mismtach is not a problem
    windP = windP.sort_values(by=windP.columns[0])
    windP = windP.reset_index(drop=True)

    # convert to series because dataframe looping is slow
    wind_timeseries = windP[windP.columns[0]].astype('datetime64[ns]')
    wind_Powerseries = windP[windP.columns[1]]
    psse_timeseries = psse_list['Datetime'].astype('datetime64[ns]')

    powerList = []

    for time_psse in psse_timeseries:

        Tpsse = time_psse
        Index_next = np.where(time_psse < wind_timeseries)[0][0]
        Index_prev = Index_next - 1
        Pnext = wind_Powerseries[Index_next]
        Pprev = wind_Powerseries[Index_prev]
        Tnext = wind_timeseries[Index_next]
        Tprev = wind_timeseries[Index_prev]
        Grad = (Pnext - Pprev) / (Tnext - Tprev).seconds  # MW/sec
        DeltaT = (Tpsse - Tprev).seconds
        MW_WF = Pprev + DeltaT * Grad

        if MW_WF > MW_max:
            MW_WF = MW_max
            print('warning: estimated MW exceeded maximum MW, check input data')

        powerList.append(MW_WF)

    return rawfile_dir,powerList

def psse_list_datetime(psse_list):
    # script extracts the date time off the psse filename list (not directory list)
    list = ['-'.join(snp.split('-',2)[:2]) for snp in psse_list]
    return list