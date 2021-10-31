#!/usr/bin/python
from svg_to_gcode.svg_parser import parse_file
from svg_to_gcode.compiler import Compiler, interfaces
import os
import re
import sys
import argparse
from audioop import max
from builtins import input
from os import mkdir
import hashlib
from subprocess import check_output as qx
import re
import sys
import argparse
from argparserlib.svgtoolargparser import *
from argparserlib.svgtoolargparser import required_length
from subprocess import check_output as qx
import math
import numpy as np
import copy


class translateCoo:

    def __init__(self, shiftX,shiftY):
        self.shift={"X":shiftX,"Y":shiftY}
    def __call__(self, mymatch):
        return mymatch.group(2)+str(round((float(mymatch.group(3)) + self.shift[mymatch.group(2)])*100)/100.)



class SVG2GCodeConverterPython:

    def __call__(self, arguments):
        # Press the green button in the gutter to run the script.
        gcode_compiler = Compiler(interfaces.Gcode, arguments["speed"], arguments["strength"], pass_depth=1)

        curves = parse_file(arguments["filename"])  # Parse an svg file into geometric curves

        gcode_compiler.append_curves(curves)
        gcode_compiler.compile_to_file(arguments["tmpfilegcode"], passes=1)
        data=""
        with open(arguments["tmpfilegcode"]) as fp:
            data = fp.read()
            fp.close()
            data=self.translate(data,arguments)
            with open(arguments["tmpfilegcode"], 'w') as fp:
                fp.write(data)
                fp.close()

    def translate(self,data,args):
        translateC=translateCoo(args["shift"]["x"],args["shift"]["y"])

        data = re.sub('(([X|Y])(\d+(\.+\d*)))',translateC,data)
        return data


class SVG2GCodeConverter:

    def __call__(self, arguments):

        print(arguments)
        output = qx(arguments)


