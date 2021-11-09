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
    parser.add_argument('-l', '--layersettings', type=argparser, nargs='+', action='append',
                        help='list of file names with parameters')

    parser.add_argument('-c', '--configfile', type=str,
                        help='Configuration settings for diffretn material/process layers')

    parser.add_argument('-v', '--verbose', type=str,
                        help='Tell me what are you doing all the time')

    parser.add_argument('-p', '--procedure_execution_ordering', type=str, nargs='+',
                        help='In which order should the procedures be carried out. Example "1:Engrave 2:Cut" => means engrave first, then cut.')



    args = parser.parse_args()

    if not args.verbose:
        logging.disable()

    if not os.path.exists(args.file):
        raise argparse.ArgumentTypeError(
            "Error: ' Inpuitfile '{}' does not exist!".format(
                args.file))


    if not args.layersettings and not args.configfile:
        raise argparse.ArgumentTypeError(
            "Error: Neither --configfile (-c), nor --layersettings are provided!")

    if args.layersettings and args.configfile:
        logging.debug("Both, --layersettings and  --configfile are provided. I will take command line --layersettings by default")

    layersettings = {}

    logging.info("Parse inputfile '{}'".format(str(args.file)))

    orderingargs = args.procedure_execution_ordering

    ordering = {}
    skipprocedures = {}
    skipmaterials = {}

    if orderingargs:
        for ord in orderingargs:
            splord = ord.split(":")
            ordering[splord[1]] = splord[0]

    if args.configfile:
        config = configparser.ConfigParser()
        config.read(args.configfile)
        config.sections()

        for section in config.sections():


            if section == "Settings":
                procedure_execution_ordering=config[section]["procedure_execution_ordering"]
                if procedure_execution_ordering:
                    oi=0
                    for procedure in procedure_execution_ordering.split(","):
                        ordering[procedure]=oi
                        oi+=1
                skipprocedurelist=config[section]["skipprocedure"]
                if skipprocedurelist:
                    for procedure in skipprocedurelist.split(","):
                        skipprocedures[procedure] = True

                skipmaterialslist = config[section]["skipmaterial"]
                if skipmaterialslist:
                    for material in skipmaterialslist.split(","):
                        skipmaterials[material] = True
            else:
                pathchuncks=section.split(".")
                material=pathchuncks[0]
                procedure=pathchuncks[1]
                asetting={"material":material,"procedure":procedure}
                for key in config[section]:
                    asetting[key]=config[section][key]

                argparser.prove(asetting)
                layersettings[material + "_" + procedure] = asetting



        config.sections()


    else:
        for req in args.layersettings:
            asetting = combine(req)
            argparser.prove(asetting)
            layersettings[asetting["material"] + "_" + asetting["procedure"]] = asetting

    if args.procedure_execution_ordering:
        orderingargs = args.procedure_execution_ordering

    if args.skipprocedure:
        for procedure in args.skipprocedure:
            skipprocedures[procedure] = True


    tmpdir = args.tempfolder

    tmpdircrop=os.path.join(tmpdir,"crop")
    tmpdirsplit = os.path.join(tmpdir, "split")
    tmpdirgcode = os.path.join(tmpdir, "gcode")
    if not os.path.exists(tmpdircrop):
        os.makedirs(tmpdircrop)

    if not os.path.exists(tmpdirsplit):
        os.makedirs(tmpdirsplit)

    title=Path(args.file).stem
    outdir = join(args.outputfolder, title)





    if args.skipmaterial:
        for material in args.skipmaterial:
            skipmaterials[material] = True


    if not os.path.exists(outdir):
        os.makedirs(outdir)
    logging.info("Split layers into separate files and store them in '{}'".format(tmpdirsplit))
    output = qx(["python","svgsplit.py", "--file", args.file, "--outputfolder", tmpdirsplit,"--tempfolder", tmpdircrop])
    logging.info("Splitting done!")


    onlyfiles = [f for f in listdir(tmpdirsplit) if isfile(join(tmpdirsplit, f))]
    groupfiles = {}


    for f in onlyfiles:
        nameparts = f.split(".")
        material = nameparts[1]
        procedure = nameparts[len(nameparts) - 2]
        page = nameparts[2]
        logging.info("Reading material:'"+material+"', procedure:'"+procedure+"', page:'"+page+"'")

        if material + "_" + procedure not in layersettings and material not in skipmaterials and procedure not in skipprocedures:
            raise Exception("Don't know how to carry out "+procedure+" for material "+material+". Check input arguments")

        if not material in groupfiles:
            groupfiles[material] = {}

        if not page in groupfiles[material]:
                groupfiles[material][page] = []
        idx=len(groupfiles[material][page])



        if procedure in ordering:
            idx=ordering[procedure]

        groupfiles[material][page].append(
            {"page": page, "material": material, "procedure": procedure, "filename": f,"order":idx})

    cntfiles = 0
    allfiles = 0

    for material in groupfiles:
        for page in groupfiles[material]:
            allfiles=allfiles+1




    for material in groupfiles:
       # print(material + ":" + str(groupfiles[material]))


        for pagenr in groupfiles[material]:
            page=groupfiles[material][pagenr]
            arguments = ["python", "svg2gcode_merge.py"]
            groupfiles[material][pagenr].sort(key=takeFirst)
            for meta in page:
                if meta["material"] in skipmaterials or meta["procedure"] in skipprocedures:
                    logging.info("I skip the material "+meta["material"]+" or procedure "+meta["procedure"]+". Skipped = "+str(skipprocedures))
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

            tempoutputdir = join(tmpdirgcode, title+"."+meta["material"]+"."+meta["page"])
            if not os.path.exists(tempoutputdir):
                os.makedirs(tempoutputdir)

            outfilename = join(pageoutputdir, title+"."+meta["material"]+"."+meta["page"] + ".gcode")
            arguments.append("--output")
            arguments.append(outfilename)

            arguments.append("--tempfolder")
            arguments.append(tempoutputdir)

            #print(arguments)
            logging.info("Process page "+str(cntfiles)+"of "+str(allfiles)+". Merge with settings: "+str(arguments))
            cntfiles=cntfiles+1
            output = qx(arguments)
           # print(output)

    shutil.rmtree(tmpdir)

    exit(0)


#--file toy.svg --tempfolder tmp --outputfolder toy --layersettings material:"Verkleidung" procedure:Cut speed:300 strength:950 repeat:1 support_gap:1 support_strength:0 --layersettings material:"Sturopor" procedure:Cut speed:500 strength:950 support_gap:1 support_strength:0 --layersettings material:"Holz" procedure:Cut speed:20 repeat:1 strength:950 support_gap:1 support_strength:0 --layersettings material:"Glas" procedure:Cut speed:300 repeat:1 strength:950 --layersettings material:"Verkleidung" procedure:Engrave speed:1000  strength:950 --layersettings material:"Sturopor" procedure:Engrave speed:700  strength:300 --layersettings material:"Holz" procedure:Engrave speed:700  strength:300 --layersettings material:"Glas" procedure:Cut speed:700  strength:500 --layersettings material:"Glas" procedure:Engrave speed:300 strength:950 --procedure_execution_ordering 1:Engrave 2:Cut --skipprocedure Meta --skipmaterial Frames