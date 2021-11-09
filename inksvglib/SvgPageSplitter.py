#! /usr/bin/python3
import xml.etree.ElementTree as ET
import os
import copy
from subprocess import check_output as qx
import argparse
import hashlib
from pathlib import Path
SVG_NS = "http://www.w3.org/2000/svg"

class SvgPageSplitter:

    def __init__(self):
        self.args = ""
    def getChildren(self, node, root=False):
        tmpchildren={}
        children = node.findall('{http://www.w3.org/2000/svg}g')
        for child in children:
            if '{http://www.inkscape.org/namespaces/inkscape}groupmode' in child.attrib:
                if child.attrib['{http://www.inkscape.org/namespaces/inkscape}groupmode'] == "layer":

                    id=child.attrib['id']
                    label = child.attrib['{http://www.inkscape.org/namespaces/inkscape}label']
                    tmpchildren[id]={"id":id,"label":label,"node":child}
        return tmpchildren
    def leaveChild(self, father,belovedchild):
        listtorem = []
        e = list(father)
        for child in e:
            if child!=belovedchild:
                listtorem.append(child)
        for child in listtorem:
            father.remove(child)


    def leaveId(self,material_tree,material_id):
        rootnode = material_tree.getroot()
        son = rootnode.findall('.//{'+SVG_NS+'}g[@id="' + material_id + '"]' )[0]
        father=rootnode.findall('.//{'+SVG_NS+'}g[@id="'+material_id+'"]...' )[0]

        self.leaveChild(father,son)
        return material_tree

    # xml.findall('.//g[@id="123"]...')



    def splitLayerHierarchy(self, infile,export_folder,tmp_folder):

        tree = ET.parse(infile)
        root = tree.getroot()

        tmpdircropout = tmp_folder
        tmpdirsplitout =export_folder
        materials=self.getChildren(root)

        #for node in tree.findall('.//{%s}rect' % SVG_NS)


        for material_id in materials:
            material=materials[material_id]
            material_tree=self.leaveId(copy.deepcopy(tree),material_id)
            material["type"]="material"
            material["pages"]=[]
            filename=material["label"]
            pages=self.getChildren(material["node"],root)

            for page_id in pages:
                page=pages[page_id]
                page_tree=self.leaveId(copy.deepcopy(material_tree),page_id)
                page["type"]="page"
                material["pages"].append(page)
                filename = material["label"]+"."+page["label"]
                tmpdir=os.path.join(tmpdircropout,filename)
                if not os.path.exists(tmpdir):
                    os.makedirs(tmpdir)

                result = hashlib.md5(infile.encode('utf-8'))
                tmpfile = os.path.join(tmpdir, str(result.hexdigest()) + os.path.basename(
                    infile)+"." + filename+"_cropped.svg")
                page_tree.write(tmpfile)
                output = qx(['inkscape', "--export-text-to-path", "--export-area-drawing", tmpfile, "-o", tmpfile])
                page_tree = ET.parse(tmpfile)
                processes = self.getChildren(page["node"])
                page["processes"]=[]
                for process_id in processes:
                    process=processes[process_id]
                    process["type"]="process"
                    page["processes"].append(process)
                    process_tree=self.leaveId(copy.deepcopy(page_tree),process_id)

                    processsplitfolder=os.path.join(tmpdirsplitout, os.path.join(
                                                    material["label"],page["label"]
                                                    ))
                    #if not os.path.exists(processsplitfolder):
                    #    os.makedirs(processsplitfolder)

                    tmpfile = os.path.join(export_folder,  Path(infile).stem+"."+material["label"]+"."+page["label"]+"."+process["label"]+ ".svg")
                    process_tree.write(tmpfile)

                    output = qx(['inkscape', "--export-text-to-path", tmpfile, "-o", tmpfile])
                    process["outfile"]=tmpfile
        return materials


    def fromCommandline(self):
        parser = argparse.ArgumentParser(
            description='Splits an SVG file according to layer hierachy. Each leaf-layer exports to a separate file')
        parser.add_argument('-f', '--file', type=str, required=True,
                            help='Input SVG containing layer')
        parser.add_argument('-o', '--outputfolder', type=str, required=True,
                            help='Input SVG containing layer')
        parser.add_argument('-t', '--tempfolder', type=str, required=True,
                            help='Input SVG containing layer')

        args = parser.parse_args()
        res = self.splitLayerHierarchy(args.file,args.outputfolder,args.tempfolder)
        self.args = args
        return res