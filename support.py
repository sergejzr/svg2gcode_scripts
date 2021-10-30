import argparse
import os
import re
from subprocess import check_output as qx
from os import listdir
from os.path import isfile, join
from argparserlib.svgtoolargparser import *
from pathlib import Path
import shutil
import math
import numpy as np


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
                for line in originallines:
                    i = i + 1

                    if (i - 1) == split["gapstart"]["p1"]["linenr"]:
                        newdata = newdata + "(addedSwitchblock start)\nS" + str(
                            support["laseroff"]) + "\n"
                        newdata += line + "\n"
                    elif (i - 1) == split["gapstart"]["p2"]["linenr"]:
                        newdata += line + "\n(addedSwitchblock end)\nS" + str(
                            support["laseron"]) + "\n"
                    else:
                        if (i - 1) == split["gapend"]["p1"]["linenr"]:
                            newdata = newdata + "(addedSwitchblock start)\nS" + str(
                                support["laseroff"]) + "\n"
                            newdata += line + "\n"
                        elif (i - 1) == split["gapend"]["p2"]["linenr"]:
                            newdata += line + "\n(addedSwitchblock end)\nS" + str(
                                support["laseron"]) + "\n"
                        else:
                            newdata += line + "\n"

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
                gapstart = line["p2"]
            if gapstart:
                startlen = startlen + line["len"]
            if startlen and startlen >= gap:
                gapend = line["p2"]
                return {"p1": gapstart, "p2": gapend}


argparser = ArgumentColonparser(arguments=[{"name": "material", "type": "str", "required": True},
                                           {"name": "procedure", "type": "str", "required": True},
                                           {"name": "speed", "type": "int", "required": True},
                                           {"name": "repeat", "type": "int", "required": False, "default": 1},
                                           {"name": "strength", "type": "int", "required": True},
                                           {"name": "support_strength", "type": "int"},
                                           {"name": "support_gap", "type": "float"}
                                           ])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Converts multi-layered SVG into multi-step gcode.\n Example call:\n' + '--file toy.svg --tempfolder tmp --outputfolder toyresult --layersettings material:"Wood1mm" procedure:Cut speed:100 strength:950 repeat:2 support_gap:2 support_strength:500 --layersettings material:"Styrofoam" procedure:Cut speed:500 strength:950 support_gap:1 support_strength:300 --layersettings material:"Wood3mm" procedure:Cut speed:20 repeat:5 strength:950 support_gap:2 support_strength:500 --layersettings material:"Glas" procedure:Cut speed:300 repeat:2 strength:950 --layersettings material:"Wood1mm" procedure:Engrave speed:700  strength:950 --layersettings material:"Styrofoam" procedure:Engrave speed:700  strength:300 --layersettings material:"Wood3mm" procedure:Engrave speed:700  strength:300 --layersettings material:"Glas" procedure:Cut speed:700  strength:500 --layersettings material:"Glas" procedure:Engrave speed:300 strength:950  --skipprocedure Meta --skipmaterial Frames')
    parser.add_argument('-f', '--file', type=str, required=True,
                        help='Input SVG containing layer')

    args = parser.parse_args()

    with open(args.file) as fp:
        data = fp.read()
        fp.close()

    repeater = CutRepeater(1,  # False)
                           {"gap": 10, "laseron": 900, "laseroff": 0})
    res = re.sub('(^G0.*\n(.*\n)+?S0)', repeater, data + "\n", flags=re.MULTILINE)

    with open("test.gcode", 'w') as fp:
        fp.write(res)
        fp.close()

    exit(0)


