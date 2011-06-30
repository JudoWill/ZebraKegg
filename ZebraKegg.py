from mechanize import Browser
from collections import defaultdict
from subprocess import call
import os, os.path
import re
import argparse
import shlex
from random import uniform
import colorsys


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
            
        
def pick_colors(ncolors):
    
    for hue in range(0,360, 360/ncolors):
        saturation = 90+uniform(0,10)
        lightness = 50+uniform(0,10)
        res = colorsys.hls_to_rgb(hue/256, lightness/256, saturation/256)
        rgb = [int(x*256) for x in res]
        hval = '#'+''.join(hex(x)[-2:] for x in rgb)
        yield hval



if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description = 'Make "zebra" plots for kegg picutes.')
    parser.add_argument('--genefile', dest = 'genefile', required = True,
                            help = 'path/to/file which contains the gene-to-group mapping.')
    parser.add_argument('--colorfile', dest = 'colorfile', default = None,
                            help = 'path/to/file which has the group-to-color mapping.')
    parser.add_argument('--destdir', dest = 'destdir', default = None, 
                            help = 'path/to/destination where you want the maps to be created.')

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
    wrong_ids = set()
    with open(args.genefile) as handle:
        for lnum, line in enumerate(handle):
            parts = line.strip().split()
            try:
                int(parts[0])
            except ValueError:
                wrong_ids.add((parts[0], lnum))
            except IndexError:
                continue
            group_dict[parts[1]].add(parts[0])
    if wrong_ids:
        wstr = ''
        for wid, lnum in wrong_ids:
            wstr += '"%s" on line %i\n' % (wid, lnum)
        wstr += 'do not look like entrez-ids.'
        raise ValueError, wstr

    color_dict = {}
    if args.colorfile:
        with open(args.colorfile) as handle:
            for line in handle:
                parts = line.strip().split()
                color_dict[parts[0]] = parts[1]
    else:
        with open(args.genefile + '.color', 'w') as handle:
            for key, color in izip(group_dict.keys(), pick_colors(len(group_dict))):
                color_dict[key] = color
                handle.write('%s\t%s\n' % (key, color))
            

    assert all(x in color_dict for x in group_dict.keys()), 'Not all colors mentioned in %s are in %s' % (parser.genefile, parser.colorfile)

    for key, genes in group_dict.items():
        ogenes = dict((x, color_dict[key]) for x in genes)
        tdir = os.path.join(dest_dir, key)
        try:
            os.mkdir(tdir)
        except OSError:
            pass
        keggbw = KeggBrowser()
        keggbw.init_for_kegg()
        keggbw.search_pathways(ogenes)
        keggbw.get_pathways(outpath = tdir)

    cmd = """matlab -r "combine_keggs('%s');quit;" -nodesktop -logfile %s -nosplash""" % (dest_dir, os.path.join(dest_dir, 'tmp.out'))
    print cmd
    call(shlex.split(cmd))





