This is a tool for creating "striped" KEGG diagrams using the tool at http://www.genome.jp/kegg/tool/color_pathway.html

Requires:
======
- Matlab with the Image Processing toolbox
- python 2.7 with the mechanize library or python 2.6 with argparse and mechanize

When provided with a list entrez-ids and group-names and a mapping between group-names and colors it will create a set of diagrams in-which the shared nodes will have a striped color.

GeneList example:
========
28727	CD-Down
343069	CD-Down
374920	CD-Up
3483	CD-Up
374907	UC-down
4303	Common-down
374907	Common-down
29924	UC-down
84787	UC-down
374907	CD-Down

All group names must be valid path-names (no non-ascii characters or spaces). 

ColorList example:
==========
CD-Down blue,red
CD-Up green
Common-Down pink,green
Common-Up purple
UC-Down yellow,blue
UC-Up red,green

The colors must be valid choices from the KEGG Color Pathway tool.
