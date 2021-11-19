import argparse
from argparserlib.svgtoolargparser import *
import configparser
import re
import os
from subprocess import check_output as qx

# This is a sample Python script.

# Press Umschalt+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generates images for laser cut/engrave tests')

    parser.add_argument('-c', '--configfile', type=str, required=True,
                        help='list of file names with parameters')
    parser.add_argument('-o', '--outputfolder', type=str, required=True,
                        help='The folder to write out all the results (an SVG, an INI and a GCode file)')
    args = parser.parse_args()

    if args.configfile:
        config = configparser.ConfigParser()
        config.read(args.configfile)


    comb = lambda s, n: (s[i:i + n] for i in range(0, len(s), n))

    circleblockregex = re.compile('(<g\n.*\n.*\n.*{LAYERLABELPARAM.*\n(.*\n)*?.*/g>)', flags=re.MULTILINE)
    textblockregex = re.compile('(<g.*\n(.*\n){2}.*label="Text.*\n(.*\n)*?.*g>)', flags=re.MULTILINE)
    xparamregex = re.compile('\{XPARAM\}')
    yparamregex = re.compile('\{YPARAM\}')
    layerlabelparamregex = re.compile('\{LAYERLABELPARAM\}')
    fparamregex = re.compile('\{FPARAM\}')

    with open("templates/oval.svgtemplate") as fp:
        data = fp.read()
        fp.close()

    circleblock = circleblockregex.search(data).group(1)
    textblock = textblockregex.search(data).group(1)
    circles = ""
    texts = ""
    iniblock="[Material.NewTextLayer]\n"
    iniblock +="strength = 100\n"
    iniblock += "speed = 100\n"
    iniblock += "[Material.Bounds]\n"
    iniblock += "strength = 100\n"
    iniblock += "speed = 100\n"

    xstart = 5
    ystart = 15
    runningx = xstart
    runningy = ystart
    xgap = 10
    ygap = 15

    for section in config.sections():
        s = config[section]["S"]
    #    [Verkleidung.Cut]
    #    speed = 300
    #    strength = 950

        inarr = config[section]["F"].split(",");
        cols = int(config[section]["cols"]);
        rows = int(len(inarr) / cols)
        rows = groups_leap = [inarr[i::rows] for i in range(rows)]

        newtextblock = xparamregex.sub(str(runningx), yparamregex.sub(str(runningy-10), fparamregex.sub(
            "S"+s, textblock)))
        #runningy+=5

        texts += "\n" + newtextblock
        for row in rows:
            for num in row:
                num = num.strip()

                iniblock += "[Material.S" + s + "F" + str(num)+"]\n"
                iniblock += "strength = " + s + "\n"
                iniblock += "speed = " + str(num) + "\n"

                newcircleblock = xparamregex.sub(str(runningx), yparamregex.sub(str(runningy), layerlabelparamregex.sub(
                    str("S" + s + "F" + str(num)), circleblock)))

                circles += "\n" + newcircleblock

                newtextblock = xparamregex.sub(str(runningx - 4), yparamregex.sub(str(runningy - 5), fparamregex.sub(
                    str(str(num)), textblock)))
                texts += "\n" + newtextblock

                runningx += xgap

            runningy += ygap
            runningx = xstart
        runningy += ygap/2

    res = circleblockregex.sub(circles, textblockregex.sub(texts, data))

    if not os.path.exists(args.outputfolder):
        os.makedirs(args.outputfolder)

    svgfile = os.path.join(args.outputfolder,
                           "input_oval.svg")

    with open(svgfile, 'w') as fp:
        fp.write(res)
        fp.close()

    inifile = os.path.join(args.outputfolder,
                           "input_oval_settings.ini")
    with open(inifile, 'w') as fp:
        fp.write(iniblock)
        fp.close()


    qx(["python", "main.py", "--file", svgfile, "--configfile", inifile,"-p","x:5","y:5", "--tempfolder", "tmp", "--outputfolder",str(args.outputfolder), "-v", "True"])