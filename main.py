import argparse
import os
import re
from subprocess import check_output as qx
from os import listdir
from os.path import isfile, join
from argparserlib.svgtoolargparser import *
from pathlib import Path
import shutil

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
    parser.add_argument('-t', '--tempfolder', type=str, required=True,
                        help='Workingfolder')

    parser.add_argument('--skipmaterial', type=str,nargs='+', required=False,
                        help='Ingore material')
    parser.add_argument('--skipprocedure', type=str, nargs='+', required=False,
                        help='Ingore procedure')

    parser.add_argument('--metaprocedure', type=str, required=False,
                        help='Use this layer as meta data only, do not engrave')

    parser.add_argument('-o', '--outputfolder', type=str, required=True,
                        help='Input SVG containing layer')
    parser.add_argument('-l', '--layersettings', type=argparser, nargs='+', required=True, action='append',
                        help='list of file names with parameters')
    parser.add_argument('-v', '--verbose', type=str,
                        help='Tell me what are you doing all the time')

    args = parser.parse_args()

    layersettings = {}


    for req in args.layersettings:
        asetting = combine(req)
        argparser.prove(asetting)
        layersettings[asetting["material"] + "_" + asetting["procedure"]] = asetting


    tmpdir = args.tempfolder

    tmpdircrop=os.path.join(tmpdir,"crop")
    tmpdirsplit = os.path.join(tmpdir, "split")
    if not os.path.exists(tmpdircrop):
        os.makedirs(tmpdircrop)

    if not os.path.exists(tmpdirsplit):
        os.makedirs(tmpdirsplit)

    title=Path(args.file).stem
    outdir = join(args.outputfolder, title)

    skipprocedures={}

    if args.skipprocedure:
        for procedure in args.skipprocedure:
            skipprocedures[procedure] = True


    skipmaterials = {}
    if args.skipmaterial:
        for material in args.skipmaterial:
            skipmaterials[material] = True


    if not os.path.exists(outdir):
        os.makedirs(outdir)

    output = qx(["python","pagesplit.py", "--file", args.file, "--outputfolder", tmpdirsplit,"--tempfolder", tmpdircrop])

    onlyfiles = [f for f in listdir(tmpdirsplit) if isfile(join(tmpdirsplit, f))]
    groupfiles = {}

    for f in onlyfiles:
        nameparts = f.split(".")
        material = nameparts[1]
        procedure = nameparts[len(nameparts) - 2]
        page = nameparts[2]

        if material + "_" + procedure not in layersettings and material not in skipmaterials and procedure not in skipprocedures:
            raise Exception("Don't know how to carry out "+procedure+" for material "+material+". Check input arguments")

        if not material in groupfiles:
            groupfiles[material] = {}

        if not page in groupfiles[material]:
                groupfiles[material][page] = []

        groupfiles[material][page].append(
            {"page": page, "material": material, "procedure": procedure, "filename": f})

    #
    for fkey in groupfiles:
        print(fkey + ":" + str(groupfiles[fkey]))



    for material in groupfiles:
        print(material + ":" + str(groupfiles[material]))


        for pagenr in groupfiles[material]:
            page=groupfiles[material][pagenr]
            arguments = ["python", "mergesvg2gcode.py"]
            for meta in page:
                if meta["material"] in skipmaterials or meta["procedure"] in skipprocedures:
                    print("I skip the material "+meta["material"]+" or procedure "+meta["procedure"]+". Skipped = "+str(skipprocedures))
                    continue
                arguments.append("--file")
                arguments.append(join(tmpdirsplit, meta["filename"]))


                searchkey=meta["material"] + "_" + meta["procedure"]
                if not searchkey in layersettings:
                    searchkey="*_" + meta["procedure"]
                    if not searchkey in layersettings:
                        raise "Don't know how to proceed with material: "+str(meta["material"])+" and/or procedure:"+str(meta["procedure"])

                cargs = layersettings[searchkey]
                arguments.append("speed:"+str(cargs["speed"]))
                arguments.append("repeat:"+str(cargs["repeat"]))
                arguments.append("strength:"+str(cargs["strength"]))

                support = False
                if "support_gap" in cargs and cargs["support_gap"]:
                    arguments.append("support_gap:" + str(cargs["support_gap"]))

                    if not "support_strength" in cargs:
                        strength=0
                    else:
                        strength= cargs["support_strength"]

                    arguments.append("support_strength:" + str(strength))



                arguments.append("--padding")
                arguments.append("x:5")
                arguments.append("y:5")
                arguments.append("--autoshiftY")
                arguments.append("False")
                arguments.append("--globals2g")
                #arguments.append("F")
                arguments.append("B")
            if len(arguments)==2:
                continue
            pageoutputdir = join(outdir, meta["material"])
            if not os.path.exists(pageoutputdir):
                os.makedirs(pageoutputdir)

            tempoutputdir = join(tmpdir, title+"."+meta["material"]+"."+meta["page"])
            if not os.path.exists(tempoutputdir):
                os.makedirs(tempoutputdir)

            outfilename = join(pageoutputdir, title+"."+meta["material"]+"."+meta["page"] + ".gcode")
            arguments.append("--output")
            arguments.append(outfilename)

            arguments.append("--tempfolder")
            arguments.append(tempoutputdir)
            tempoutputdir
            print(arguments)

            output = qx(arguments)
            print(output)

    #shutil.rmtree(tmpdir)

    exit(0)


