import configparser
import datetime
import os
import subprocess
import sys

import numpy as np
import pandas as pd


class HRR(object):
    def __init__(self, config, compile_=False):
        """"
            THis is a python-wrapper to handle HRR model in conjunction with a data assimilation module.
            Small edition of original source code was performed.
            v.1.0.0: Daily simulation.
            Coding: Yuta Ishitsuka
        """
        # read input info. for HRR.
        self.config = configparser.ConfigParser()
        self.config.read(config)
        self.rootDir = self.config.get("model", "rootDir")

        # file name configuration
        self.srcDir = os.path.join(self.rootDir, "src/")
        self.exe = os.path.join(self.srcDir, "run")

        # compile or not
        if compile_:
            self.__compile()

    def __compile(self):

        print("compilation is activated. Make clean/all.")
        os.chdir(self.srcDir)
        print("make clean")
        subprocess.check_call(["make", "clean"])
        print("make all")
        subprocess.check_call(["make", "all"])
        os.chdir(self.rootDir)

    def __createInputFile(self, date, runoffDir, restart, mode, outDir):

        assimUpdate = mode
        roffData = os.path.join(runoffDir,
                                "%s.txt" % (date.strftime("%Y%m%d")))
        restFile = restart
        pfafunits = self.config.get("input", "pfafunits")
        ndx = self.config.get("input", "ndx")
        ndt = 24 # for future improvement
        dtis = 3600  # for future improvement
        self.outerDt = dtis * ndt
        iyear = date.year
        imonth = date.month
        iday = date.day
        doy = (date - datetime.datetime(date.year, 1, 1, 0)).days + 1
        sbRate = self.config.get("input", "sbRate")
        n_ch_all = self.config.get("input", "n_ch_all")

        VARS = [
            "pfafunits", "ndx", "ndt", "dtis", "iyear", "imonth", "iday",
            "Julian Day", "setfsub_rate", "n_ch_all"
        ]
        VALS = {
            "pfafunits": pfafunits,
            "ndx": ndx,
            "ndt": ndt,
            "dtis": dtis,
            "iyear": iyear,
            "imonth": imonth,
            "iday": iday,
            "Julian Day": doy,
            "setfsub_rate": sbRate,
            "n_ch_all": n_ch_all
        }

        self.infoPath = os.path.join(outDir, "input.txt")
        with open(self.infoPath, mode="w") as f:
            f.write("%s\n" % assimUpdate)
            f.write("%s\n" % self.srcDir)
            f.write("%s\n" % roffData)
            f.write("%s\n" % restart)
            f.write("%s\n" % outDir)
            [f.write("%s    %s\n" % (str(VALS[var]), var)) for var in VARS]

    def output(self, df, oName, mode="a"):

        if mode == "w":
            with open(oName, "w") as f:
                df = df.reset_index().rename({"index": "Date"}, axis=1)
                df.to_csv(f, index=False)
        elif mode == "a":
            with open(oName, "a") as f:
                df.to_csv(f, header=False)
        else:
            raise IOError("mode %s is unsupported." % mode)

    def main_day(self,
                 date,
                 flag="restart",
                 restart="restart.txt",
                 runoffDir="../data/case6/",
                 mode="normal",
                 outDir="./out"):
        """
            main API to handle HRR
        """

        # check operation mode
        if not flag == "initial" and not flag == "restart":
            raise IOError("Undefined flag mode %s" % flag)

        # create input information file for HRR
        self.__createInputFile(date, runoffDir, restart, mode, outDir)

        # activate HRR
        subprocess.check_call([self.exe, flag, self.infoPath])

        nDate = date + datetime.timedelta(seconds=self.outerDt)
        out = pd.read_csv(os.path.join(outDir, "discharge_cms.txt"),
                          header=0,
                          sep="\s+").rename(index={0: date})

        return out, nDate


if __name__ == "__main__":

    config = "./config.ini"
    compile_ = True
    runoffDir = "/home/yi79a/DA/missouli/pyHRR/data/case3/00/"
    outDir = "/home/yi79a/DA/missouli/pyHRR/src/out"
    if not os.path.exists(outDir):
        os.makedirs(outDir)
    model = HRR(config, compile_=compile_)
    date = datetime.datetime(1990, 1, 1, 0)
    out, nDate = model.main_day(date,
                                flag="initial",
                                runoffDir=runoffDir,
                                outDir=outDir)
    model.output(out, "./test.csv", mode="w")
    date = nDate
    eDate = datetime.datetime(1990, 1, 5, 0)
    while date < eDate:
        out, nDate = model.main_day(date,
                                flag="restart",
                                runoffDir=runoffDir,
                                outDir=outDir)
        date = nDate
        model.output(out, "./test.csv", mode="a")
