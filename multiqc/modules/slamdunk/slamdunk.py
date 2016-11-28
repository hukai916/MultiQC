#!/usr/bin/env python

""" MultiQC module to parse output from Slamdunk """

from __future__ import print_function
import logging
import re
import numpy as np
from distutils.version import StrictVersion
from collections import OrderedDict

from multiqc import config, BaseMultiqcModule, plots
from curses.ascii import islower

# Initialise the logger
log = logging.getLogger(__name__)

class MultiqcModule(BaseMultiqcModule):
    """
    Slamdunk module class, parses slamdunk logs.
    """

    def __init__(self):

        # Initialise the parent object
        super(MultiqcModule, self).__init__(name='Slamdunk', anchor='slamdunk',
        href='https://github.com/t-neumann/slamdunk',
        info="is a tool to analyze SLAMSeq data. "\
         "More info to come.")

        self.slamdunk_data = dict()
        
        self.PCA_data = dict()
        
        self.utrates_data = dict()
        
        self.rates_data_plus = dict()
        self.rates_data_minus = dict()
        
        self.nontc_per_readpos_plus = dict()
        self.nontc_per_readpos_minus = dict()
        
        self.tc_per_readpos_plus = dict()
        self.tc_per_readpos_minus = dict()
        
        self.nontc_per_utrpos_plus = dict()
        self.nontc_per_utrpos_minus = dict()
        
        self.tc_per_utrpos_plus = dict()
        self.tc_per_utrpos_minus = dict()