class CutRepeater:
    def __init__(self, passes, support=False):
        self.passes = passes
        self.support = support

    def __call__(self, value):

        if self.support:
            return self.addsupport(value, self.support, self.passes)
        else:
            return self.addsupport(value, False, self.passes)

    def lineinfo(self, p1, p2):
        gap = 2
        length = math.sqrt(math.pow(p1["x"] - p2["x"], 2) + math.pow(p1["y"] - p2["y"], 2))
        if length == 0:
            return {"len": 0, "proc": 0, "p1": p1, "p2": p2}
        proc = gap / length
        return {"len": length, "proc": proc, "p1": p1, "p2": p2}

    def splitinthemiddle(self, point1, point2, gap):
        inverse = np.array([0, 0]) - np.array(point1)
        v = np.array([point1, point2])
        v = v + inverse

        dist = np.linalg.norm(v[0] - v[1])

        n1 = (((dist - gap) / 2 / dist) * v)
        n1 = n1 - n1[0]

        n2 = (((dist + gap) / 2 / dist) * v)
        n2 = n2 - n2[0]

        return [n1 - inverse, np.array([n2[1], v[1]]) - inverse]

    def findLongestLine(self, points):

        maxlen = False
        prevpoint = False
        i = 0
        for p in points:
            i = i + 1
            if not "x" in p:
                continue
            if not prevpoint:
                prevpoint = p
                continue
            linfo = self.lineinfo(prevpoint, p)
            prevpoint = p
            if not maxlen:
                maxlen = linfo
            if maxlen["len"] < linfo["len"]:
                maxlen = linfo
                maxlen["lenauslen"] = i - 1
        return maxlen

    def findGoodSupport(self, points, gap):
        lines = []
        prevpnt = False
        lenlin = 0
        i = 0
        maxlen = False
        for point in points:
            i = i + 1
            if not "x" in point:
                continue

            if prevpnt:
                linfo = self.lineinfo(prevpnt, point)
                lines.append(linfo)
                lenlin = lenlin + linfo["len"]
                if not maxlen:
                    maxlen = linfo
                if maxlen["len"] < linfo["len"]:
                    maxlen = linfo
                    maxlen["lenauslen"] = i - 1

            prevpnt = point

        sortedlines=copy.deepcopy(lines)
        #lines.sort()

        gaps = {}
        if lenlin < (gap * 4):
            return False

        if maxlen["len"] > (gap * 4):
            # self.splitinthemiddle()
            w = 3 + 4
            res = self.splitinthemiddle([maxlen["p1"]["x"], maxlen["p1"]["y"]], [maxlen["p2"]["x"], maxlen["p2"]["y"]],
                                        gap)

            return {"type": "split", "gap": maxlen}


        else:
            quater = lenlin / 4
            eight = lenlin / 8
            g1 = self.readGapAt(eight, gap, lines)
            # g2=self.readGapAt(5*eight, gap, lines)
            if g1:
                print("\nGAp1 startpoint:" + str(g1["p1"]) + "\nendpoint:" + str(g1["p2"]))
                # return {"type": "conti", "gap": g1}
                g2 = self.readGapAt(eight * 5, gap, lines)
                if g2:
                    print("\nGAp2 startpoint:" + str(g2["p1"]) + "\nendpoint:" + str(g2["p2"]))

                    return {"type": "conti", "gapstart": g1, "gapend": g2}

        return False

    def addsupport(self, match, support, passes):

        block = match.group(1)

        if not support:
            newdata = block
        else:
            newdata = ""
            lines = []
            pattern = re.compile('(.*)(X(\\d+\\.*\\d*))*\\s*(Y(\\d+\\.*\\d*))*\\s*(F\\d+)*')
            pattern_getX = re.compile('X(\d+\.*\d*)')
            pattern_getY = re.compile('Y(\d+\.*\d*)')
            pattern_getS0 = re.compile('S0')
            pattern_getSON = re.compile('S(\d+)')

            points = []
            i = 0
            oldX = 0
            oldY = 0
            maxX = -1000
            minX = 1000
            maxY = -1000
            minY = 1000

            minYLine = -1
            minXLine = -1
            maxYLine = -1
            minYLine = -1
            originallines = block.split("\n")

            i = 0
            laseron = False
            for line in originallines:
                i = i + 1
                aX = pattern_getX.search(line)
                aY = pattern_getY.search(line)
                aL = pattern_getS0.search(line)
                aLO = pattern_getSON.search(line)
                if aLO:
                    if int(aLO.group(1)) > 0:
                        laseron = True
                if aL:
                    laseron = False
                if not aX and not aY:
                    points.append({"linenr": i - 1})
                else:
                    if aX:
                        newX = float(aX.group(1))
                        oldX = newX
                    else:
                        newX = oldX
                    if aY:
                        newY = float(aY.group(1))
                        oldY = newY
                    else:
                        newY = oldY
                    if not oldX and not oldY:
                        raise Exception("Error: Either X or Y was not previously set. The point would be corrupt!")
                    else:
                        if laseron:
                            points.append({"x": newX, "y": newY, "linenr": (i - 1)})
                        else:
                            points.append({"linenr": i - 1})

            split = self.findGoodSupport(points, support["gap"])

            if split and split["type"] == "split":
                lline = split["gap"]
                a = np.array([lline["p1"]["x"], lline["p1"]["y"]])
                b = np.array([lline["p2"]["x"], lline["p2"]["y"]])
                supportsplit = self.splitinthemiddle(a, b, support["gap"])

                mpx = supportsplit[0][1][0]
                mpy = supportsplit[0][1][1]

                mp2x = supportsplit[1][0][0]
                mp2y = supportsplit[1][0][1]

                newdata = ""
                i = 0
                line = ""
                for line in originallines:
                    i = i + 1
                    newdata += line + "\n"
                    if lline and (i - 1) == lline["p1"]["linenr"]:
                        newdata = newdata + "(addedblock start)\n" + "X" + str(mpx) + " Y" + str(mpy) + "\nS" + str(
                            support["laseroff"]) + "\nX" + str(
                            mp2x) + " Y" + str(mp2y) + "\nS" + str(support["laseron"]) + "\n(added block end)\n"
            elif split and split["type"] == "conti":

                i = 0
                gapclosed=True
                for line in originallines:
                    i = i + 1

                    if (i - 1) == split["gapstart"]["p1"]["linenr"]:
                        newdata = newdata + "(addedSwitchblock start)\nS" + str(
                            support["laseroff"]) + ";\n"
                        newdata += line + "\n"
                        gapclosed=False
                    elif (i - 1) == split["gapstart"]["p2"]["linenr"]:
                        newdata += line + "\n(addedSwitchblock end)\nS" + str(
                            support["laseron"]) + ";\n"
                        gapclosed=True
                    else:
                        newdata += line + "\n"
                        #if (i - 1) == split["gapend"]["p1"]["linenr"]:
                        #    newdata = newdata + "(addedSwitchblock start)\nS" + str(
                        #        support["laseroff"]) + "\n"
                        #    newdata += line + "\n"
                        #elif (i - 1) == split["gapend"]["p2"]["linenr"]:
                        #    newdata += line + "\n(addedSwitchblock end)\nS" + str(
                        #        support["laseron"]) + "\n"
                        #else:
                        #    newdata += line + "\n"

                if not gapclosed:
                    print("WTF?")
        passestrart = passes
        returndata = ""
        while passes > 0:
            passes = passes - 1
            returndata = returndata + "\n( start pass " + str(passestrart - passes) + " of " + str(
                passestrart) + " )\n" + newdata + "( end pass " + str(passestrart - passes) + " of " + str(
                passestrart) + " )"
        return returndata

    def readGapAt(self, eight, gap, lines):
        gapstart = False
        clen = 0
        i = -1
        startlen = False
        gapend = False
        while i < len(lines) - 1:
            i = i + 1
            line = lines[i]
            clen = clen + line["len"]
            if not startlen and clen >= eight:
                startlen = 0
                gapstart = line["p1"]
            if gapstart:
                startlen = startlen + line["len"]

            if startlen and startlen >= gap:
                if (gapstart!=line):
                    gapend = line["p1"]
                else:
                    gapend = line["p2"]

                if gapstart["linenr"]==gapend["linenr"]:
                    print("A WTF")
                else:
                    return {"p1": gapstart, "p2": gapend}



