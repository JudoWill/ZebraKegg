from __future__ import division
from mechanize import Browser
from collections import defaultdict
from subprocess import call
import os, os.path
import re
import argparse
import shlex
from random import choice
from math import sqrt


class KeggBrowser(Browser):
    
    def init_for_kegg(self):
        """Initializes the browser to search Kegg Pathways."""
        print 'initializing'
        self._factory.is_html = True
        self.set_handle_robots(False)
        self.open('http://www.genome.jp/kegg/tool/color_pathway.html')
        self.KEGG_STATE = 'base_search'

    def search_pathways(self, genes, org = 'hsa'):
        """Searches KEGG for pathways that specific genes are involed in.
            
            genes is a dict() with Entrez-IDS as KEYS and a tuple() of colors or 
            None as the Values."""
        print 'searching for pathways'
        if self.KEGG_STATE != 'base_search':
            self.init_for_kegg()

        gene_str_data = ''
        for gene, colors in genes.items():
            if colors is None:
                gene_str_data += gene+'\n'
            else:
                gene_str_data += '%s %s\n' % (gene, colors)
        self.select_form(nr = 0)
        self['org_name'] = [org]
        self['unclassified'] = gene_str_data
        self['reference'] = ['white']
        print self.geturl()
        self.submit()
        self.KEGG_STATE = 'pathway_list'
        print self.geturl()

    def _get_pathway_from_url(self, url):
        
        return url.split('/')[-1].split('.')[0]

    def _download_pathway_from_link(self, link, outpath):
        
        assert self.KEGG_STATE == 'pathway_list', 'Not in the correct state to download PATHWAYS!'
        resp = self.follow_link(link = link)
        pathway_name = self._get_pathway_from_url(link.url)
        print 'downloading', pathway_name
        filename = os.path.join(outpath, pathway_name+'.png')
        try:
            #have to use regexp because of bad-html that even beautifulsoup can't parse!
            tstr = resp.get_data()
            img_loc = re.findall('<img src="([\d\w/.]*?)"', tstr)[0]
            self.retrieve('http://www.genome.jp/' + img_loc, filename = filename)
        finally:
            self.back()
        
        


    def get_pathways(self, pathway_list = None, outpath = ''):

        print 'getting pathways'
        assert self.KEGG_STATE == 'pathway_list', 'Not in the correct state!'
        links = [ln for ln in self.links() if ln.url.startswith('/kegg-bin')]
        print len(links)
        if not (pathway_list is None):
            wanted_paths = set(pathway_list)
            links = [ln for ln in links if self._get_pathway_from_url(ln.url) in wanted_paths]
        print 'links:', len(links)
        for link in links:
            self._download_pathway_from_link(link, outpath)
            

def color_dist(c1, c2):
    """Determines the 'visual-distance' between two colors.
    The algorithm is taken from "http://www.compuphase.com/cmetric.htm".

    args:
        c1 -- A three tuple in RGB INTEGER format (0-256)
        c2 -- A three tuple in RGB INTEGER format (0-256)        
    Returns
        float -- weighted distance between the two colors.
    """

    
    r1, g1, b1 = c1
    r2, g2, b2 = c2

    rmean = (r1+r2)/2

    dr = r1-r2
    dg = g1-g2
    db = b1-b2

    dc = sqrt((2+rmean/256)*(dr**2) + 4*(dg**2) + (2+(255-rmean)/255)*(db**2))
    return dc

def convert_to_html_hex(inum):
    """Converts a three-tuple in RGB interger format (0-256) into a html-hex format."""
    
    tstr = '%2s%2s%2s' % (inum[0], inum[1], inum[2])
    return tstr.replace(' ','0')

        