#         # Find and load any Cutadapt reports
#         self.cutadapt_data = dict()
#         self.cutadapt_length_counts = dict()
#         self.cutadapt_length_exp = dict()
#         self.cutadapt_length_obsexp = dict()

        # Check whether summary also contains number of counted reads
        extendedSummary = True
            
        for f in self.find_log_files(config.sp['slamdunk']['summary'], filehandles = True):
            extendedSummary = extendedSummary and self.parseSummary(f)
            
        if len(self.slamdunk_data) == 0:
            log.debug("Could not find any reports in {}".format(config.analysis_dir))
            raise UserWarning

        log.info("Found {} reports".format(len(self.slamdunk_data)))
            
        if extendedSummary:
            log.info("Extended Slamdunk summary found.")
            
        log.info("Parsing PCA reports.")
            
        for f in self.find_log_files(config.sp['slamdunk']['PCA'], filehandles = True):
            self.parsePCA(f)
            
        log.info("Parsing UTR rates reports. This can take a while...")
                        
        for f in self.find_log_files(config.sp['slamdunk']['utrrates'], filehandles = True):
            self.parseUtrRates(f)
            
        log.info("Parsing read rates reports.")
            
        for f in self.find_log_files(config.sp['slamdunk']['rates'], filehandles = True):
            self.parseSlamdunkRates(f)
            
        log.info("Parsing rates per read position reports.")
            
        for f in self.find_log_files(config.sp['slamdunk']['tcperreadpos'], filehandles = True):
            self.parseSlamdunkTCPerReadpos(f)
            
        log.info("Parsing rates per UTR position reports.")

        for f in self.find_log_files(config.sp['slamdunk']['tcperutrpos'], filehandles = True):
            self.parseSlamdunkTCPerUtrpos(f)
                
        # Start the sections
        self.sections = list()

        # Basic Stats Table
        self.slamdunkGeneralStatsTable(extendedSummary)
        
        # PCA plot
        self.slamdunkPCAPlot()
        
        # Utr rates plot
        self.slamdunkUtrRatesPlot()

        # Rates plot
        self.slamdunkOverallRatesPlot()
        
        # TC per read position plot
        self.slamdunkTcPerReadPosPlot()
        
        # TC per UTR position plot
        self.slamdunkTcPerUTRPosPlot()
        
    def parsePCA(self, f):
        
        # Skip header
        next(f['f'])
        
        for line in f['f']:
            fields = line.rstrip().split('\t')
            
            sample = fields[0]
            PC1 = fields[1]
            PC2 = fields[2]
            
            self.PCA_data[sample] = dict()

            self.PCA_data[sample] = [{'x': float(PC1), 'y': float(PC2)}]
        
        
    def parseUtrRates(self, f) :
        
        sample = f['s_name']
        self.utrates_data[sample] = OrderedDict()
        
        # Skip comment line #
        next(f['f'])
        
        # Parse header
        conversions = next(f['f']).rstrip().split('\t')
        
        order = {}
        
        for i in range(6, len(conversions)) :
            order[i] = conversions[i]
            
        utrStats = {}
        
        plotConversions = ['A_T', 'A_G', 'A_C',
                           'C_A', 'C_G', 'C_T',
                           'G_A', 'G_C', 'G_T',
                           'T_A', 'T_G', 'T_C',
        ]
        
        for conversion in plotConversions:
            utrStats[conversion] = []
            
        for line in f['f']:
            values = line.rstrip().split('\t')
            
            name = values[0]
            strand = values[4]
            
            utrDict = {}
            
            for i in range(6, len(values)) :
                
                conversion= order[i]
                
                if strand == "-" :
                    if (conversion == "A_A") :
                        conversion = "T_T"
                    elif (conversion == "G_G") :
                        conversion = "C_C"
                    elif (conversion == "C_C") :
                        conversion = "G_G"
                    elif (conversion == "T_T") :
                        conversion = "A_A"
                    elif (conversion == "A_C") :
                        conversion = "T_G"
                    elif (conversion == "A_G") :
                        conversion = "T_C"
                    elif (conversion == "A_T") :
                        conversion = "T_A"
                    elif (conversion == "C_A") :
                        conversion = "G_T"
                    elif (conversion == "C_G") :
                        conversion = "G_C"
                    elif (conversion == "C_T") :
                        conversion = "G_A"
                    elif (conversion == "G_A") :
                        conversion = "C_T"
                    elif (conversion == "G_C") :
                        conversion = "C_G"
                    elif (conversion == "G_T") :
                        conversion = "C_A"
                    elif (conversion == "T_A") :
                        conversion = "A_T"
                    elif (conversion == "T_C") :
                        conversion = "A_G"
                    elif (conversion == "T_G") :
                        conversion = "A_C"
                
                utrDict[conversion] = int(values[i])
            
            if (np.sum(utrDict.values()) > 0) :
                Asum = utrDict['A_A'] + utrDict['A_C'] + utrDict['A_G'] + utrDict['A_T']
                Csum = utrDict['C_A'] + utrDict['C_C'] + utrDict['C_G'] + utrDict['C_T']
                Gsum = utrDict['G_A'] + utrDict['G_C'] + utrDict['G_G'] + utrDict['G_T']
                Tsum = utrDict['T_A'] + utrDict['T_C'] + utrDict['T_G'] + utrDict['T_T']
                
                if Asum > 0 :
                    utrDict['A_T'] = utrDict['A_T'] / float(Asum) * 100
                    utrDict['A_G'] = utrDict['A_G'] / float(Asum) * 100
                    utrDict['A_C'] = utrDict['A_C'] / float(Asum) * 100
                else :
                    utrDict['A_T'] = 0
                    utrDict['A_G'] = 0
                    utrDict['A_C'] = 0
                if Csum > 0:
                    utrDict['C_A'] = utrDict['C_A'] / float(Csum) * 100
                    utrDict['C_G'] = utrDict['C_G'] / float(Csum) * 100
                    utrDict['C_T'] = utrDict['C_T'] / float(Csum) * 100
                else :
                    utrDict['C_A'] = 0
                    utrDict['C_G'] = 0
                    utrDict['C_T'] = 0
                if Gsum > 0:
                    utrDict['G_A'] = utrDict['G_A'] / float(Gsum) * 100
                    utrDict['G_C'] = utrDict['G_C'] / float(Gsum) * 100
                    utrDict['G_T'] = utrDict['G_T'] / float(Gsum) * 100
                else :
                    utrDict['G_A'] = 0
                    utrDict['G_C'] = 0
                    utrDict['G_T'] = 0
                if Tsum > 0:
                    utrDict['T_A'] = utrDict['T_A'] / float(Tsum) * 100
                    utrDict['T_G'] = utrDict['T_G'] / float(Tsum) * 100
                    utrDict['T_C'] = utrDict['T_C'] / float(Tsum) * 100
                else :
                    utrDict['T_A'] = 0
                    utrDict['T_G'] = 0
                    utrDict['T_C'] = 0
                    
                for conversion in plotConversions:
                    utrStats[conversion].append(utrDict[conversion])
            
        
        for conversion in plotConversions:
            self.utrates_data[sample][re.sub("_",">",conversion)] = np.median(utrStats[conversion])

    def parseSlamdunkRates(self, f):
        
        sample = f['s_name']
        
        # Skip comment line #
        next(f['f'])
        
        bases = next(f['f']).rstrip().split('\t')
        
        baseDict = {}
        order = {}
        
        for i in range(1, len(bases)) :
            order[i] = bases[i]
                    
        for line in f['f']:
            values = line.rstrip().split('\t')
            base = values[0]
            baseDict[base]= {}
            
            for i in range(1, len(values)) :
            
                baseDict[base][order[i]] = int(values[i])
                
        divisor = {}      
        
        for fromBase in baseDict:
            for toBase in baseDict[fromBase]:
                if(toBase.islower()) :
                    if not divisor.has_key(fromBase.lower()) :
                        divisor[fromBase.lower()] = 0
                    divisor[fromBase.lower()] += baseDict[fromBase][toBase]
                else:
                    if not divisor.has_key(fromBase) :
                        divisor[fromBase] = 0
                    divisor[fromBase] += baseDict[fromBase][toBase]
             
        #log.info(str(baseDict))
        #log.info(str(divisor))
        
        for fromBase in baseDict:
            for toBase in baseDict[fromBase]:
                if(toBase.islower()) :
                    baseDict[fromBase][toBase] = baseDict[fromBase][toBase] / float(divisor[fromBase.lower()]) * 100
                else:
                    baseDict[fromBase][toBase] = baseDict[fromBase][toBase] / float(divisor[fromBase]) * 100
        
        #log.info(str(baseDict))
        
        self.rates_data_plus[sample] = {}
        self.rates_data_minus[sample] = {}
        
        for fromBase in baseDict:
            for toBase in baseDict[fromBase]:
                if fromBase != "N" and toBase.upper() != "N" and fromBase != toBase.upper():
                    if(toBase.islower()) :
                        self.rates_data_minus[sample][fromBase + ">" + toBase.upper()] = baseDict[fromBase][toBase]
                    else :
                        self.rates_data_plus[sample][fromBase + ">" + toBase] = baseDict[fromBase][toBase]
                        
    def parseSlamdunkTCPerReadpos(self, f):
        
        sample = f['s_name']
        
        # Skip comment line #
        next(f['f'])
        
        self.nontc_per_readpos_plus[sample] = {}
        self.nontc_per_readpos_minus[sample] = {}
        
        self.tc_per_readpos_plus[sample] = {}
        self.tc_per_readpos_minus[sample] = {}
        
        pos = 1
        
        for line in f['f']:
            values = line.rstrip().split('\t')
            if int(values[4]) > 0 :
                self.nontc_per_readpos_plus[sample][pos] = float(int(values[0])) / int(values[4]) * 100
                self.tc_per_readpos_plus[sample][pos] = float(int(values[2])) / int(values[4]) * 100
            else :
                self.nontc_per_readpos_plus[sample][pos] = 0
                self.tc_per_readpos_plus[sample][pos] = 0
                
            if int(values[5]) > 0:
                self.nontc_per_readpos_minus[sample][pos] = float(int(values[1])) / int(values[5]) * 100
                self.tc_per_readpos_minus[sample][pos] = float(int(values[3])) / int(values[5]) * 100
            else:
                self.nontc_per_readpos_minus[sample][pos] = 0
                self.tc_per_readpos_minus[sample][pos] = 0
                
            pos += 1
            
    def parseSlamdunkTCPerUtrpos(self, f):
        
        sample = f['s_name']
        
        # Skip comment line #
        next(f['f'])
        
        self.nontc_per_utrpos_plus[sample] = {}
        self.nontc_per_utrpos_minus[sample] = {}
        
        self.tc_per_utrpos_plus[sample] = {}
        self.tc_per_utrpos_minus[sample] = {}
        
        pos = 1
        
        for line in f['f']:
            values = line.rstrip().split('\t')
            if int(values[4]) > 0 :
                self.nontc_per_utrpos_plus[sample][pos] = float(int(values[0])) / int(values[4]) * 100
                self.tc_per_utrpos_plus[sample][pos] = float(int(values[2])) / int(values[4]) * 100
            else :
                self.nontc_per_utrpos_plus[sample][pos] = 0
                self.tc_per_utrpos_plus[sample][pos] = 0
                
            if int(values[5]) > 0:
                self.nontc_per_utrpos_minus[sample][pos] = float(int(values[1])) / int(values[5]) * 100
                self.tc_per_utrpos_minus[sample][pos] = float(int(values[3])) / int(values[5]) * 100
            else:
                self.nontc_per_utrpos_minus[sample][pos] = 0
                self.tc_per_utrpos_minus[sample][pos] = 0
                
            pos += 1
    
    def parseSummary(self, f):
        
        # Skip comment line #
        next(f['f'])
        
        # Skip header line "FileName..."
        columnCount = next(f['f']).count("\t") + 1
            
        for line in f['f']:
            fields = line.rstrip().split("\t")
            self.slamdunk_data[self.clean_s_name(fields[0],"")] = dict()
            self.slamdunk_data[self.clean_s_name(fields[0],"")]['sequenced'] = int(fields[4])
            self.slamdunk_data[self.clean_s_name(fields[0],"")]['mapped'] = int(fields[5])
            self.slamdunk_data[self.clean_s_name(fields[0],"")]['deduplicated'] = int(fields[6])
            self.slamdunk_data[self.clean_s_name(fields[0],"")]['filtered'] = int(fields[7])
            
            # Additional Count Column found in Table
            if columnCount == 10:
                self.slamdunk_data[self.clean_s_name(fields[0],"")]['counted'] = int(fields[8])
                
        self.add_data_source(f)
        
        return columnCount == 10

    def slamdunkGeneralStatsTable(self, extendedSummary):
        """ Take the parsed summary stats from Slamdunk and add it to the
        basic stats table at the top of the report """


        headers = OrderedDict()
        headers['sequenced'] = {
            'title': 'Sequenced',
            'description': '# sequenced reads',
            'shared_key': 'slamdunk_reads',
            'min': 0,
            'format': '{:.f}'
        }
        headers['mapped'] = {
            'title': 'Mapped',
            'description': '# mapped reads',
            'shared_key': 'slamdunk_reads',
            'min': 0,
            'format': '{:.f}'
        }
        headers['deduplicated'] = {
            'title': 'Deduplicated',
            'description': '# deduplicated reads',
            'shared_key': 'slamdunk_reads',
            'min': 0,
            'format': '{:.f}'
        }
        headers['filtered'] = {
            'title': 'Filtered',
            'description': '# reads after filtering',
            'shared_key': 'slamdunk_reads',
            'min': 0,
            'format': '{:.f}'
        }
        
        if (extendedSummary) :
            headers['counted'] = {
                'title': 'Counted',
                'description': '# reads after filtering',
                'shared_key': 'slamdunk_reads',
                'min': 0,
                'format': '{:.f}'
            }
        self.general_stats_addcols(self.slamdunk_data, headers)
        
    def slamdunkOverallRatesPlot (self):
        """ Generate the overall rates plot """

        pconfig = {
            'id': 'overallratesplot',
            'title': 'Overall conversion rates in reads',
            'cpswitch' : False,
            'cpswitch_c_active': False,
            'stacking' : 'normal',
            'data_labels': [
                "Plus Strand +",
                "Minus Strand -", 
            ]
        }
        
        cats = [OrderedDict(), OrderedDict()]
        
        cats[0]['T>C'] = {
            'name': 'T>C',
            'color': '#D7301F'
        }
        cats[0]['A>T'] = {
            'name': 'A>T',
            'color': '#C6DBEF'
        }
        cats[0]['A>G'] = {
            'name': 'A>G',
            'color': '#6BAED6'
        }
        cats[0]['A>C'] = {
            'name': 'A>C',
            'color': '#2171B5'
        }
        cats[0]['T>A'] = {
            'name': 'T>A',
            'color': '#C7E9C0'
        }
        cats[0]['T>G'] = {
            'name': 'T>G',
            'color': '#74C476'
        }
        cats[0]['G>A'] = {
            'name': 'G>A',
            'color': '#D9D9D9'
        }
        cats[0]['G>T'] = {
            'name': 'G>T',
            'color': '#969696'
        }
        cats[0]['G>C'] = {
            'name': 'G>C',
            'color': '#525252'
        }
        cats[0]['C>A'] = {
            'name': 'C>A',
            'color': '#DADAEB'
        }
        cats[0]['C>T'] = {
            'name': 'C>T',
            'color': '#9E9AC8'
        }
        cats[0]['C>G'] = {
            'name': 'C>G',
            'color': '#6A51A3'
        }
        
        cats[1]['A>G'] = {
            'name': 'A>G',
            'color': '#D7301F'
        }
        cats[1]['A>T'] = {
            'name': 'A>T',
            'color': '#C6DBEF'
        }
        cats[1]['A>C'] = {
            'name': 'A>C',
            'color': '#2171B5'
        }
        cats[1]['T>A'] = {
            'name': 'T>A',
            'color': '#C7E9C0'
        }
        cats[1]['T>G'] = {
            'name': 'T>G',
            'color': '#74C476'
        }
        cats[1]['T>C'] = {
            'name': 'T>C',
            'color': '#238B45'
        }
        cats[1]['G>A'] = {
            'name': 'G>A',
            'color': '#D9D9D9'
        }
        cats[1]['G>T'] = {
            'name': 'G>T',
            'color': '#969696'
        }
        cats[1]['G>C'] = {
            'name': 'G>C',
            'color': '#525252'
        }
        cats[1]['C>A'] = {
            'name': 'C>A',
            'color': '#DADAEB'
        }
        cats[1]['C>T'] = {
            'name': 'C>T',
            'color': '#9E9AC8'
        }
        cats[1]['C>G'] = {
            'name': 'C>G',
            'color': '#6A51A3'
        }
        
        
