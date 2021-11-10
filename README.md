# svg2gcode
Scripts for converting / batchprocessing of multilayerd inkscape SVG files into GCODE for variety of CNC progamms like laserGRBL

<img width ="800px" src="doc/step.svg"/>

- Input(1): Multilayered Inkscape SVG, where each Layer should be engraved/cut with different parameters
- Input(2): Parameter setting file
- Output: GCode to process directly in laserGRBL
- Optional: The script can auto-generate supports (leaving tiny edge part so the object can not fall out upon cut)


If have a larger project, you can keep all parts in one file and only separate them through layers in pages. In this case, the script can generate a GCode file for each page.
<img src="toy.svg"/>

### Why?
For my CNC project, I work with inkscape  and often want to have all parts and peeces to be in a single SVG file, where I can adjust and adapt the drawing without loosing the overview. However each part and peece can require own material and cutting/engraving parameters. For example I would like first to engrave parts and cut them after, but leaving small supports such that the parts do not fall off. This script package should do exactly this!


### SVG structure

Input:
  (1)A multilayered SVG file. Each root layers name correspond to a material (For example Wood/Sturofoam/Glas etc.) as defined by user. Each material-layer can contain multiple page-layers. Each page layer can contains multiple procedure layers (example: Cut/Engrave/Write etc.) as defined by user.
 
 input.svg
   |-Material - Layer (Wood/Sturofoam/etc.)
   |    |-PageNr - Layer
   |        |-Procedure -Layer (Cut/Engrave/etc.)
   |            object1
   |            objectn
   |-Material2 ... 
            
  (2) A set of rules of how to parametrize a particular material-procedure combination. Parameters include feed, laser strength, passes, whether support should be added to cutting peeces, etc.

Output:
  For each page-layer a GCODE fiel is generated where all procedure layers are merged into one. Thus a page can be carried out at once.



### Installation

(1) Install Python (e.g simplest through <a href="https://www.anaconda.com/products/individual">Anaconda</a>)

(2) Download/clone the project 

(3) Install python dependencies:
pip install -r requirements.txt

(4) Done

### Quick Start
After installation just run the toy example with supplied toy.svg and material.ini:

python main.py --file toy.svg --configfile=material.ini --tempfolder tmp --outputfolder toyresult -v True

The output will be stored into the folder "toyresult" page by page.

Open and use any generated GCode file from "toyresult" in your CNC programm (like laserGRBL)

### Known issues/limitations:
The software is highly experimental, I had to learn many things by doing and I had to do it fast. The code is a mess. The names of the parametrers are not standartized and should be renamed in the futute (e.g "speed" and "strength" should become "F" and "S", respectively)

The software may have issues. Please check the generated output (even better would be to simulate ) before cutting
Example simulator: https://ncviewer.com/


### CREDITS:
<a href="https://inkscape.org/">inkscape</a> for the program to easily design of parts in SVG
<a href="https://pypi.org/project/pygcode/">pygcode</a> for the packege for conversion SVG to GCODE
<a href="https://github.com/arkypita/LaserGRBL">LaserGRB</a>for a great UI to display GCODE and communicate with hardware
<a href="https://www.ebay.de/sch/i.html?_from=R40&_trksid=p2380057.m570.l1313&_nkw=cnc+laser&_sacat=0">All cheap CNC Laser hardware</a> for making real objects out of computer drawings

