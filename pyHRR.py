import datetime
import numpy as np
import pandas as pd
import subprocess
import ConfigParser
import os
import sys

class HRR(object):

    def __init__(self,config,compile_=False):
        """"
            THis is a python-wrapper to handle HRR model in conjunction with a data assimilation module. 
            Small edition of original source code was performed.
            v.1.0.0: Daily simulation.
            Coding: Yuta Ishitsuka
        """
        # read input info. for HRR.
        self.config = ConfigParser.ConfigParser()
        self.config.read(config)

        # compile or not
        if compile_:
            self.__compile()

        # file name configuration
        self.exe = "./run"


    def __compile(self):
        
        print "compilation is activated. Make clean/all."
        os.chdir("./src")
        print "make clean"
        subprocess.check_call(["make","clean"])
        print "make all"
        subprocess.check_call(["make","all"])
        os.chdir("../")


    def __createInputFile(self,date):

        roffData = "../data/case6/%s.txt"%(date.strftime("%Y%m%d"))
        restFile = "./restart.txt"
        pfafunits = self.config.get("input","pfafunits")
        ndx = self.config.get("input","ndx")
        ndt = 24 # for future improvement
        dtis = 3600 # for future improvement
        self.outerDt = dtis*ndt
        iyear = date.year
        imonth = date.month
        iday = date.day
        doy = (date - datetime.datetime(date.year,1,1,0)).days + 1
        sbRate = self.config.get("input","sbRate")
        n_ch_all = self.config.get("input","n_ch_all")

        VARS = ["pfafunits","ndx","ndt","dtis","iyear","imonth","iday","Julian Day","setfsub_rate","n_ch_all"]
        VALS = {"pfafunits":pfafunits,"ndx":ndx,"ndt":ndt,"dtis":dtis,"iyear":iyear,"imonth":imonth,"iday":iday,"Julian Day":doy,"setfsub_rate":sbRate,"n_ch_all":n_ch_all}

        with open("./src/input.txt",mode="w") as f:
            f.write("%s\n"%roffData)
            f.write("%s\n"%restFile)
            [f.write("%s    %s\n" % (str(VALS[var]),var)) for var in VARS]


    def main_day(self,date,flag="restart"):
        """
            main API to handle HRR
        """
        
        # check operation mode
        if flag == "initial":
            print "initial mode is activated. Initialize reaches"
            print date
        elif flag == "restart":
            print date
        else:
            raise IOError("Undefined flag mode %s"%flag)

        # create input information file for HRR
        self.__createInputFile(date)

        # activate HRR
        os.chdir("./src")
        subprocess.check_call([self.exe, flag])
        os.chdir("../")

        nDate = date + datetime.timedelta(seconds = self.outerDt)
        out = pd.read_csv("src/discharge_cms.txt",header=0,sep="\s+").rename(index={0:date})
        print(out)

        return out, nDate


if __name__ == "__main__":

    config = "./config.ini"
    compile_ = True
    model = HRR(config,compile_=compile_)
    date = datetime.datetime(1990,1,1,0)
    model.main_day(date,flag="initial")
    date = date + datetime.timedelta(days=1)
    while date < datetime.datetime(1991,1,1,0):
        model.main_day(date,flag="restart")
        date = date + datetime.timedelta(days=1)