class Svg2GcodeMerger:

    def roundme(self,match):
        lst = float(int(float(match.group(2)) * 100)) / 100.

        return match.group(1) + str(lst)
    def svg2cleangc(self, newline, speed, strength, codestyle, repeat, addsuport=False):

        #newline = re.sub("G1\s(.*)\nG1\s(.*)\nG0\s(.*)\n\(\scity", 'G1 \g<1>\nG1 \g<2>\nS0\nG0 \g<3>\n( city', newline,
        #                 flags=re.MULTILINE)

       # newline = re.sub('\( end \)', 'S0', newline, flags=re.MULTILINE)
        #newline = re.sub('\( city \d* \)', 'S' + str(strength), newline, flags=re.MULTILINE)

        if codestyle != "laserGRBL":
            return newline
        newline="\n"+newline+"\n" #for regex match
        # G\d+.*\n)(G0.*\n)
        #        newline = re.sub("^G1(.*)\nG1\\1\n", 'G1\\1\n', newline,
        #                         flags=re.MULTILINE)
        #
        newline = re.sub('^M5;\nG1', 'S0;\nG0', newline,
                         flags=re.MULTILINE)

        newline = re.sub('^G0.*(X.*)(Y.*);', '\nG0 \\1\\2;', newline,
                         flags=re.MULTILINE)

        newline = re.sub('^(M3.*\nG1(.*)(X.*)(Y.*));\n', 'S'+str(strength)+';\nG1 \\3\\4 F'+str(speed)+';\n', newline,
                         flags=re.MULTILINE)
        newline = re.sub('^M5;\n', 'S0;\n', newline,
                         flags=re.MULTILINE)



        newline = re.sub('([X|Y])(\\d+\.*\\d*)', self.roundme, newline, flags=re.MULTILINE)
        newline = re.sub('(G92.*)\n', "", newline, flags=re.MULTILINE)
        newline = re.sub('(G90.*)\n', "", newline, flags=re.MULTILINE)
        #newline = re.sub('G0\\s+M3\\s+S0\n', "S0;\n", newline, flags=re.MULTILINE)
        res=newline
        if False:
            mx = re.compile("^G0.*")
            res = False
            oldX = False
            oldY = False
            oldF = False
            oldG = False
            oldline = False

            for line in newline.split("\n"):

                if oldline and oldline == line:
                    print("doubled")
                else:
                    oldline = line
                    if not mx.match(line):
                        mt = re.match('.*X(\\d+(\.\\d*)*).*', line)
                        if mt:
                            newX = float(mt.group(1))
                        else:
                            newX = False

                        mt = re.match('.*Y(\\d+(\.\\d*)*).*', line)
                        if mt:
                            newY = float(mt.group(1))
                        else:
                            newY = False

                        mt = re.match('.*F(\\d+).*', line)
                        if mt:
                            newF = float(mt.group(1))
                        else:
                            newF = False

                        cleanedline = False
                        mt = re.match('(G(\\d+)).*', line)
                        if mt:
                            newG = int(mt.group(2))

                            if not oldG or newG != oldG:
                                cleanedline = "G" + str(newG)
                                oldF = False
                            oldG = newG
                            if newX:
                                if cleanedline:
                                    cleanedline = cleanedline + " "
                                else:
                                    cleanedline = ""

                                if not oldX or newX != oldX:
                                    cleanedline = cleanedline + "X" + str(newX)
                                oldX = newX

                            if newY:
                                if cleanedline:
                                    cleanedline = cleanedline + " "
                                else:
                                    cleanedline = ""

                                if not oldY or newY != oldY:
                                    cleanedline = cleanedline + "Y" + str(newY)
                                oldY = newY

                            if newF:
                                if cleanedline:
                                    cleanedline = cleanedline + " "
                                else:
                                    cleanedline = ""

                                if not oldF or newF != oldF:
                                    cleanedline = cleanedline + "F" + str(newF)
                                oldF = newF
                        else:
                            oldG = False
                            cleanedline = line

                        if res:
                            res = res + "\n"
                        else:
                            res = ""
                    else:
                        cleanedline = line
                    res = res + cleanedline

       # res = re.sub('\nS0\nM5\nG0', "\nS0 M5 S0\nG0 X0 Y0", res, flags=re.MULTILINE)

        support=False
        if addsuport:
            support={"gap":addsuport["support_gap"],"laseron":strength,"laseroff":addsuport["support_strength"]}

        rptr = CutRepeater(repeat, support)
        res = re.sub('(^G0.*\n(.*\n)+?(M5\s+)*S0;)', rptr, res, flags=re.MULTILINE)
        #res = re.sub('(^G0.*\n(.*\n)+?(M5\s+)*S0;)', "\n(object start)\n\\1\n(object end)\n", res, flags=re.MULTILINE)
        #"\n(object start)\n\\1\n(object end)\n"

        # if repeat>1:
        #    rounds=repeat
        #    replacement=False
        #    while rounds>0:
        #        rounds=round-1
        #        if not replacement:
        #            replacement=""
        #        else:
        #            replacement="\n"+replacement
        #        replacement=replacement+"\\1"

        # res = re.sub('^((G0.*)\nS([1-9]+\\d*)(((.*)\n)+?S0))', replacement, res, flags=re.MULTILINE)
        return "M3 S0;\n"+res+"\nM5 S0;\n"

    def process(self, outputfilename, inputfiles, s2g={}, padding={"x": 5, "y": 5}, autoshiftY=False, codestyle=None,
                tmpdir="tmpwork"):

        if not os.path.exists(tmpdir):
            os.makedirs(tmpdir)

        if not "x" in padding:
            padding["x"] = 0
        if not "y" in padding:
            padding["y"] = 0

        paddingx = int(padding["x"])
        paddingy = int(padding["y"])

        for info in inputfiles:
            info["shift"] = {"x": 0, "y": 0}

        print(info)

        for info in inputfiles:
            info["shift"]["y"] = info["shift"]["y"] + paddingy
            info["shift"]["x"] = info["shift"]["x"] + paddingx

        completedata = ""

        filenames = ""
        for info in inputfiles:
            s2gkeys = {}
            for akey in s2g:
                if s2g[akey]:
                    s2gkeys[akey] = (s2g[akey])
                else:
                    s2gkeys[akey] = ""

            for akey in info["s2g"]:
                if s2g[akey]:
                    s2gkeys[akey] = (s2g[akey])
                else:
                    s2gkeys[akey] = ""

            arguments = []

            for akey in s2gkeys:
                arguments.append("-" + akey)
                if s2g[akey] and s2g[akey] != "":
                    arguments.append(s2g[akey])


            arguments.append('-Y ' + str(info["shift"]["y"]))
            arguments.append('-X ' + str(info["shift"]["x"]))
            arguments.append('-f ' + str(info["speed"]))
            arguments.append(info["filename"])

            result = hashlib.md5(info["filename"].encode('utf-8'))

            info["tmpfilegcode"] = os.path.join(tmpdir,
                                                result.hexdigest() + os.path.basename(info["filename"]) + ".gcode")

            conv= SVG2GCodeConverterPython()
            #arguments.append(info["tmpfilegcode"])
            conv(info)



            #           output = qx(
            #               ['/home/szerr/git/svg2gcode/svg2gcode', '-F', '-B', '-w ' + str(info["dim"]["w"]),
            #                '-Y ' + str(info["shift"]["y"]),
            #                '-X ' + str(info["shift"]["x"]),
            #                "-f " + str(info["speed"]), info["filename"] + "_cropped.svg", info["filename"] + ".gcode"])

            # Reading data from file1
            with open(info["tmpfilegcode"]) as fp:
                data = fp.read()
                fp.close()
            supportstr="no"
            if info["support"]:
                supportstr = "yes, "+str(info["support"])+"'"
            cleandata = "( file start "+info["filename"]+")\n( speed:"+str(info["speed"])+", strength:"+str(info["strength"])+\
                        " codestyle='"+codestyle+"', passes:"+str(info["repeat"])+" support:"+supportstr+" )\n"+\
                        self.svg2cleangc(data, info["speed"], info["strength"], codestyle, info["repeat"], info["support"])+\
                        "( file end "+info["filename"]+")\n"
            #            if jumpspeed:
            #                cleandata = re.sub('S0\nG(.*)F(\\d+)', 'S0\nG\\1F' + str(jumpspeed), cleandata, flags=re.MULTILINE)
            repeat = info["repeat"]

            roundstring = ""
            while repeat > 0 and False:
                if info["repeat"] > 1:
                    roundstring = " round " + str(info["repeat"] - repeat + 1) + " of " + str(info["repeat"])
                completedata = completedata + "( start file: " + info[
                    "filename"] + "; " + roundstring + " )\n" + cleandata + "( end file: " + info[
                                   "filename"] + "; " + roundstring + " )\n"
                repeat = repeat - 1
