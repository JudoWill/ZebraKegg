from mechanize import Browser
import os, os.path
import re


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
                gene_str_data += '%s %s\n' % (gene, ','.join(colors))
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
            
        





if __name__ == '__main__':
    

    odir = 'keggtest/'

    genes = {'2146':('blue',), '8880':('blue',), '5436':('blue',), '22976':('blue',),
            '1476':('blue',),'3148':('blue',),'5438':('blue',),'6772':('blue',),
            '8317':('blue',),'10799':('blue',),'8318':('blue',),'10609':('blue',),
            '22974':('blue',),'79902':('blue',),'1457':('blue','red',),'5423':('blue','red',),'890':('blue','red',)}
    keggbw = KeggBrowser()
    keggbw.init_for_kegg()
    keggbw.search_pathways(genes)
    keggbw.get_pathways(outpath = odir)






