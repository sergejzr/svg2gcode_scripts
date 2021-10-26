import argparse
import re


def combine(arrayofdicts):
    res = {}
    for dict in arrayofdicts:
        for dkey in dict:
            res[dkey] = dict[dkey]
    return res

def required_length(nmin,nmax):
    class RequiredLength(argparse.Action):
        def __call__(self, parser, args, values, option_string=None):
            if not nmin<=len(values)<=nmax:
                msg='argument "{f}" requires between {nmin} and {nmax} arguments'.format(
                    f=self.dest,nmin=nmin,nmax=nmax)
                raise argparse.ArgumentTypeError(msg)
            setattr(args, self.dest, values)
    return RequiredLength

class Paddingtype:
    def __init__(self):
        self.pattern=re.compile("([x|y]):(\\d+)")

    def __call__(self, value):
        a=self.pattern.match(value)
        if a:
            return {a.group(1): a.group(2)}

        raise argparse.ArgumentTypeError(
            "'{}' should be either: x or y".format(
                value))

class Filetype:
    patterns = {
        'filename': re.compile(".*\.svg"),
        's2gargument': re.compile("s2g_(\\w+):*(.*)"),
    }




    def __init__(self,arguments):
        for argument in arguments:
            argument["pattern"]=re.compile(argument["name"]+":(.+)")

        self.arguments=arguments

    def __call__(self, value):
        a = self.patterns["filename"].match(value)
        if a:
            return {"file": value}
        a = self.patterns["s2gargument"].match(value)

        if a:
            if a.group(2):
                return {a.group(1): a.group(2)}
            else:
                return {a.group(1): ""}

        for argument in self.arguments:

            a=argument["pattern"].match(value)
            if a:
                res=a.group(1)
                if argument["type"]:
                    if argument["type"] =="int":
                        res=int(res)
                    else:
                        if argument["type"] =="float":
                            res = float(res)

                return {argument["name"]: res}

        raise argparse.ArgumentTypeError(
            "'{}' should be either: (1) a file name (*.svg), (2) 'strength' parameter, (3) 'repeat' parameter, or (4) parameter for sv32gcode (svg2_PARAM:VALUE)".format(
                value))
        return value

    def prove(self, filedesc):
        for argument in self.arguments:
            if "required" in argument and argument["required"] and not "name" in  argument and not argument["name"] in filedesc:
                raise argparse.ArgumentTypeError(
                    "Error: '"+argument["name"]+"' is mandatory for -file")
            else:
                if not argument["name"] in filedesc:
                    if "default" in argument:
                        filedesc[argument["name"] ]=argument["default"]
                    else:
                        filedesc[argument["name"]] = None
        if not "s2g" in filedesc:
            filedesc["s2g"]={}





class s2gtype():
    patterns = {
        's2vargs': re.compile("(Y|X|F|Z|B|T|V)*([c|f|n|s|w|t|m|z]:(\\d\.*\\d*))*"),
    }

    def __call__(self, value):
        a = self.patterns["s2vargs"].match(value)
        if a:
            if a.group(1):
                return {a.group(1): ""}
            if len(a.group())>3 and a.group(4):
                return {a.group(3): a.group(4)}

        raise argparse.ArgumentTypeError(
            "'{}' should be a parameter accepted by svg2gcode:\n\
Y shift Y-ax\n\
X sfit X-ax\n\
c use z-axis instead of laser\n\
f feed rate (3500)\n\
n # number of reorders (30)\n\
s scale (1.0)\n\
F flip Y-axis\n\
w final width in mm\n\
t Bezier tolerance (0.5)\n\
m machine accuracy (0.1)\n\
z z-traverse (1.0)\n\
Z z-engage (-1.0)\n\
B do Bezier curve smoothing\n\
T engrave only TSP-path\n\
V optmize for Voronoi Stipples".format(
                value))
        return value

class ArgumentColonparser:

    def __init__(self,arguments):
        for argument in arguments:
            argument["pattern"]=re.compile(argument["name"]+"(:(.+))*")

        self.arguments=arguments

    def __call__(self, value):
        for argument in self.arguments:

            a=argument["pattern"].match(value)
            if a:
                res=a.group(2)
                if argument["type"]:
                    if argument["type"] =="int":
                        res=int(res)
                    else:
                        if argument["type"] =="float":
                            res = float(res)
                        else:
                            if argument["type"] == "bool":
                                if res and len(res)>0:
                                    res = bool(res)
                                else:
                                    res=True

                return {argument["name"]: res}

        raise argparse.ArgumentTypeError(
            "'{}' should be either: (1) a file name (*.svg), (2) 'strength' parameter, (3) 'repeat' parameter, or (4) parameter for sv32gcode (svg2_PARAM:VALUE)".format(
                value))
        return value

    def prove(self, filedesc):
        for argument in self.arguments:
            if ("required" in argument) and (argument["required"]) and (not argument["name"] in filedesc):
                raise argparse.ArgumentTypeError(
                    "Error: '"+argument["name"]+"' is mandatory for -file")
            else:
                if not argument["name"] in filedesc:
                    if "default" in argument:
                        filedesc[argument["name"] ]=argument["default"]
                    else:
                        filedesc[argument["name"]] = None
        return True
