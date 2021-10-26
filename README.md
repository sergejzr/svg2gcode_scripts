# svg2gcode
Scripts for manipulating / batchprocessing of SVG files into "multi-layered", "multi-passed" "auto-supported-parts" Gcode for variety of CNC progamms like laserGRBL

Input:
  (1)A multilayered SVG file. Each root layers name correspond to a material (For example Wood/Sturofoam/Glas etc.) as defined by user. Each material-layer can contain multiple page-layers. Each page layer can contains multiple procedure layers (example: Cut/Engrave/Write etc.) as defined by user.
  (2) A set of rules of how to parametrize a particular material-procedure combination. Parameters include feed, laser strength, passes, whether support should be added to cutting peeces, etc.

Output:
  For each page-layer a GCODE fiel is generated where all procedure layers are merged into one. Thus a page can be carried out at once.
  
Explanation:
For my CNC project, I often want to have all parts and peeces to be in a single SVG file, where I can adjust and adapt the drawing without loosing the overview. However each part and peece can require own material and cutting/engraving parameters. For example I would like first to engrave parts and cut them after, but leaving small supports such that the parts do not fall off. This script package should do exactly this!

Example call (to put all gcode into the folder "toyresult"):

python main.py --file toy.svg --tempfolder tmp --outputfolder toyresult \
--layersettings material:"Wood1mm" procedure:Cut speed:100 strength:950 repeat:2 support_gap:2 support_strength:500 \
--layersettings material:"Styrofoam" procedure:Cut speed:500 strength:950 support_gap:1 support_strength:300 \
--layersettings material:"Wood3mm" procedure:Cut speed:20 repeat:5 strength:950 support_gap:2 support_strength:500 \
--layersettings material:"Glas" procedure:Cut speed:300 repeat:2 strength:950 \
--layersettings material:"Wood1mm" procedure:Engrave speed:700  strength:950 \
--layersettings material:"Styrofoam" procedure:Engrave speed:700  strength:300 \
--layersettings material:"Wood3mm" procedure:Engrave speed:700  strength:300 \
--layersettings material:"Glas" procedure:Cut speed:700  strength:500 \
--layersettings material:"Glas" procedure:Engrave speed:300 strength:950  \
--skipprocedure Meta --skipmaterial Frames