#         for cat in self.rates_data_plus[self.rates_data_plus.keys()[0]]:
#             cats[0][cat] = dict()
#             cats[0][cat]['name'] = cat
#             cats[0][cat]['color'] = cat
#             
#         for cat in self.rates_data_plus[self.rates_data_minus.keys()[0]]:
#             cats[1][cat] = dict()
#             cats[1][cat]['name'] = cat
        
        self.sections.append({
            'name': 'Conversion rates per read',
            'anchor': 'slamdunk_overall_rates',
            'content': '<p>This plot shows the individual conversion rates over all reads. \n\
                        It shows these conversion rates strand-specific: This means for a properly labelled \n\
                        sample you would see a T>C excess on \n\
                        the plus-strand and an A>G excess on the minus strand. <br>\n\
                        See the <a href="http://slamdunk.readthedocs.io/en/latest/Alleyoop.html#rates" target="_blank">slamdunk documentation</a> \n\
                        for more information on how these numbers are generated.</p>' +  
                        plots.bargraph.plot([self.rates_data_plus,self.rates_data_minus], cats, pconfig)
        })
    

    def slamdunkUtrRatesPlot (self):
        """ Generate the UTR rates plot """
        
        cats = OrderedDict()
        cats['T>C'] = {
            'name': 'T>C',
            'color': '#D7301F'
        }
        cats['A>T'] = {
            'name': 'A>T',
            'color': '#C6DBEF'
        }
        cats['A>G'] = {
            'name': 'A>G',
            'color': '#6BAED6'
        }
        cats['A>C'] = {
            'name': 'A>C',
            'color': '#2171B5'
        }
        cats['T>A'] = {
            'name': 'T>A',
            'color': '#C7E9C0'
        }
        cats['T>G'] = {
            'name': 'T>G',
            'color': '#74C476'
        }
        cats['G>A'] = {
            'name': 'G>A',
            'color': '#D9D9D9'
        }
        cats['G>T'] = {
            'name': 'G>T',
            'color': '#969696'
        }
        cats['G>C'] = {
            'name': 'G>C',
            'color': '#525252'
        }
        cats['C>A'] = {
            'name': 'C>A',
            'color': '#DADAEB'
        }
        cats['C>T'] = {
            'name': 'C>T',
            'color': '#9E9AC8'
        }
        cats['C>G'] = {
            'name': 'C>G',
            'color': '#6A51A3'
        }

        pconfig = {
            'id': 'slamdunk_utrratesplot',
            'title': 'Overall conversion rates per UTR',
            'cpswitch' : False,
            'cpswitch_c_active': False,
            'stacking' : 'normal',
        }
        
        self.sections.append({
            'name': 'Conversion rates per UTR',
            'anchor': 'slamdunk_utr_rates',
            'content': '<p>This plot shows the individual conversion rates for all UTRs.<br> \n\
                        See the <a href="http://slamdunk.readthedocs.io/en/latest/Alleyoop.html#utrrates" target="_blank">slamdunk documentation</a> \n\
                        for more information on how these numbers are generated.</p>' +  
                        plots.bargraph.plot(self.utrates_data, cats, pconfig)
        })
    
    def slamdunkPCAPlot (self):
        """ Generate the PCA plots """
        
        pconfig = {
            'id': 'slamdunk_pca',
            'title': 'Slamdunk PCA',
            'xlab' : 'PC1',
            'ylab' : 'PC2',
            'tt_label': 'PC1 {point.x:.2f}: PC2 {point.y:.2f}'
        }
        
        self.sections.append({
            'name': 'PCA (T>C based)',
            'anchor': 'slamdunk_PCA',
            'content': '<p> This plot shows the principal components of samples based on the distribution of reads with T>C conversions within UTRs. <br>\n\
                        See the <a href="http://slamdunk.readthedocs.io/en/latest/Alleyoop.html#summary" target="_blank">slamdunk documentation</a> \n\
                        for more information on how these numbers are generated.</p>' +  
                        plots.scatter.plot(self.PCA_data, pconfig) 
        })
        
    def slamdunkTcPerReadPosPlot (self):
        """ Generate the tc per read pos plots """
        
        pconfig_nontc = {
            'id': 'slamdunk_nontcperreadpos_plot',
            'title': 'Non-T>C mutations over reads',
            'ylab': 'Percent mutated %',
            'xlab': 'Position in read',
            'xDecimals': False,
            'ymin': 0,
            'tt_label': '<b>Pos {point.x}</b>: {point.y:.2f} %',
            'data_labels': [{'name': 'Forward reads +', 'ylab': 'Percent mutated %'},
                            {'name': 'Reverse reads -', 'ylab': 'Percent mutated %'}]
        }
        
        pconfig_tc = {
            'id': 'slamdunk_tcperreadpos_plot',
            'title': 'T>C conversions over reads',
            'ylab': 'Percent converted %',
            'xlab': 'Position in read',
            'xDecimals': False,
            'ymin': 0,
            'tt_label': '<b>Pos {point.x}</b>: {point.y:.2f} %',
            'data_labels': [{'name': 'Forward reads +', 'ylab': 'Percent converted %'},
                            {'name': 'Reverse reads -', 'ylab': 'Percent converted %'}]
        }        
        
        self.sections.append({
            'name': 'Non T>C mutations over read positions',
            'anchor': 'slamdunk_nontcperreadpos',
            'content': '<p>This plot shows the distribution of non T>C mutations across read positions. <br> \n\
                        See the <a href="http://slamdunk.readthedocs.io/en/latest/Alleyoop.html#tcperreadpos" target="_blank">slamdunk documentation</a> \n\
                        for more information on how these numbers are generated.</p>' +  
                        plots.linegraph.plot([self.nontc_per_readpos_plus, self.nontc_per_readpos_minus], pconfig_nontc) 
        })
        
        self.sections.append({
            'name': 'T>C conversions over read positions',
            'anchor': 'slamdunk_tcperreadpos',
            'content': '<p>This plot shows the distribution of T>C conversions across read positions. <br> \n\
                        See the <a href="http://slamdunk.readthedocs.io/en/latest/Alleyoop.html#tcperreadpos" target="_blank">slamdunk documentation</a> \n\
                        for more information on how these numbers are generated.</p>' +  
                        plots.linegraph.plot([self.tc_per_readpos_plus, self.tc_per_readpos_minus], pconfig_tc) 
        })
        
    def slamdunkTcPerUTRPosPlot (self):
        """ Generate the tc per UTR pos plots """
        
        pconfig_nontc = {
            'id': 'slamdunk_slamdunk_nontcperutrpos_plot',
            'title': 'Non-T>C mutations over UTR ends',
            'ylab': 'Percent mutated %',
            'xlab': 'Position in UTR from 3\' end',
            'xDecimals': False,
            'ymin': 0,
            'tt_label': '<b>Pos {point.x}</b>: {point.y:.2f} %',
            'data_labels': [{'name': 'UTRs on plus strand', 'ylab': 'Percent mutated %'},
                            {'name': 'UTRs on minus strand', 'ylab': 'Percent mutated %'}]
        }
        
        pconfig_tc = {
            'id': 'slamdunk_slamdunk_tcperutrpos_plot',
            'title': 'T>C conversions over UTR ends',
            'ylab': 'Percent converted %',
            'xlab': 'Position in UTR from 3\' end',
            'xDecimals': False,
            'ymin': 0,
            'tt_label': '<b>Pos {point.x}</b>: {point.y:.2f} %',
            'data_labels': [{'name': 'UTRs on plus strand', 'ylab': 'Percent converted %'},
                            {'name': 'UTRs on minus strand', 'ylab': 'Percent converted %'}]
        }        
        
        self.sections.append({
            'name': 'Non T>C mutations over UTR positions',
            'anchor': 'slamdunk_nontcperutrpos',
            'content': '<p>This plot shows the distribution of non T>C mutations across UTR positions for the last 200 bp from the 3\' UTR end. <br> \n\
                        See the <a href="http://slamdunk.readthedocs.io/en/latest/Alleyoop.html#tcperutrpos" target="_blank">slamdunk documentation</a> \n\
                        for more information on how these numbers are generated.</p>' +  
                        plots.linegraph.plot([self.nontc_per_utrpos_plus, self.nontc_per_utrpos_minus], pconfig_nontc) 
        })
        
        self.sections.append({
            'name': 'T>C conversions over UTR positions',
            'anchor': 'tcperutrpos',
            'content': '<p>This plot shows the distribution of T>C conversions across UTR positions for the last 200 bp from the 3\' UTR end . <br> \n\
                        See the <a href="http://slamdunk.readthedocs.io/en/latest/Alleyoop.html#tcperutrpos" target="_blank">slamdunk documentation</a> \n\
                        for more information on how these numbers are generated.</p>' +  
                        plots.linegraph.plot([self.tc_per_utrpos_plus, self.tc_per_utrpos_minus], pconfig_tc) 
        })