def pick_colors(ncolors, default = None):
    """Yields a visually distinct group of colors.

    Colors are picked from a list of "web-safe" colors that KEGG should accept.


    args:
        ncolors -- An integer indicating the number of colors to pick.
    kwargs:    
        default = None -- If provided it will use the default as the initial 
                          color to pick. If None then it will pick a random 
                          color
    Returns:
        generator -- (color-name, html-formatted hex)
    """

    color_choices = {}
    with open('color_names.txt') as handle:
        for line in handle:
            cname, colors = line.strip().split('\t')
            color_choices[cname] = [int(x, base = 16) for x in colors.split()]

    assert ncolors < len(color_choices), "You have more than %i different groups, You probably don't want to do this!"
    
    if default is None:    
        default = choice(color_choices.keys())
    picked_colors = ((default, color_choices.pop(default)),)
    while len(picked_colors) < ncolors:
        bdist = None
        for cname, color in color_choices.iteritems():
            dist = min(color_dist(x, color) for _, x in picked_colors)
            if bdist is None or dist > bdist:
                bdist = dist
                bcolor = cname
        picked_colors += ((bcolor, color_choices.pop(bcolor)),)

    for cname, color in picked_colors:
        yield cname, '#'+convert_to_html_hex(color)


def get_group_kegg_images(tdir, genes, color, org):
    """Downloads marked KEGG diagrams.
    
    Args:
        tdir -- The location to download the images to.
        genes -- A list of entrez-ids to mark.
        color -- A kegg-formated color.
    Returns:
        None
    """

    for key, genes in group_dict.items():
        ogenes = dict((x, color) for x in genes)

        keggbw = KeggBrowser()
        keggbw.init_for_kegg()
        keggbw.search_pathways(ogenes, org = org)
        keggbw.get_pathways(outpath = tdir)


def join_images(dest_dir):
    """Calls matlab and merges the images"""

    cmd = """matlab -r "combine_keggs('%s');quit;" -nodesktop -logfile %s -nosplash""" % (dest_dir, os.path.join(dest_dir, 'tmp.out'))
    print cmd
    call(shlex.split(cmd))

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description = 'Make "zebra" plots for kegg picutes.')
    parser.add_argument('--genefile', dest = 'genefile', required = True,
                            help = 'path/to/file which contains the gene-to-group mapping.')
    parser.add_argument('--colorfile', dest = 'colorfile', default = None,
                            help = 'path/to/file which has the group-to-color mapping.')
    parser.add_argument('--destdir', dest = 'destdir', default = None, 
                            help = 'path/to/destination where you want the maps to be created.')
    parser.add_argument('--keggorg', dest = 'keggorg', default = 'hsa', 
                            help = 'The organism to use for the pathway drawings.')


    args = parser.parse_args()
    if args.destdir is None:
        dest_dir = args.colorfile.split('.')[0]
    else:
        dest_dir = args.destdir

    try:
        os.mkdir(dest_dir)
    except OSError:
        pass

    group_dict = defaultdict(set)
    with open(args.genefile) as handle:
        for lnum, line in enumerate(handle):
            parts = line.strip().split()
            group_dict[parts[1]].add(parts[0])

    color_dict = {}
    if args.colorfile:
        with open(args.colorfile) as handle:
            for line in handle:
                parts = line.strip().split()
                color_dict[parts[0]] = parts[1]
    else:
        with open(args.genefile + '.color', 'w') as handle:
            for key, (cname, cnum) in izip(group_dict.keys(), pick_colors(len(group_dict))):
                color_dict[key] = cnum
                handle.write('%s\t%s\t%s\n' % (key, num, cname))
            

    assert all(x in color_dict for x in group_dict.keys()), 'Not all colors mentioned in %s are in %s' % (parser.genefile, parser.colorfile)

    
    for key, genes in group_dict.items():
        tdir = os.path.join(dest_dir, key)
        try:
            os.mkdir(tdir)
        except OSError:
            pass

        get_group_kegg_images(tdir, genes, color_dict[key], args.keggargs)

    join_images(dest_dir)