#            filenames = filenames + "0+" + info["filename"]

            completedata = completedata + cleandata

        with open(outputfilename, 'w') as fp:
            fp.write(completedata)
            fp.close()

    def clargs(self):
        return self.args

    def fromCommandline(self):

        fileparser = Filetype(arguments=[{"name": "speed", "type": "int", "required": True},
                                         {"name": "repeat", "type": "int", "required": False, "default": 1},
                                         {"name": "strength", "type": "int", "required": True},
                                         {"name": "support_strength", "type": "int"},
                                         {"name": "support_gap", "type": "float"}
                                         ])
        parser = argparse.ArgumentParser(
            description='Merges inkscape SVG files list into  a laserGRBL conform gcode file.')
        parser.add_argument('-f', '--file', type=fileparser, nargs='+', required=True, action='append',
                            help='list of file names with parameters')
        parser.add_argument('--globals2g', type=s2gtype(), nargs='+',
                            help='list of options passed directly to svg2gcode as default values. Same options supplied to files override those values')
        parser.add_argument('-a', '--autoscale', type=bool, default=True,
                            help='will auto scale the image using vg information')
        parser.add_argument('-p', '--padding', type=Paddingtype(), nargs='+',
                            help='Padding of the image, so CNC doesnt have to work on border limits')
        parser.add_argument('--autoshiftY', type=bool, nargs='?', default=False,
                            help='Shifts the whole image such that it can be started from left bottom corner')
        parser.add_argument('--codestyle', type=str, nargs='+', default="laserGRBL",
                            help='Only one option is supported "laserGRBL" ')
        parser.add_argument('-o', '--output', type=str, required=True, help='output file *.gcode')
        parser.add_argument('-t', '--tempfolder', type=str, required=True,
                            help='Workingfolder')


        args=parser.parse_args()



        inputarray = []

        for filedesc in args.file:
            filedesc = combine(filedesc)
            fileparser.prove(filedesc)

            curfile = {"filename": filedesc["file"],
                       "speed": filedesc["speed"],
                       "strength": filedesc["strength"],
                       "repeat": filedesc["repeat"],
                       "s2g": filedesc["s2g"]
                       }
            support=False
            if "support_gap" in filedesc and filedesc["support_gap"]:
                support = {"support_gap": filedesc["support_gap"]}

                if not "support_strength" in filedesc and not filedesc["support_strength"]:
                    support["support_strength"]= 0
                else:
                    support["support_strength"]=filedesc["support_strength"]

            curfile["support"] = support

            inputarray.append(curfile)
        self.args = args
        return self.process(args.output, inputarray,
                            s2g=combine(args.globals2g),
                            padding=combine(args.padding), autoshiftY=args.autoshiftY, codestyle=args.codestyle,
                            tmpdir=args.tempfolder)
