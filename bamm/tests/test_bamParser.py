###############################################################################
#                                                                             #
#    This program is free software: you can redistribute it and/or modify     #
#    it under the terms of the GNU General Public License as published by     #
#    the Free Software Foundation, either version 3 of the License, or        #
#    (at your option) any later version.                                      #
#                                                                             #
#    This program is distributed in the hope that it will be useful,          #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU General Public License for more details.                             #
#                                                                             #
#    You should have received a copy of the GNU General Public License        #
#    along with this program. If not, see <http://www.gnu.org/licenses/>.     #
#                                                                             #
###############################################################################

import random
from math import isnan
from numpy import mean, median, std, array, round, sort
from nose.tools import assert_equals, assert_true
import sys
import os
import json
import gzip

from bamm.cWrapper import *

class TestBamParser:
    @classmethod
    def setup_class(self):
        """Setup class variables before any tests."""

        # the following files already exist
        self.fastaFile = 'MG1655.fa'
        self.readKey = 'readkey.csv'
        self.bins = ['bin1', 'bin2']

        # the following data files will be in created
        self.peFile = ['pe.1.fa', 'pe.2.fa']    # coupled
        self.mpFile = 'mp.fa'                   # interleaved
        self.upFile = 'up.fa'                   # single
        self.contigsFile = 'contigs.fa'         # contigs
        self.poFile = "predicted_outputs.json"  # predicted outputs

        # we need to make some test data based on out test model
        self.model_dir = os.path.join(os.path.split(__file__)[0], "modelling")
        self.model_data_dir = os.path.join(self.model_dir, "data")
        os.system("%s -o %s -r %s -f %s -g %s %s" % \
                  (os.path.join(self.model_dir,"makeTestData.py"),
                   self.model_dir,
                   os.path.join(self.model_data_dir, self.readKey),
                   os.path.join(self.model_data_dir, self.fastaFile),
                   os.path.join(self.model_data_dir, self.bins[0]),
                   os.path.join(self.model_data_dir, self.bins[1])
                   )
                  )

        # now we can load the predicted outputs
        with open(os.path.join(self.model_dir, self.poFile), "r") as fh:
            self.predictedOutputs = json.loads(fh.readline())

        # these files will exist after the mapping is done
        self.peBamFile = ['contigs.pe.1.bam', 'contigs.pe.1.bam.bai']
        self.mpBamFile = ['contigs.mp.bam', 'contigs.mp.bam.bai']
        self.upBamFile = ['contigs.up.bam', 'contigs.up.bam.bai']

        # predicted outputs is a hash with three keys:
        self.pOutKeys = ['coverages', 'links', 'extracts']

        # keep the names of some stuff we'll be testing
        self.pOutCovTypes = ['cmean',
                             'counts',
                             'pmean',
                             'opmean',
                             'tpmean',
                             'pmedian'
                             ]
        self.extFlags = {'mix_bams': {'--mix_bams' : True, '' : False},
                         'mix_groups': {'--mix_groups' : True, '' : False},
                         'mix_reads': {'--mix_reads' : True, '' : False}}

        self.pOutContigs = ['A', 'B', 'C', 'E']

    @classmethod
    def teardown_class(self):
        self.rmTestFile(self.mpFile)
        self.rmTestFile(self.peFile[0])
        self.rmTestFile(self.peFile[1])
        self.rmTestFile(self.upFile)
        self.rmTestFile(self.contigsFile)
        self.rmTestFile(self.poFile)
        self.rmTestFile(self.peBamFile[0])
        self.rmTestFile(self.peBamFile[1])
        self.rmTestFile(self.mpBamFile[0])
        self.rmTestFile(self.mpBamFile[1])
        self.rmTestFile(self.upBamFile[0])
        self.rmTestFile(self.upBamFile[1])
        self.rmTestFile("covs")
        self.rmTestFile("links")

    @classmethod
    def rmTestFile(self, file):
        full_path = os.path.join(self.model_dir, file)
        if os.path.exists(full_path):
            os.remove(full_path)
        else:
            sys.stderr.write("No file: %s\n" % full_path)

    def test_A_make(self):
        cmd = 'bamm make --silent -d %s -i %s -c %s %s -s %s -o %s' % \
            (os.path.join(self.model_dir, self.contigsFile),
             os.path.join(self.model_dir, self.mpFile),
             os.path.join(self.model_dir, self.peFile[0]),
             os.path.join(self.model_dir, self.peFile[1]),
             os.path.join(self.model_dir, self.upFile),
             self.model_dir)
        os.system(cmd)

        EX = os.path.exists(os.path.join(self.model_dir,
                                         self.peBamFile[0]))
        EX &= os.path.exists(os.path.join(self.model_dir,
                                          self.peBamFile[1]))
        EX &= os.path.exists(os.path.join(self.model_dir,
                                          self.mpBamFile[0]))
        EX &= os.path.exists(os.path.join(self.model_dir,
                                          self.mpBamFile[1]))
        EX &= os.path.exists(os.path.join(self.model_dir,
                                          self.upBamFile[0]))
        EX &= os.path.exists(os.path.join(self.model_dir,
                                          self.upBamFile[1]))
        assert(EX)

    def squishLink(self, link):
        return ",".join([str(i) for i in link])

    def test_B_parse(self):
        squished_links = sort([self.squishLink(i) \
                               for i in self.predictedOutputs["links"]])
        links_file = os.path.join(self.model_dir, "links")
        covs_file = os.path.join(self.model_dir, "covs")
        for c_type in self.pOutCovTypes:
            # run the parser
            cmd = 'bamm parse -c %s -m %s -l %s -t 3 -b %s %s %s' % \
                    (covs_file,
                     c_type,
                     links_file,
                     os.path.join(self.model_dir, self.peBamFile[0]),
                     os.path.join(self.model_dir, self.mpBamFile[0]),
                     os.path.join(self.model_dir, self.upBamFile[0]))
            os.system(cmd)

            # read in the covs file and check it against the predicted output
            with open(covs_file) as c_fh:
                header = c_fh.readline().rstrip().split("\t")
                pe_col = 0
                mp_col = 0
                up_col = 0
                for i in [2,3,4]:
                    if not pe_col and self.peBamFile[0] in header[i]:
                        pe_col = i
                        continue
                    if not mp_col and self.mpBamFile[0] in header[i]:
                        mp_col = i
                        continue
                    if not up_col and self.upBamFile[0] in header[i]:
                        up_col = i
                        continue

                # check the coverages line by line
                for line in c_fh:
                    fields = line.rstrip().split("\t")
                    contig = fields[0]
                    row = self.predictedOutputs["coverages"][c_type][contig]
                    po = [round(float(i),4) for i in [row['PE'],
                                                      row['MP'],
                                                      row['UP']]
                          ]
                    res = [round(float(i),4) for i in [fields[pe_col],
                                                       fields[mp_col],
                                                       fields[up_col]]
                           ]
                    for i in range(len(res)):
                        assert_equals(po[i], res[i])

            # test the links file
            with open(links_file) as l_fh:
                header = l_fh.readline().rstrip().split("\t")
                these_links = []
                for line in l_fh:
                    fields = line.rstrip().split("\t")
                    fields[-1] = os.path.split(fields[-1])[1].replace(".bam",
                                                                      "")
                    these_links.append(self.squishLink(fields))
                these_links = sort(these_links)
                for i in range(len(these_links)):
                    assert_equals(these_links[i], squished_links[i])

    def test_C_extract(self):
        for i_opt in ['', '--interleave']:
            for b_opt in self.extFlags['mix_bams'].keys():
                for r_opt in self.extFlags['mix_reads'].keys():
                    for g_opt in self.extFlags['mix_groups'].keys():
                        hash_subset = self.predictedOutputs['extracts'] \
                            [i_opt] \
                            [str(self.extFlags['mix_bams'][b_opt])] \
                            [str(self.extFlags['mix_reads'][r_opt])] \
                            [str(self.extFlags['mix_groups'][g_opt])]

                        cmd = 'bamm extract %s --headers_only -o %s -t 1 -b %s %s %s -g %s %s %s %s %s' % \
                            (i_opt,
                             self.model_dir,
                             os.path.join(self.model_dir, self.peBamFile[0]),
                             os.path.join(self.model_dir, self.mpBamFile[0]),
                             os.path.join(self.model_dir, self.upBamFile[0]),
                             os.path.join(self.model_data_dir, self.bins[0]),
                             os.path.join(self.model_data_dir, self.bins[1]),
                             b_opt,
                             r_opt,
                             g_opt)

                        os.system(cmd)

                        # first test that all the files we EXPECT to be there
                        # have in fact been created
                        for file in hash_subset.keys():
                            full_path = os.path.join(self.model_dir, file)
                            assert_true(os.path.exists(full_path))

                            # now extract the headers from the file
                            headers = []
                            with gzip.open(full_path) as fh:
                                for line in fh:
                                    headers.append(line.rstrip())
                            headers = sort(headers)
                            test_headers = sort(hash_subset[file])

                            # make sure the number of headers match
                            assert_equals(len(headers), len(test_headers))

                            # now make sure that the headers are right
                            for i in range(len(headers)):
                                assert_equals(headers[i], test_headers[i])

                            self.rmTestFile(file)