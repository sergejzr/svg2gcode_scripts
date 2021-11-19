import argparse
import logging
import os
import re
from subprocess import check_output as qx
from os import listdir
from os.path import isfile, join
from argparserlib.svgtoolargparser import *
from pathlib import Path
import shutil
import configparser

# take second element for sort
def takeFirst(elem):
    return elem["order"]

logging.basicConfig(level=logging.INFO)

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
        description='Converts multi-layered SVG into multi-step gcode.\n Example call:\n'+'--file toy.svg --tempfolder tmp --outputfolder toyresult --layersettings material:"Wood1mm" procedure:Cut speed:100 strength:950 repeat:2 support_gap:2 support_strength:500 --layersettings material:"Styrofoam" procedure:Cut speed:500 strength:950 support_gap:1 support_strength:300 --layersettings material:"Wood3mm" procedure:Cut speed:20 repeat:5 strength:950 support_gap:2 support_strength:500 --layersettings material:"Glas" procedure:Cut speed:300 repeat:2 strength:950 --layersettings material:"Wood1mm" procedure:Engrave speed:700  strength:950 --layersettings material:"Styrofoam" procedure:Engrave speed:700  strength:300 --layersettings material:"Wood3mm" procedure:Engrave speed:700  strength:300 --layersettings material:"Glas" procedure:Cut speed:700  strength:500 --layersettings material:"Glas" procedure:Engrave speed:300 strength:950  --skipprocedure Meta --skipmaterial Frames')
    parser.add_argument('-f', '--file', type=str, required=True,
                        help='Input SVG containing layer')
    parser.add_argument('-t', '--tempfolder', type=str, required=False,
                        help='Workingfolder')
    parser.add_argument('-o', '--outputfolder', type=str, required=True,
                        help='Input SVG containing layer')
    parser.add_argument('-c', '--configfile', type=str,
                        help='Configuration settings for diffrent material/process layers')
    parser.add_argument('-p', '--padding', type=str, nargs='+',
                        help='Padding of the image, so CNC doesnt have to work on border limits')
    parser.add_argument('-v', '--verbose', type=str,
                        help='Tell me what are you doing all the time')



    args = parser.parse_args()

    if not args.verbose:
        logging.disable()

    if not os.path.exists(args.file):
        raise argparse.ArgumentTypeError(
            "Error: ' Inpuitfile '{}' does not exist!".format(
                args.file))


    if not args.configfile:
        raise argparse.ArgumentTypeError(
            "Error: --configfile (-c) is not provided!")


    if args.tempfolder:
        tmpdir = args.tempfolder
    else:
        tmpdir="tmp"

    tmpdircrop=os.path.join(tmpdir,"crop")
    tmpdirsplit = os.path.join(tmpdir, "split")
    tmpdirgcode = os.path.join(tmpdir, "gcode")
    if not os.path.exists(tmpdircrop):
        os.makedirs(tmpdircrop)

    if not os.path.exists(tmpdirsplit):
        os.makedirs(tmpdirsplit)

    title=Path(args.file).stem
    outdir = join(args.outputfolder, title)

    if not os.path.exists(outdir):
        os.makedirs(outdir)
    logging.info("Split layers into separate files and store them in '{}'".format(tmpdirsplit))
    output = qx(["python","svgsplit.py", "--file", args.file, "--outputfolder", tmpdirsplit,"--tempfolder", tmpdircrop])
    logging.info("Splitting done!")

    arguments = ["python", "svg2gcode_merge.py"]
    arguments.append("--configfile")
    arguments.append(str(args.configfile))
    arguments.append("--padding")
    if args.padding:
        arguments.append(" ".join(args.padding))
    arguments.append("--inputfolder")
    arguments.append(tmpdirsplit)
    arguments.append("--outputfolder")
    arguments.append(args.outputfolder)
    if args.tempfolder:
        arguments.append("--tempfolder")
        arguments.append(args.tempfolder)
    output = qx(arguments)




    exit(0)


#--file toy.svg --tempfolder tmp --outputfolder toy --layersettings material:"Verkleidung" procedure:Cut speed:300 strength:950 repeat:1 support_gap:1 support_strength:0 --layersettings material:"Sturopor" procedure:Cut speed:500 strength:950 support_gap:1 support_strength:0 --layersettings material:"Holz" procedure:Cut speed:20 repeat:1 strength:950 support_gap:1 support_strength:0 --layersettings material:"Glas" procedure:Cut speed:300 repeat:1 strength:950 --layersettings material:"Verkleidung" procedure:Engrave speed:1000  strength:950 --layersettings material:"Sturopor" procedure:Engrave speed:700  strength:300 --layersettings material:"Holz" procedure:Engrave speed:700  strength:300 --layersettings material:"Glas" procedure:Cut speed:700  strength:500 --layersettings material:"Glas" procedure:Engrave speed:300 strength:950 --procedure_execution_ordering 1:Engrave 2:Cut --skipprocedure Meta --skipmaterial Frames