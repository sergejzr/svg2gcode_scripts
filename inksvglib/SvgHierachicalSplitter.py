#! /usr/bin/python3
import xml.etree.ElementTree as ET
import os
import copy
from subprocess import check_output as qx
import argparse


class SvgHierachicalSplitter:

    def __init__(self):
        self.args = ""

    def headnode(self, node):
        listtorem = []
        e = list(node)

        for child in e:
            listtorem.append(child)
        for child in listtorem:
            node.remove(child)
        return node

    def emptyTree(self, node, root=False):
        listchildpaths = []

        emptynode = copy.deepcopy(node)
        emptynode = self.headnode(emptynode)
        children = node.findall('{http://www.w3.org/2000/svg}g')
        tmpchildren = []
        for child in children:
            if '{http://www.inkscape.org/namespaces/inkscape}groupmode' in child.attrib:
                if child.attrib['{http://www.inkscape.org/namespaces/inkscape}groupmode'] == "layer":
                    tmpchildren.append(child)
        children = tmpchildren

        lname = node.get('{http://www.inkscape.org/namespaces/inkscape}label')
        if not lname:
            lname = "svg"
        if len(lname) == 1:
            lname = 'char_' + str(ord(lname))

        if len(children) == 0:

            return [{"lable": lname, "node": node}]
        else:
            for child in children:
                listcur = self.emptyTree(child)

                for renodepair in listcur:
                    renode = renodepair["node"]
                    relable = renodepair["lable"]

                    curfather = copy.deepcopy(emptynode)
                    curfather.append(renode)
                    curlable = lname + "." + relable
                    listchildpaths.append({"lable": curlable, "node": curfather})

        return listchildpaths

    def splitLayerHierarchy(self, infile, export_folder):

        tree = ET.parse(infile)
        root = tree.getroot()
        listofresults = []
        trees = self.emptyTree(root)

        for cnodepair in trees:
            label = cnodepair["lable"]
            cnode = cnodepair["node"]
            ctree = copy.deepcopy(tree)
            ctree._setroot(cnode)
            outfilename = os.path.join(export_folder, label + '.svg')
            ctree.write(outfilename)
            output = qx(['inkscape', outfilename, "-o", outfilename])
            listofresults.append(outfilename)
        return listofresults

    def clargs(self):
        return self.args

    def fromCommandline(self):
        parser = argparse.ArgumentParser(
            description='Splits an SVG file according to layer hierachy. Each leaf-layer exports to a separate file')
        parser.add_argument('-f', '--file', type=str, nargs='+', required=True,
                            help='Input SVG containing layer')
        parser.add_argument('-o', '--outputfolder', type=str, nargs='+', required=True,
                            help='Input SVG containing layer')

        args = parser.parse_args()
        res = self.splitLayerHierarchy(args.file[0], args.outputfolder[0])
        self.args = args
        return res
