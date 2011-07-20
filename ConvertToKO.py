from __future__ import division
from mechanize import Browser
from collections import defaultdict
import os, os.path
import re
import argparse
from itertools import islice

def take(iterable, N):
    return list(islice(iterable, N))


class ConvertingBrowser(Browser):
    
    def init_for_conversion(self):
        """Initializes the browser for converting Entrez to KO IDS"""
    
        self.set_handle_robots(False)
        self.baseurl = 'http://www.genome.jp/'
        self.main_search_page = 'http://www.genome.jp/kegg/kegg3.html'
        self.urldict = {} #a place to put the dbget lookup urls
        self.mappingdict = {} #a place to put the final KOs
        self._go_to_base()


    def _go_to_base(self):
        """Goes to the base-search location."""
        self.open(self.main_search_page)
        self.state = 'base_search'

    def _search_group(self, input_list):
        """Searches a list of <100 entrez ids against the KEGG ids"""        


        assert len(input_list) < 100, 'Conversion tool only accepts 100 items at a time!'
        if self.state != 'base_search':
            self._go_to_base()

        lookup_ids = set(input_list) - set(self.urldict.keys())
        if lookup_ids:
            self.select_form(nr = 1)
            self['text'] = '\n'.join(lookup_ids)
            self.submit()
            self.state = 'id_lookup'
    
            for ln in self.links():
                newurl = self.baseurl + ln.url
                entrezid = ln.text.split(':')[-1]
                self.urldict[entrezid] = newurl
        print 'converted %i entrez to urls' % len(self.urldict)

    def _get_kos(self):
        """Finds the KOs from all urls that have been gathered before."""

        regexp = re.compile('ko:(\w*\d*)')
        for entrez, url in self.urldict.items():
            resp = self.open(url)
            html = resp.read()
            res = regexp.findall(html)
            if len(res) == 1:
                self.mappingdict[entrez] = res[0]
                if len(self.mappingdict) % 100 == 0:
                    print 'converted %i entrez to KOs' % len(self.mappingdict)

    def convert_ids(self, idlist):
        
        idlist = list(idlist) #since we will need to go through it twice

        iditer = iter(idlist)
        block = take(iditer,90)
        while block:
            self._search_group(block)
            block = take(iditer, 90)

        self._get_kos()

        for entrez in idlist:
            try:
                yield entrez, self.mappingdict[entrez]
            except KeyError:
                pass





if __name__ == '__main__':
    
    
    parser = argparse.ArgumentParser(description = 'Convert a list of Entrez-ids into KOs')
    parser.add_argument('--infile', dest = 'infile', required = True, 
                        help = 'path/to/input/file')
    parser.add_argument('--destfile', dest = 'destfile', required = True, 
                        help = 'path/to/output/file')
    
    args = parser.parse_args()

    entrez_ids = islice([line.split(None)[0] for line in open(args.infile)],500)
    
    converting_browser = ConvertingBrowser()
    converting_browser.init_for_conversion()

    mapping = dict(converting_browser.convert_ids(entrez_ids))

    with open(args.destfile, 'w') as ohandle:
        with open(args.infile) as ihandle:
            for line in ihandle:
                parts = line.split(None,1)
                try:
                    ko = mapping[parts[0]]
                    ohandle.write(ko + '\t' + parts[1] + '\n')
                except KeyError:
                    pass






















        
