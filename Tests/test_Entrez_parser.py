# Copyright 2008-2010 by Michiel de Hoon.  All rights reserved.
# Revisions copyright 2009-2016 by Peter Cock. All rights reserved.
# This code is part of the Biopython distribution and governed by its
# license.  Please see the LICENSE file that should have been included
# as part of this package.
"""Testing code for Bio.Entrez parsers."""

import os
import pickle
import unittest
from io import BytesIO

from Bio import Entrez
from Bio import StreamModeError


class GeneralTests(unittest.TestCase):
    """General tests for Bio.Entrez."""

    def test_closed_file(self):
        """Test parsing closed file fails gracefully."""
        stream = open("Entrez/einfo1.xml", "rb")
        stream.close()
        self.assertRaises(ValueError, Entrez.read, stream)

    def test_read_bytes_stream(self):
        """Test reading a file opened in binary mode."""
        with open("Entrez/pubmed1.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(len(record), 2)
        self.assertIn("MedlineCitation", record[0])

    def test_parse_bytes_stream(self):
        """Test parsing a file opened in binary mode."""
        with open("Entrez/pubmed1.xml", "rb") as stream:
            records = Entrez.parse(stream)
            n = 0
            for record in records:
                self.assertIn("MedlineCitation", record)
                n += 1
        self.assertEqual(n, 2)

    def test_read_text_file(self):
        """Test reading a file opened in text mode."""
        message = "^the XML file must be opened in binary mode.$"
        with open("Entrez/pubmed1.xml") as stream:
            with self.assertRaisesRegex(StreamModeError, message):
                Entrez.read(stream)

    def test_parse_text_file(self):
        """Test parsing a file opened in text mode."""
        message = "^the XML file must be opened in binary mode.$"
        with open("Entrez/einfo1.xml") as stream:
            records = Entrez.parse(stream)
            with self.assertRaisesRegex(StreamModeError, message):
                next(records)

    def test_BytesIO(self):
        """Test parsing a BytesIO stream (bytes not string)."""
        with open("Entrez/einfo1.xml", "rb") as stream:
            data = stream.read()
        stream = BytesIO(data)
        record = Entrez.read(stream)
        self.assertIn("DbList", record)
        stream.close()

    def test_pickle(self):
        """Test if records created by the parser can be pickled."""
        directory = "Entrez"
        filenames = os.listdir(directory)
        for filename in sorted(filenames):
            basename, extension = os.path.splitext(filename)
            if extension != ".xml":
                continue
            if filename in (
                "biosample.xml",  # DTD not specified in XML file
                "einfo3.xml",  # DTD incomplete
                "einfo4.xml",  # XML corrupted
                "journals.xml",  # Missing XML declaration
            ):
                continue
            path = os.path.join(directory, filename)
            with open(path, "rb") as stream:
                if filename in ("epost2.xml", "esummary8.xml", "esummary10.xml"):
                    # these include an ErrorElement
                    record = Entrez.read(stream, ignore_errors=True)
                else:
                    record = Entrez.read(stream)
            with BytesIO() as stream:
                pickle.dump(record, stream)
                stream.seek(0)
                pickled_record = pickle.load(stream)
            self.assertEqual(record, pickled_record)


class EInfoTest(unittest.TestCase):
    """Tests for parsing XML output returned by EInfo."""

    def test_list(self):
        """Test parsing database list returned by EInfo."""
        # To create the XML file, use
        # >>> Bio.Entrez.einfo()
        with open("Entrez/einfo1.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(
            record["DbList"],
            [
                "pubmed",
                "protein",
                "nucleotide",
                "nuccore",
                "nucgss",
                "nucest",
                "structure",
                "genome",
                "books",
                "cancerchromosomes",
                "cdd",
                "gap",
                "domains",
                "gene",
                "genomeprj",
                "gensat",
                "geo",
                "gds",
                "homologene",
                "journals",
                "mesh",
                "ncbisearch",
                "nlmcatalog",
                "omia",
                "omim",
                "pmc",
                "popset",
                "probe",
                "proteinclusters",
                "pcassay",
                "pccompound",
                "pcsubstance",
                "snp",
                "taxonomy",
                "toolkit",
                "unigene",
                "unists",
            ],
        )

    def test_pubmed1(self):
        """Test parsing database info returned by EInfo."""
        # To create the XML file, use
        # >>> Bio.Entrez.einfo(db="pubmed")
        with open("Entrez/einfo2.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record["DbInfo"]["DbName"], "pubmed")
        self.assertEqual(record["DbInfo"]["MenuName"], "PubMed")
        self.assertEqual(record["DbInfo"]["Description"], "PubMed bibliographic record")
        self.assertEqual(record["DbInfo"]["Count"], "17905967")
        self.assertEqual(record["DbInfo"]["LastUpdate"], "2008/04/15 06:42")

        self.assertEqual(len(record["DbInfo"]["FieldList"]), 40)

        self.assertEqual(record["DbInfo"]["FieldList"][0]["Name"], "ALL")
        self.assertEqual(record["DbInfo"]["FieldList"][0]["FullName"], "All Fields")
        self.assertEqual(
            record["DbInfo"]["FieldList"][0]["Description"],
            "All terms from all searchable fields",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][0]["TermCount"], "70792830")
        self.assertEqual(record["DbInfo"]["FieldList"][0]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][0]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][0]["SingleToken"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][0]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][0]["IsHidden"], "N")

        self.assertEqual(len(record["DbInfo"]["LinkList"]), 46)

        self.assertEqual(record["DbInfo"]["LinkList"][0]["Name"], "pubmed_books_refs")
        self.assertEqual(record["DbInfo"]["LinkList"][0]["Menu"], "Cited in Books")
        self.assertEqual(
            record["DbInfo"]["LinkList"][0]["Description"],
            "PubMed links associated with Books",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][0]["DbTo"], "books")

    def test_pubmed2(self):
        """Test validating the XML against the DTD."""
        # To create the XML file, use
        # >>> Bio.Entrez.einfo(db="pubmed")
        # Starting some time in 2010, the results returned by Bio.Entrez
        # included some tags that are not part of the corresponding DTD.
        from Bio.Entrez import Parser

        with open("Entrez/einfo3.xml", "rb") as stream:
            self.assertRaises(Parser.ValidationError, Entrez.read, stream)

    def test_pubmed3(self):
        """Test non-validating parser on XML with an inconsistent DTD."""
        # To create the XML file, use
        # >>> Bio.Entrez.einfo(db="pubmed")
        # Starting some time in 2010, the results returned by Bio.Entrez
        # included some tags that are not part of the corresponding DTD.
        with open("Entrez/einfo3.xml", "rb") as stream:
            record = Entrez.read(stream, validate=False)
        self.assertEqual(record["DbInfo"]["DbName"], "pubmed")
        self.assertEqual(record["DbInfo"]["MenuName"], "PubMed")
        self.assertEqual(record["DbInfo"]["Description"], "PubMed bibliographic record")
        self.assertEqual(record["DbInfo"]["Count"], "20161961")
        self.assertEqual(record["DbInfo"]["LastUpdate"], "2010/09/10 04:52")

        self.assertEqual(len(record["DbInfo"]["FieldList"]), 45)
        self.assertEqual(record["DbInfo"]["FieldList"][0]["Name"], "ALL")
        self.assertEqual(record["DbInfo"]["FieldList"][0]["FullName"], "All Fields")
        self.assertEqual(
            record["DbInfo"]["FieldList"][0]["Description"],
            "All terms from all searchable fields",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][0]["TermCount"], "89981460")
        self.assertEqual(record["DbInfo"]["FieldList"][0]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][0]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][0]["SingleToken"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][0]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][0]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][1]["Name"], "UID")
        self.assertEqual(record["DbInfo"]["FieldList"][1]["FullName"], "UID")
        self.assertEqual(
            record["DbInfo"]["FieldList"][1]["Description"],
            "Unique number assigned to publication",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][1]["TermCount"], "0")
        self.assertEqual(record["DbInfo"]["FieldList"][1]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][1]["IsNumerical"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][1]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][1]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][1]["IsHidden"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][2]["Name"], "FILT")
        self.assertEqual(record["DbInfo"]["FieldList"][2]["FullName"], "Filter")
        self.assertEqual(
            record["DbInfo"]["FieldList"][2]["Description"], "Limits the records"
        )
        self.assertEqual(record["DbInfo"]["FieldList"][2]["TermCount"], "4070")
        self.assertEqual(record["DbInfo"]["FieldList"][2]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][2]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][2]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][2]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][2]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][3]["Name"], "TITL")
        self.assertEqual(record["DbInfo"]["FieldList"][3]["FullName"], "Title")
        self.assertEqual(
            record["DbInfo"]["FieldList"][3]["Description"],
            "Words in title of publication",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][3]["TermCount"], "12475481")
        self.assertEqual(record["DbInfo"]["FieldList"][3]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][3]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][3]["SingleToken"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][3]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][3]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][4]["Name"], "WORD")
        self.assertEqual(record["DbInfo"]["FieldList"][4]["FullName"], "Text Word")
        self.assertEqual(
            record["DbInfo"]["FieldList"][4]["Description"],
            "Free text associated with publication",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][4]["TermCount"], "39413498")
        self.assertEqual(record["DbInfo"]["FieldList"][4]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][4]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][4]["SingleToken"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][4]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][4]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][5]["Name"], "MESH")
        self.assertEqual(record["DbInfo"]["FieldList"][5]["FullName"], "MeSH Terms")
        self.assertEqual(
            record["DbInfo"]["FieldList"][5]["Description"],
            "Medical Subject Headings assigned to publication",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][5]["TermCount"], "554666")
        self.assertEqual(record["DbInfo"]["FieldList"][5]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][5]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][5]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][5]["Hierarchy"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][5]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][6]["Name"], "MAJR")
        self.assertEqual(
            record["DbInfo"]["FieldList"][6]["FullName"], "MeSH Major Topic"
        )
        self.assertEqual(
            record["DbInfo"]["FieldList"][6]["Description"],
            "MeSH terms of major importance to publication",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][6]["TermCount"], "493091")
        self.assertEqual(record["DbInfo"]["FieldList"][6]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][6]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][6]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][6]["Hierarchy"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][6]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][7]["Name"], "AUTH")
        self.assertEqual(record["DbInfo"]["FieldList"][7]["FullName"], "Author")
        self.assertEqual(
            record["DbInfo"]["FieldList"][7]["Description"], "Author(s) of publication"
        )
        self.assertEqual(record["DbInfo"]["FieldList"][7]["TermCount"], "11268262")
        self.assertEqual(record["DbInfo"]["FieldList"][7]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][7]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][7]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][7]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][7]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][8]["Name"], "JOUR")
        self.assertEqual(record["DbInfo"]["FieldList"][8]["FullName"], "Journal")
        self.assertEqual(
            record["DbInfo"]["FieldList"][8]["Description"],
            "Journal abbreviation of publication",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][8]["TermCount"], "118354")
        self.assertEqual(record["DbInfo"]["FieldList"][8]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][8]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][8]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][8]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][8]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][9]["Name"], "AFFL")
        self.assertEqual(record["DbInfo"]["FieldList"][9]["FullName"], "Affiliation")
        self.assertEqual(
            record["DbInfo"]["FieldList"][9]["Description"],
            "Author's institutional affiliation and address",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][9]["TermCount"], "17538809")
        self.assertEqual(record["DbInfo"]["FieldList"][9]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][9]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][9]["SingleToken"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][9]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][9]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][10]["Name"], "ECNO")
        self.assertEqual(record["DbInfo"]["FieldList"][10]["FullName"], "EC/RN Number")
        self.assertEqual(
            record["DbInfo"]["FieldList"][10]["Description"],
            "EC number for enzyme or CAS registry number",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][10]["TermCount"], "82892")
        self.assertEqual(record["DbInfo"]["FieldList"][10]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][10]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][10]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][10]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][10]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][11]["Name"], "SUBS")
        self.assertEqual(
            record["DbInfo"]["FieldList"][11]["FullName"], "Substance Name"
        )
        self.assertEqual(
            record["DbInfo"]["FieldList"][11]["Description"],
            "CAS chemical name or MEDLINE Substance Name",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][11]["TermCount"], "204197")
        self.assertEqual(record["DbInfo"]["FieldList"][11]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][11]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][11]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][11]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][11]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][12]["Name"], "PDAT")
        self.assertEqual(
            record["DbInfo"]["FieldList"][12]["FullName"], "Publication Date"
        )
        self.assertEqual(
            record["DbInfo"]["FieldList"][12]["Description"], "Date of publication"
        )
        self.assertEqual(record["DbInfo"]["FieldList"][12]["TermCount"], "35200")
        self.assertEqual(record["DbInfo"]["FieldList"][12]["IsDate"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][12]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][12]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][12]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][12]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][13]["Name"], "EDAT")
        self.assertEqual(record["DbInfo"]["FieldList"][13]["FullName"], "Entrez Date")
        self.assertEqual(
            record["DbInfo"]["FieldList"][13]["Description"],
            "Date publication first accessible through Entrez",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][13]["TermCount"], "33978")
        self.assertEqual(record["DbInfo"]["FieldList"][13]["IsDate"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][13]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][13]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][13]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][13]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][14]["Name"], "VOL")
        self.assertEqual(record["DbInfo"]["FieldList"][14]["FullName"], "Volume")
        self.assertEqual(
            record["DbInfo"]["FieldList"][14]["Description"],
            "Volume number of publication",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][14]["TermCount"], "12026")
        self.assertEqual(record["DbInfo"]["FieldList"][14]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][14]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][14]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][14]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][14]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][15]["Name"], "PAGE")
        self.assertEqual(record["DbInfo"]["FieldList"][15]["FullName"], "Pagination")
        self.assertEqual(
            record["DbInfo"]["FieldList"][15]["Description"],
            "Page number(s) of publication",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][15]["TermCount"], "1274867")
        self.assertEqual(record["DbInfo"]["FieldList"][15]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][15]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][15]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][15]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][15]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][16]["Name"], "PTYP")
        self.assertEqual(
            record["DbInfo"]["FieldList"][16]["FullName"], "Publication Type"
        )
        self.assertEqual(
            record["DbInfo"]["FieldList"][16]["Description"],
            "Type of publication (e.g., review)",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][16]["TermCount"], "71")
        self.assertEqual(record["DbInfo"]["FieldList"][16]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][16]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][16]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][16]["Hierarchy"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][16]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][17]["Name"], "LANG")
        self.assertEqual(record["DbInfo"]["FieldList"][17]["FullName"], "Language")
        self.assertEqual(
            record["DbInfo"]["FieldList"][17]["Description"], "Language of publication"
        )
        self.assertEqual(record["DbInfo"]["FieldList"][17]["TermCount"], "57")
        self.assertEqual(record["DbInfo"]["FieldList"][17]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][17]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][17]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][17]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][17]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][18]["Name"], "ISS")
        self.assertEqual(record["DbInfo"]["FieldList"][18]["FullName"], "Issue")
        self.assertEqual(
            record["DbInfo"]["FieldList"][18]["Description"],
            "Issue number of publication",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][18]["TermCount"], "16835")
        self.assertEqual(record["DbInfo"]["FieldList"][18]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][18]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][18]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][18]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][18]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][19]["Name"], "SUBH")
        self.assertEqual(
            record["DbInfo"]["FieldList"][19]["FullName"], "MeSH Subheading"
        )
        self.assertEqual(
            record["DbInfo"]["FieldList"][19]["Description"],
            "Additional specificity for MeSH term",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][19]["TermCount"], "83")
        self.assertEqual(record["DbInfo"]["FieldList"][19]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][19]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][19]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][19]["Hierarchy"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][19]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][20]["Name"], "SI")
        self.assertEqual(
            record["DbInfo"]["FieldList"][20]["FullName"], "Secondary Source ID"
        )
        self.assertEqual(
            record["DbInfo"]["FieldList"][20]["Description"],
            "Cross-reference from publication to other databases",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][20]["TermCount"], "3821402")
        self.assertEqual(record["DbInfo"]["FieldList"][20]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][20]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][20]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][20]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][20]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][21]["Name"], "MHDA")
        self.assertEqual(record["DbInfo"]["FieldList"][21]["FullName"], "MeSH Date")
        self.assertEqual(
            record["DbInfo"]["FieldList"][21]["Description"],
            "Date publication was indexed with MeSH terms",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][21]["TermCount"], "33923")
        self.assertEqual(record["DbInfo"]["FieldList"][21]["IsDate"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][21]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][21]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][21]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][21]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][22]["Name"], "TIAB")
        self.assertEqual(
            record["DbInfo"]["FieldList"][22]["FullName"], "Title/Abstract"
        )
        self.assertEqual(
            record["DbInfo"]["FieldList"][22]["Description"],
            "Free text associated with Abstract/Title",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][22]["TermCount"], "35092258")
        self.assertEqual(record["DbInfo"]["FieldList"][22]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][22]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][22]["SingleToken"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][22]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][22]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][23]["Name"], "OTRM")
        self.assertEqual(record["DbInfo"]["FieldList"][23]["FullName"], "Other Term")
        self.assertEqual(
            record["DbInfo"]["FieldList"][23]["Description"],
            "Other terms associated with publication",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][23]["TermCount"], "333870")
        self.assertEqual(record["DbInfo"]["FieldList"][23]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][23]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][23]["SingleToken"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][23]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][23]["IsHidden"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][24]["Name"], "INVR")
        self.assertEqual(record["DbInfo"]["FieldList"][24]["FullName"], "Investigator")
        self.assertEqual(
            record["DbInfo"]["FieldList"][24]["Description"], "Investigator"
        )
        self.assertEqual(record["DbInfo"]["FieldList"][24]["TermCount"], "516245")
        self.assertEqual(record["DbInfo"]["FieldList"][24]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][24]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][24]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][24]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][24]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][25]["Name"], "COLN")
        self.assertEqual(
            record["DbInfo"]["FieldList"][25]["FullName"], "Corporate Author"
        )
        self.assertEqual(
            record["DbInfo"]["FieldList"][25]["Description"],
            "Corporate Author of publication",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][25]["TermCount"], "132665")
        self.assertEqual(record["DbInfo"]["FieldList"][25]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][25]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][25]["SingleToken"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][25]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][25]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][26]["Name"], "CNTY")
        self.assertEqual(
            record["DbInfo"]["FieldList"][26]["FullName"], "Place of Publication"
        )
        self.assertEqual(
            record["DbInfo"]["FieldList"][26]["Description"], "Country of publication"
        )
        self.assertEqual(record["DbInfo"]["FieldList"][26]["TermCount"], "279")
        self.assertEqual(record["DbInfo"]["FieldList"][26]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][26]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][26]["SingleToken"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][26]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][26]["IsHidden"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][27]["Name"], "PAPX")
        self.assertEqual(
            record["DbInfo"]["FieldList"][27]["FullName"], "Pharmacological Action"
        )
        self.assertEqual(
            record["DbInfo"]["FieldList"][27]["Description"],
            "MeSH pharmacological action pre-explosions",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][27]["TermCount"], "420")
        self.assertEqual(record["DbInfo"]["FieldList"][27]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][27]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][27]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][27]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][27]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][28]["Name"], "GRNT")
        self.assertEqual(record["DbInfo"]["FieldList"][28]["FullName"], "Grant Number")
        self.assertEqual(
            record["DbInfo"]["FieldList"][28]["Description"], "NIH Grant Numbers"
        )
        self.assertEqual(record["DbInfo"]["FieldList"][28]["TermCount"], "2588283")
        self.assertEqual(record["DbInfo"]["FieldList"][28]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][28]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][28]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][28]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][28]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][29]["Name"], "MDAT")
        self.assertEqual(
            record["DbInfo"]["FieldList"][29]["FullName"], "Modification Date"
        )
        self.assertEqual(
            record["DbInfo"]["FieldList"][29]["Description"],
            "Date of last modification",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][29]["TermCount"], "2777")
        self.assertEqual(record["DbInfo"]["FieldList"][29]["IsDate"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][29]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][29]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][29]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][29]["IsHidden"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][30]["Name"], "CDAT")
        self.assertEqual(
            record["DbInfo"]["FieldList"][30]["FullName"], "Completion Date"
        )
        self.assertEqual(
            record["DbInfo"]["FieldList"][30]["Description"], "Date of completion"
        )
        self.assertEqual(record["DbInfo"]["FieldList"][30]["TermCount"], "9268")
        self.assertEqual(record["DbInfo"]["FieldList"][30]["IsDate"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][30]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][30]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][30]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][30]["IsHidden"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][31]["Name"], "PID")
        self.assertEqual(record["DbInfo"]["FieldList"][31]["FullName"], "Publisher ID")
        self.assertEqual(
            record["DbInfo"]["FieldList"][31]["Description"], "Publisher ID"
        )
        self.assertEqual(record["DbInfo"]["FieldList"][31]["TermCount"], "8894288")
        self.assertEqual(record["DbInfo"]["FieldList"][31]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][31]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][31]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][31]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][31]["IsHidden"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][32]["Name"], "FAUT")
        self.assertEqual(record["DbInfo"]["FieldList"][32]["FullName"], "First Author")
        self.assertEqual(
            record["DbInfo"]["FieldList"][32]["Description"],
            "First Author of publication",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][32]["TermCount"], "6068222")
        self.assertEqual(record["DbInfo"]["FieldList"][32]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][32]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][32]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][32]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][32]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][33]["Name"], "FULL")
        self.assertEqual(
            record["DbInfo"]["FieldList"][33]["FullName"], "Full Author Name"
        )
        self.assertEqual(
            record["DbInfo"]["FieldList"][33]["Description"],
            "Full Author Name(s) of publication",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][33]["TermCount"], "6419103")
        self.assertEqual(record["DbInfo"]["FieldList"][33]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][33]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][33]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][33]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][33]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][34]["Name"], "FINV")
        self.assertEqual(
            record["DbInfo"]["FieldList"][34]["FullName"], "Full Investigator Name"
        )
        self.assertEqual(
            record["DbInfo"]["FieldList"][34]["Description"],
            "Full name of investigator",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][34]["TermCount"], "243898")
        self.assertEqual(record["DbInfo"]["FieldList"][34]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][34]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][34]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][34]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][34]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][35]["Name"], "TT")
        self.assertEqual(
            record["DbInfo"]["FieldList"][35]["FullName"], "Transliterated Title"
        )
        self.assertEqual(
            record["DbInfo"]["FieldList"][35]["Description"],
            "Words in transliterated title of publication",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][35]["TermCount"], "2177885")
        self.assertEqual(record["DbInfo"]["FieldList"][35]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][35]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][35]["SingleToken"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][35]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][35]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][36]["Name"], "LAUT")
        self.assertEqual(record["DbInfo"]["FieldList"][36]["FullName"], "Last Author")
        self.assertEqual(
            record["DbInfo"]["FieldList"][36]["Description"],
            "Last Author of publication",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][36]["TermCount"], "5655625")
        self.assertEqual(record["DbInfo"]["FieldList"][36]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][36]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][36]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][36]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][36]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][37]["Name"], "PPDT")
        self.assertEqual(
            record["DbInfo"]["FieldList"][37]["FullName"], "Print Publication Date"
        )
        self.assertEqual(
            record["DbInfo"]["FieldList"][37]["Description"],
            "Date of print publication",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][37]["TermCount"], "35164")
        self.assertEqual(record["DbInfo"]["FieldList"][37]["IsDate"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][37]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][37]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][37]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][37]["IsHidden"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][38]["Name"], "EPDT")
        self.assertEqual(
            record["DbInfo"]["FieldList"][38]["FullName"], "Electronic Publication Date"
        )
        self.assertEqual(
            record["DbInfo"]["FieldList"][38]["Description"],
            "Date of Electronic publication",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][38]["TermCount"], "4282")
        self.assertEqual(record["DbInfo"]["FieldList"][38]["IsDate"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][38]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][38]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][38]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][38]["IsHidden"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][39]["Name"], "LID")
        self.assertEqual(record["DbInfo"]["FieldList"][39]["FullName"], "Location ID")
        self.assertEqual(
            record["DbInfo"]["FieldList"][39]["Description"], "ELocation ID"
        )
        self.assertEqual(record["DbInfo"]["FieldList"][39]["TermCount"], "56212")
        self.assertEqual(record["DbInfo"]["FieldList"][39]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][39]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][39]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][39]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][39]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][40]["Name"], "CRDT")
        self.assertEqual(record["DbInfo"]["FieldList"][40]["FullName"], "Create Date")
        self.assertEqual(
            record["DbInfo"]["FieldList"][40]["Description"],
            "Date publication first accessible through Entrez",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][40]["TermCount"], "27563")
        self.assertEqual(record["DbInfo"]["FieldList"][40]["IsDate"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][40]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][40]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][40]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][40]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][41]["Name"], "BOOK")
        self.assertEqual(record["DbInfo"]["FieldList"][41]["FullName"], "Book")
        self.assertEqual(
            record["DbInfo"]["FieldList"][41]["Description"],
            "ID of the book that contains the document",
        )
        self.assertEqual(record["DbInfo"]["FieldList"][41]["TermCount"], "342")
        self.assertEqual(record["DbInfo"]["FieldList"][41]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][41]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][41]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][41]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][41]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][42]["Name"], "ED")
        self.assertEqual(record["DbInfo"]["FieldList"][42]["FullName"], "Editor")
        self.assertEqual(
            record["DbInfo"]["FieldList"][42]["Description"], "Section's Editor"
        )
        self.assertEqual(record["DbInfo"]["FieldList"][42]["TermCount"], "335")
        self.assertEqual(record["DbInfo"]["FieldList"][42]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][42]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][42]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][42]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][42]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][43]["Name"], "ISBN")
        self.assertEqual(record["DbInfo"]["FieldList"][43]["FullName"], "ISBN")
        self.assertEqual(record["DbInfo"]["FieldList"][43]["Description"], "ISBN")
        self.assertEqual(record["DbInfo"]["FieldList"][43]["TermCount"], "189")
        self.assertEqual(record["DbInfo"]["FieldList"][43]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][43]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][43]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][43]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][43]["IsHidden"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][44]["Name"], "PUBN")
        self.assertEqual(record["DbInfo"]["FieldList"][44]["FullName"], "Publisher")
        self.assertEqual(
            record["DbInfo"]["FieldList"][44]["Description"], "Publisher's name"
        )
        self.assertEqual(record["DbInfo"]["FieldList"][44]["TermCount"], "161")
        self.assertEqual(record["DbInfo"]["FieldList"][44]["IsDate"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][44]["IsNumerical"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][44]["SingleToken"], "Y")
        self.assertEqual(record["DbInfo"]["FieldList"][44]["Hierarchy"], "N")
        self.assertEqual(record["DbInfo"]["FieldList"][44]["IsHidden"], "N")
        self.assertEqual(len(record["DbInfo"]["LinkList"]), 57)
        self.assertEqual(record["DbInfo"]["LinkList"][0]["Name"], "pubmed_biosample")
        self.assertEqual(record["DbInfo"]["LinkList"][0]["Menu"], "BioSample Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][0]["Description"], "BioSample links"
        )
        self.assertEqual(record["DbInfo"]["LinkList"][0]["DbTo"], "biosample")
        self.assertEqual(record["DbInfo"]["LinkList"][1]["Name"], "pubmed_biosystems")
        self.assertEqual(record["DbInfo"]["LinkList"][1]["Menu"], "BioSystem Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][1]["Description"],
            "Pathways and biological systems (BioSystems) that cite the current articles. Citations are from the BioSystems source databases (KEGG and BioCyc).",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][1]["DbTo"], "biosystems")
        self.assertEqual(record["DbInfo"]["LinkList"][2]["Name"], "pubmed_books_refs")
        self.assertEqual(record["DbInfo"]["LinkList"][2]["Menu"], "Cited in Books")
        self.assertEqual(
            record["DbInfo"]["LinkList"][2]["Description"],
            "NCBI Bookshelf books that cite the current articles.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][2]["DbTo"], "books")
        self.assertEqual(
            record["DbInfo"]["LinkList"][3]["Name"], "pubmed_cancerchromosomes"
        )
        self.assertEqual(record["DbInfo"]["LinkList"][3]["Menu"], "CancerChrom Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][3]["Description"],
            "Cancer chromosome records that cite the current articles.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][3]["DbTo"], "cancerchromosomes")
        self.assertEqual(record["DbInfo"]["LinkList"][4]["Name"], "pubmed_cdd")
        self.assertEqual(record["DbInfo"]["LinkList"][4]["Menu"], "Domain Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][4]["Description"],
            "Conserved Domain Database (CDD) records that cite the current articles. Citations are from the CDD source database records (PFAM, SMART).",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][4]["DbTo"], "cdd")
        self.assertEqual(record["DbInfo"]["LinkList"][5]["Name"], "pubmed_domains")
        self.assertEqual(record["DbInfo"]["LinkList"][5]["Menu"], "3D Domain Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][5]["Description"],
            "Structural domains in the NCBI Structure database that are parts of the 3D structures reported in the current articles.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][5]["DbTo"], "domains")
        self.assertEqual(record["DbInfo"]["LinkList"][6]["Name"], "pubmed_epigenomics")
        self.assertEqual(record["DbInfo"]["LinkList"][6]["Menu"], "Epigenomics Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][6]["Description"],
            "Related Epigenomics records",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][6]["DbTo"], "epigenomics")
        self.assertEqual(record["DbInfo"]["LinkList"][7]["Name"], "pubmed_gap")
        self.assertEqual(record["DbInfo"]["LinkList"][7]["Menu"], "dbGaP Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][7]["Description"],
            "Genotypes and Phenotypes (dbGaP) studies that cite the current articles.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][7]["DbTo"], "gap")
        self.assertEqual(record["DbInfo"]["LinkList"][8]["Name"], "pubmed_gds")
        self.assertEqual(record["DbInfo"]["LinkList"][8]["Menu"], "GEO DataSet Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][8]["Description"],
            "Gene expression and molecular abundance data reported in the current articles that are also included in the curated Gene Expression Omnibus (GEO) DataSets.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][8]["DbTo"], "gds")
        self.assertEqual(record["DbInfo"]["LinkList"][9]["Name"], "pubmed_gene")
        self.assertEqual(record["DbInfo"]["LinkList"][9]["Menu"], "Gene Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][9]["Description"],
            "Gene records that cite the current articles. Citations in Gene are added manually by NCBI or imported from outside public resources.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][9]["DbTo"], "gene")
        self.assertEqual(
            record["DbInfo"]["LinkList"][10]["Name"], "pubmed_gene_bookrecords"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][10]["Menu"], "Gene (from Bookshelf)"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][10]["Description"],
            "Gene records in this citation",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][10]["DbTo"], "gene")
        self.assertEqual(
            record["DbInfo"]["LinkList"][11]["Name"], "pubmed_gene_citedinomim"
        )
        self.assertEqual(record["DbInfo"]["LinkList"][11]["Menu"], "Gene (OMIM) Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][11]["Description"],
            "Gene records associated with Online Mendelian Inheritance in Man (OMIM) records that cite the current articles in their reference lists.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][11]["DbTo"], "gene")
        self.assertEqual(record["DbInfo"]["LinkList"][12]["Name"], "pubmed_gene_rif")
        self.assertEqual(
            record["DbInfo"]["LinkList"][12]["Menu"], "Gene (GeneRIF) Links"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][12]["Description"],
            "Gene records that have the current articles as Reference into Function citations (GeneRIFs). NLM staff reviewing the literature while indexing MEDLINE add GeneRIFs manually.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][12]["DbTo"], "gene")
        self.assertEqual(record["DbInfo"]["LinkList"][13]["Name"], "pubmed_genome")
        self.assertEqual(record["DbInfo"]["LinkList"][13]["Menu"], "Genome Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][13]["Description"],
            "Genome records that include the current articles as references. These are typically the articles that report the sequencing and analysis of the genome.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][13]["DbTo"], "genome")
        self.assertEqual(record["DbInfo"]["LinkList"][14]["Name"], "pubmed_genomeprj")
        self.assertEqual(record["DbInfo"]["LinkList"][14]["Menu"], "Project Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][14]["Description"],
            "Genome Project records that cite the current articles. References on Genome Projects include manually added citations and those included on sequences in the project.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][14]["DbTo"], "genomeprj")
        self.assertEqual(record["DbInfo"]["LinkList"][15]["Name"], "pubmed_gensat")
        self.assertEqual(record["DbInfo"]["LinkList"][15]["Menu"], "GENSAT Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][15]["Description"],
            "Gene Expression Nervous System Atlas (GENSAT) records that cite the current articles. References on GENSAT records are provided by GENSAT investigators, and also include references on the corresponding NCBI Gene record.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][15]["DbTo"], "gensat")
        self.assertEqual(record["DbInfo"]["LinkList"][16]["Name"], "pubmed_geo")
        self.assertEqual(record["DbInfo"]["LinkList"][16]["Menu"], "GEO Profile Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][16]["Description"],
            "Gene Expression Omnibus (GEO) Profiles of molecular abundance data. The current articles are references on the Gene record associated with the GEO profile.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][16]["DbTo"], "geo")
        self.assertEqual(record["DbInfo"]["LinkList"][17]["Name"], "pubmed_homologene")
        self.assertEqual(record["DbInfo"]["LinkList"][17]["Menu"], "HomoloGene Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][17]["Description"],
            "HomoloGene clusters of homologous genes and sequences that cite the current articles. These are references on the Gene and sequence records in the HomoloGene entry.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][17]["DbTo"], "homologene")
        self.assertEqual(record["DbInfo"]["LinkList"][18]["Name"], "pubmed_nuccore")
        self.assertEqual(record["DbInfo"]["LinkList"][18]["Menu"], "Nucleotide Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][18]["Description"],
            "Primary database (GenBank) nucleotide records reported in the current articles as well as Reference Sequences (RefSeqs) that include the articles as references.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][18]["DbTo"], "nuccore")
        self.assertEqual(
            record["DbInfo"]["LinkList"][19]["Name"], "pubmed_nuccore_refseq"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][19]["Menu"], "Nucleotide (RefSeq) Links"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][19]["Description"],
            "NCBI nucleotide Reference Sequences (RefSeqs) that are cited in the current articles, included in the corresponding Gene Reference into Function, or that include the PubMed articles as references.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][19]["DbTo"], "nuccore")
        self.assertEqual(
            record["DbInfo"]["LinkList"][20]["Name"], "pubmed_nuccore_weighted"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][20]["Menu"], "Nucleotide (Weighted) Links"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][20]["Description"],
            "Nucleotide records associated with the current articles through the Gene database. These are the related sequences on the Gene record that are added manually by NCBI.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][20]["DbTo"], "nuccore")
        self.assertEqual(record["DbInfo"]["LinkList"][21]["Name"], "pubmed_nucest")
        self.assertEqual(record["DbInfo"]["LinkList"][21]["Menu"], "EST Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][21]["Description"],
            "Expressed Sequence Tag (EST) nucleotide sequence records reported in the current articles.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][21]["DbTo"], "nucest")
        self.assertEqual(record["DbInfo"]["LinkList"][22]["Name"], "pubmed_nucgss")
        self.assertEqual(record["DbInfo"]["LinkList"][22]["Menu"], "GSS Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][22]["Description"],
            "Genome Survey Sequence (GSS) nucleotide records reported in the current articles.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][22]["DbTo"], "nucgss")
        self.assertEqual(record["DbInfo"]["LinkList"][23]["Name"], "pubmed_omia")
        self.assertEqual(record["DbInfo"]["LinkList"][23]["Menu"], "OMIA Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][23]["Description"],
            "Online Mendelian Inheritance in Animals (OMIA) records that cite the current articles.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][23]["DbTo"], "omia")
        self.assertEqual(
            record["DbInfo"]["LinkList"][24]["Name"], "pubmed_omim_bookrecords"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][24]["Menu"], "OMIM (from Bookshelf)"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][24]["Description"],
            "OMIM records in this citation",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][24]["DbTo"], "omim")
        self.assertEqual(
            record["DbInfo"]["LinkList"][25]["Name"], "pubmed_omim_calculated"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][25]["Menu"], "OMIM (calculated) Links"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][25]["Description"],
            "Online Mendelian Inheritance in Man (OMIM) records that include the current articles as references in the light bulb links within or in the citations at the end of the OMIM record. The references available through the light bulb link are collected using the PubMed related articles algorithm to identify records with similar terminology to the OMIM record.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][25]["DbTo"], "omim")
        self.assertEqual(record["DbInfo"]["LinkList"][26]["Name"], "pubmed_omim_cited")
        self.assertEqual(record["DbInfo"]["LinkList"][26]["Menu"], "OMIM (cited) Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][26]["Description"],
            "Online Mendelian Inheritance in Man (OMIM) records that include the current articles as reference cited at the end of the OMIM record.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][26]["DbTo"], "omim")
        self.assertEqual(record["DbInfo"]["LinkList"][27]["Name"], "pubmed_pcassay")
        self.assertEqual(record["DbInfo"]["LinkList"][27]["Menu"], "BioAssay Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][27]["Description"],
            "PubChem BioAssay experiments on the biological activities of small molecules that cite the current articles. The depositors of BioAssay data provide these references.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][27]["DbTo"], "pcassay")
        self.assertEqual(record["DbInfo"]["LinkList"][28]["Name"], "pubmed_pccompound")
        self.assertEqual(record["DbInfo"]["LinkList"][28]["Menu"], "Compound Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][28]["Description"],
            "PubChem chemical compound records that cite the current articles. These references are taken from those provided on submitted PubChem chemical substance records. Multiple substance records may contribute to the PubChem compound record.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][28]["DbTo"], "pccompound")
        self.assertEqual(
            record["DbInfo"]["LinkList"][29]["Name"], "pubmed_pccompound_mesh"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][29]["Menu"], "Compound (MeSH Keyword)"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][29]["Description"],
            "PubChem chemical compound records that are classified under the same Medical Subject Headings (MeSH) controlled vocabulary as the current articles.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][29]["DbTo"], "pccompound")
        self.assertEqual(
            record["DbInfo"]["LinkList"][30]["Name"], "pubmed_pccompound_publisher"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][30]["Menu"], "Compound (Publisher) Links"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][30]["Description"],
            "Link to publisher deposited structures in the PubChem Compound database.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][30]["DbTo"], "pccompound")
        self.assertEqual(record["DbInfo"]["LinkList"][31]["Name"], "pubmed_pcsubstance")
        self.assertEqual(record["DbInfo"]["LinkList"][31]["Menu"], "Substance Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][31]["Description"],
            "PubChem chemical substance records that cite the current articles. These references are taken from those provided on submitted PubChem chemical substance records.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][31]["DbTo"], "pcsubstance")
        self.assertEqual(
            record["DbInfo"]["LinkList"][32]["Name"], "pubmed_pcsubstance_bookrecords"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][32]["Menu"],
            "PubChem Substance (from Bookshelf)",
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][32]["Description"],
            "Structures in the PubChem Substance database in this citation",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][32]["DbTo"], "pcsubstance")
        self.assertEqual(
            record["DbInfo"]["LinkList"][33]["Name"], "pubmed_pcsubstance_mesh"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][33]["Menu"], "Substance (MeSH Keyword)"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][33]["Description"],
            "PubChem chemical substance (submitted) records that are classified under the same Medical Subject Headings (MeSH) controlled vocabulary as the current articles.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][33]["DbTo"], "pcsubstance")
        self.assertEqual(
            record["DbInfo"]["LinkList"][34]["Name"], "pubmed_pcsubstance_publisher"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][34]["Menu"], "Substance (Publisher) Links"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][34]["Description"],
            "Publisher deposited structures in the PubChem Compound database that are reported in the current articles.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][34]["DbTo"], "pcsubstance")
        self.assertEqual(record["DbInfo"]["LinkList"][35]["Name"], "pubmed_pepdome")
        self.assertEqual(record["DbInfo"]["LinkList"][35]["Menu"], "Peptidome Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][35]["Description"],
            "Protein mass spectrometry and other proteomics data from the Peptidome database reported in the current articles.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][35]["DbTo"], "pepdome")
        self.assertEqual(record["DbInfo"]["LinkList"][36]["Name"], "pubmed_pmc")
        self.assertEqual(record["DbInfo"]["LinkList"][36]["Menu"], "PMC Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][36]["Description"],
            "Free full-text versions of the current articles in the PubMed Central database.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][36]["DbTo"], "pmc")
        self.assertEqual(
            record["DbInfo"]["LinkList"][37]["Name"], "pubmed_pmc_bookrecords"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][37]["Menu"],
            "References in PMC for this Bookshelf citation",
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][37]["Description"],
            "Full text of articles in PubMed Central cited in this record",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][37]["DbTo"], "pmc")
        self.assertEqual(record["DbInfo"]["LinkList"][38]["Name"], "pubmed_pmc_embargo")
        self.assertEqual(record["DbInfo"]["LinkList"][38]["Menu"], "")
        self.assertEqual(
            record["DbInfo"]["LinkList"][38]["Description"],
            "Embargoed PMC article associated with PubMed",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][38]["DbTo"], "pmc")
        self.assertEqual(record["DbInfo"]["LinkList"][39]["Name"], "pubmed_pmc_local")
        self.assertEqual(record["DbInfo"]["LinkList"][39]["Menu"], "")
        self.assertEqual(
            record["DbInfo"]["LinkList"][39]["Description"],
            "Free full text articles in PMC",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][39]["DbTo"], "pmc")
        self.assertEqual(record["DbInfo"]["LinkList"][40]["Name"], "pubmed_pmc_refs")
        self.assertEqual(record["DbInfo"]["LinkList"][40]["Menu"], "Cited in PMC")
        self.assertEqual(
            record["DbInfo"]["LinkList"][40]["Description"],
            "Full-text articles in the PubMed Central Database that cite the current articles.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][40]["DbTo"], "pmc")
        self.assertEqual(record["DbInfo"]["LinkList"][41]["Name"], "pubmed_popset")
        self.assertEqual(record["DbInfo"]["LinkList"][41]["Menu"], "PopSet Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][41]["Description"],
            "Sets of sequences from population and evolutionary genetic studies in the PopSet database reported in the current articles.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][41]["DbTo"], "popset")
        self.assertEqual(record["DbInfo"]["LinkList"][42]["Name"], "pubmed_probe")
        self.assertEqual(record["DbInfo"]["LinkList"][42]["Menu"], "Probe Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][42]["Description"],
            "Molecular reagents in the Probe database that cite the current articles. References in Probe are provided by submitters of the data.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][42]["DbTo"], "probe")
        self.assertEqual(record["DbInfo"]["LinkList"][43]["Name"], "pubmed_protein")
        self.assertEqual(record["DbInfo"]["LinkList"][43]["Menu"], "Protein Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][43]["Description"],
            "Protein translation features of primary database (GenBank) nucleotide records reported in the current articles as well as Reference Sequences (RefSeqs) that include the articles as references.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][43]["DbTo"], "protein")
        self.assertEqual(
            record["DbInfo"]["LinkList"][44]["Name"], "pubmed_protein_refseq"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][44]["Menu"], "Protein (RefSeq) Links"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][44]["Description"],
            "NCBI protein Reference Sequences (RefSeqs) that are cited in the current articles, included in the corresponding Gene Reference into Function, or that include the PubMed articles as references.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][44]["DbTo"], "protein")
        self.assertEqual(
            record["DbInfo"]["LinkList"][45]["Name"], "pubmed_protein_weighted"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][45]["Menu"], "Protein (Weighted) Links"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][45]["Description"],
            "Protein records associated with the current articles through related Gene database records. These are the related sequences on the Gene record that are added manually by NCBI.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][45]["DbTo"], "protein")
        self.assertEqual(
            record["DbInfo"]["LinkList"][46]["Name"], "pubmed_proteinclusters"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][46]["Menu"], "Protein Cluster Links"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][46]["Description"],
            "Clusters of related proteins from the Protein Clusters database that cite the current articles. Sources of references in Protein Clusters include the associated Gene and Conserved Domain records as well as NCBI added citations.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][46]["DbTo"], "proteinclusters")
        self.assertEqual(record["DbInfo"]["LinkList"][47]["Name"], "pubmed_pubmed")
        self.assertEqual(record["DbInfo"]["LinkList"][47]["Menu"], "Related Citations")
        self.assertEqual(
            record["DbInfo"]["LinkList"][47]["Description"],
            "Calculated set of PubMed citations closely related to the selected article(s) retrieved using a word weight algorithm. Related articles are displayed in ranked order from most to least relevant, with the \u201clinked from\u201d citation displayed first.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][47]["DbTo"], "pubmed")
        self.assertEqual(
            record["DbInfo"]["LinkList"][48]["Name"], "pubmed_pubmed_bookrecords"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][48]["Menu"],
            "References for this Bookshelf citation",
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][48]["Description"],
            "PubMed abstracts for articles cited in this record",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][48]["DbTo"], "pubmed")
        self.assertEqual(record["DbInfo"]["LinkList"][49]["Name"], "pubmed_pubmed_refs")
        self.assertEqual(
            record["DbInfo"]["LinkList"][49]["Menu"], "References for PMC Articles"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][49]["Description"],
            "Citation referenced in PubMed article. Only valid for PubMed citations that are also in PMC.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][49]["DbTo"], "pubmed")
        self.assertEqual(record["DbInfo"]["LinkList"][50]["Name"], "pubmed_snp")
        self.assertEqual(record["DbInfo"]["LinkList"][50]["Menu"], "SNP Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][50]["Description"],
            "Nucleotide polymorphism records from dbSNP that have current articles as submitter-provided references.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][50]["DbTo"], "snp")
        self.assertEqual(record["DbInfo"]["LinkList"][51]["Name"], "pubmed_snp_cited")
        self.assertEqual(record["DbInfo"]["LinkList"][51]["Menu"], "SNP (Cited)")
        self.assertEqual(
            record["DbInfo"]["LinkList"][51]["Description"],
            "Nucleotide polymorphism records from dbSNP that have NCBI dbSNP identifiers reported in the PubMed abstract of the current articles.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][51]["DbTo"], "snp")
        self.assertEqual(record["DbInfo"]["LinkList"][52]["Name"], "pubmed_sra")
        self.assertEqual(record["DbInfo"]["LinkList"][52]["Menu"], "SRA Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][52]["Description"],
            "Massively-parallel sequencing project data in the Short Read Archive (SRA) that are reported in the current articles.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][52]["DbTo"], "sra")
        self.assertEqual(record["DbInfo"]["LinkList"][53]["Name"], "pubmed_structure")
        self.assertEqual(record["DbInfo"]["LinkList"][53]["Menu"], "Structure Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][53]["Description"],
            "Three-dimensional structure records in the NCBI Structure database for data reported in the current articles.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][53]["DbTo"], "structure")
        self.assertEqual(
            record["DbInfo"]["LinkList"][54]["Name"], "pubmed_taxonomy_entrez"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][54]["Menu"], "Taxonomy via GenBank"
        )
        self.assertEqual(
            record["DbInfo"]["LinkList"][54]["Description"],
            "Taxonomy records associated with the current articles through taxonomic information on related molecular database records (Nucleotide, Protein, Gene, SNP, Structure).",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][54]["DbTo"], "taxonomy")
        self.assertEqual(record["DbInfo"]["LinkList"][55]["Name"], "pubmed_unigene")
        self.assertEqual(record["DbInfo"]["LinkList"][55]["Menu"], "UniGene Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][55]["Description"],
            "UniGene clusters of expressed sequences that are associated with the current articles through references on the clustered sequence records and related Gene records.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][55]["DbTo"], "unigene")
        self.assertEqual(record["DbInfo"]["LinkList"][56]["Name"], "pubmed_unists")
        self.assertEqual(record["DbInfo"]["LinkList"][56]["Menu"], "UniSTS Links")
        self.assertEqual(
            record["DbInfo"]["LinkList"][56]["Description"],
            "Genetic, physical, and sequence mapping reagents in the UniSTS database associated with the current articles through references on sequence tagged site (STS) submissions as well as automated searching of PubMed abstracts and full-text PubMed Central articles for marker names.",
        )
        self.assertEqual(record["DbInfo"]["LinkList"][56]["DbTo"], "unists")

    def test_corrupted(self):
        """Test if corrupted XML is handled correctly."""
        # To create the XML file, use
        # >>> Bio.Entrez.einfo()
        # and manually delete the last couple of lines
        from Bio.Entrez import Parser

        with open("Entrez/einfo4.xml", "rb") as stream:
            self.assertRaises(Parser.CorruptedXMLError, Entrez.read, stream)


class ESearchTest(unittest.TestCase):
    """Tests for parsing XML output returned by ESearch."""

    def test_pubmed1(self):
        """Test parsing XML returned by ESearch from PubMed (first test)."""
        # To create the XML file, use
        # >>> Bio.Entrez.esearch(db="pubmed", term="biopython")
        with open("Entrez/esearch1.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record["Count"], "5")
        self.assertEqual(record["RetMax"], "5")
        self.assertEqual(record["RetStart"], "0")
        self.assertEqual(len(record["IdList"]), 5)
        self.assertEqual(record["IdList"][0], "16403221")
        self.assertEqual(record["IdList"][1], "16377612")
        self.assertEqual(record["IdList"][2], "14871861")
        self.assertEqual(record["IdList"][3], "14630660")
        self.assertEqual(record["IdList"][4], "12230038")
        self.assertEqual(len(record["TranslationSet"]), 0)
        self.assertEqual(len(record["TranslationStack"]), 2)
        self.assertEqual(record["TranslationStack"][0]["Term"], "biopython[All Fields]")
        self.assertEqual(record["TranslationStack"][0]["Field"], "All Fields")
        self.assertEqual(record["TranslationStack"][0]["Count"], "5")
        self.assertEqual(record["TranslationStack"][0]["Explode"], "Y")
        self.assertEqual(record["TranslationStack"][0].tag, "TermSet")
        self.assertEqual(record["TranslationStack"][1], "GROUP")
        self.assertEqual(record["TranslationStack"][1].tag, "OP")
        self.assertEqual(record["QueryTranslation"], "biopython[All Fields]")

    def test_pubmed2(self):
        """Test parsing XML returned by ESearch from PubMed (second test)."""
        # Search in PubMed for the term cancer for the entrez date from
        # the last 60 days and retrieve the first 100 IDs and translations
        # using the history parameter.
        # To create the XML file, use
        # >>> Bio.Entrez.esearch(db="pubmed", term="cancer", reldate=60,
        #                        datetype="edat", retmax=100, usehistory="y")
        with open("Entrez/esearch2.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record["Count"], "10238")
        self.assertEqual(record["RetMax"], "100")
        self.assertEqual(record["RetStart"], "0")
        self.assertEqual(record["QueryKey"], "12")
        self.assertEqual(
            record["WebEnv"],
            "0rYFb69LfbTFXfG7-0HPo2BU-ZFWF1s_51WtYR5e0fAzThQCR0WIW12inPQRRIj1xUzSfGgG9ovT9-@263F6CC86FF8F760_0173SID",
        )
        self.assertEqual(len(record["IdList"]), 100)
        self.assertEqual(record["IdList"][0], "18411453")
        self.assertEqual(record["IdList"][1], "18411431")
        self.assertEqual(record["IdList"][2], "18411430")
        self.assertEqual(record["IdList"][3], "18411429")
        self.assertEqual(record["IdList"][4], "18411428")
        self.assertEqual(record["IdList"][5], "18411402")
        self.assertEqual(record["IdList"][6], "18411381")
        self.assertEqual(record["IdList"][7], "18411373")
        self.assertEqual(record["IdList"][8], "18411372")
        self.assertEqual(record["IdList"][9], "18411371")
        self.assertEqual(record["IdList"][10], "18411370")
        self.assertEqual(record["IdList"][11], "18411367")
        self.assertEqual(record["IdList"][12], "18411306")
        self.assertEqual(record["IdList"][13], "18411292")
        self.assertEqual(record["IdList"][14], "18411277")
        self.assertEqual(record["IdList"][15], "18411260")
        self.assertEqual(record["IdList"][16], "18411234")
        self.assertEqual(record["IdList"][17], "18411200")
        self.assertEqual(record["IdList"][18], "18411199")
        self.assertEqual(record["IdList"][19], "18411198")
        self.assertEqual(record["IdList"][20], "18411197")
        self.assertEqual(record["IdList"][21], "18411195")
        self.assertEqual(record["IdList"][22], "18411194")
        self.assertEqual(record["IdList"][23], "18411193")
        self.assertEqual(record["IdList"][24], "18411192")
        self.assertEqual(record["IdList"][25], "18411191")
        self.assertEqual(record["IdList"][26], "18411052")
        self.assertEqual(record["IdList"][27], "18411048")
        self.assertEqual(record["IdList"][28], "18411046")
        self.assertEqual(record["IdList"][29], "18411019")
        self.assertEqual(record["IdList"][30], "18411018")
        self.assertEqual(record["IdList"][31], "18411017")
        self.assertEqual(record["IdList"][32], "18411015")
        self.assertEqual(record["IdList"][33], "18411014")
        self.assertEqual(record["IdList"][34], "18411011")
        self.assertEqual(record["IdList"][35], "18411010")
        self.assertEqual(record["IdList"][36], "18411005")
        self.assertEqual(record["IdList"][37], "18411003")
        self.assertEqual(record["IdList"][38], "18411001")
        self.assertEqual(record["IdList"][39], "18411000")
        self.assertEqual(record["IdList"][40], "18410999")
        self.assertEqual(record["IdList"][41], "18410998")
        self.assertEqual(record["IdList"][42], "18410997")
        self.assertEqual(record["IdList"][43], "18410995")
        self.assertEqual(record["IdList"][44], "18410977")
        self.assertEqual(record["IdList"][45], "18410975")
        self.assertEqual(record["IdList"][46], "18410966")
        self.assertEqual(record["IdList"][47], "18410954")
        self.assertEqual(record["IdList"][48], "18410953")
        self.assertEqual(record["IdList"][49], "18410934")
        self.assertEqual(record["IdList"][50], "18410925")
        self.assertEqual(record["IdList"][51], "18410903")
        self.assertEqual(record["IdList"][52], "18410826")
        self.assertEqual(record["IdList"][53], "18410739")
        self.assertEqual(record["IdList"][54], "18410720")
        self.assertEqual(record["IdList"][55], "18410716")
        self.assertEqual(record["IdList"][56], "18410709")
        self.assertEqual(record["IdList"][57], "18410705")
        self.assertEqual(record["IdList"][58], "18410692")
        self.assertEqual(record["IdList"][59], "18410690")
        self.assertEqual(record["IdList"][60], "18410634")
        self.assertEqual(record["IdList"][61], "18410618")
        self.assertEqual(record["IdList"][62], "18410610")
        self.assertEqual(record["IdList"][63], "18410593")
        self.assertEqual(record["IdList"][64], "18410587")
        self.assertEqual(record["IdList"][65], "18410567")
        self.assertEqual(record["IdList"][66], "18410539")
        self.assertEqual(record["IdList"][67], "18410530")
        self.assertEqual(record["IdList"][68], "18410528")
        self.assertEqual(record["IdList"][69], "18410461")
        self.assertEqual(record["IdList"][70], "18410455")
        self.assertEqual(record["IdList"][71], "18410444")
        self.assertEqual(record["IdList"][72], "18410443")
        self.assertEqual(record["IdList"][73], "18410442")
        self.assertEqual(record["IdList"][74], "18410441")
        self.assertEqual(record["IdList"][75], "18410440")
        self.assertEqual(record["IdList"][76], "18410439")
        self.assertEqual(record["IdList"][77], "18410437")
        self.assertEqual(record["IdList"][78], "18410436")
        self.assertEqual(record["IdList"][79], "18410435")
        self.assertEqual(record["IdList"][80], "18410431")
        self.assertEqual(record["IdList"][81], "18410430")
        self.assertEqual(record["IdList"][82], "18410428")
        self.assertEqual(record["IdList"][83], "18410427")
        self.assertEqual(record["IdList"][84], "18410405")
        self.assertEqual(record["IdList"][85], "18410404")
        self.assertEqual(record["IdList"][86], "18410355")
        self.assertEqual(record["IdList"][87], "18410327")
        self.assertEqual(record["IdList"][88], "18410312")
        self.assertEqual(record["IdList"][89], "18410311")
        self.assertEqual(record["IdList"][90], "18410307")
        self.assertEqual(record["IdList"][91], "18410259")
        self.assertEqual(record["IdList"][92], "18410249")
        self.assertEqual(record["IdList"][93], "18410245")
        self.assertEqual(record["IdList"][94], "18410243")
        self.assertEqual(record["IdList"][95], "18410242")
        self.assertEqual(record["IdList"][96], "18410060")
        self.assertEqual(record["IdList"][97], "18410013")
        self.assertEqual(record["IdList"][98], "18409992")
        self.assertEqual(record["IdList"][99], "18409991")
        self.assertEqual(len(record["TranslationSet"]), 1)
        self.assertEqual(record["TranslationSet"][0]["From"], "cancer")
        self.assertEqual(
            record["TranslationSet"][0]["To"],
            '(("neoplasms"[TIAB] NOT Medline[SB]) OR "neoplasms"[MeSH Terms] OR cancer[Text Word])',
        )
        self.assertEqual(len(record["TranslationStack"]), 13)
        self.assertEqual(record["TranslationStack"][0]["Term"], '"neoplasms"[TIAB]')
        self.assertEqual(record["TranslationStack"][0]["Field"], "TIAB")
        self.assertEqual(record["TranslationStack"][0]["Count"], "52104")
        self.assertEqual(record["TranslationStack"][0]["Explode"], "Y")
        self.assertEqual(record["TranslationStack"][0].tag, "TermSet")
        self.assertEqual(record["TranslationStack"][1]["Term"], "Medline[SB]")
        self.assertEqual(record["TranslationStack"][1]["Field"], "SB")
        self.assertEqual(record["TranslationStack"][1]["Count"], "16509514")
        self.assertEqual(record["TranslationStack"][1]["Explode"], "Y")
        self.assertEqual(record["TranslationStack"][1].tag, "TermSet")
        self.assertEqual(record["TranslationStack"][2], "NOT")
        self.assertEqual(record["TranslationStack"][2].tag, "OP")
        self.assertEqual(record["TranslationStack"][3], "GROUP")
        self.assertEqual(record["TranslationStack"][3].tag, "OP")
        self.assertEqual(
            record["TranslationStack"][4]["Term"], '"neoplasms"[MeSH Terms]'
        )
        self.assertEqual(record["TranslationStack"][4]["Field"], "MeSH Terms")
        self.assertEqual(record["TranslationStack"][4]["Count"], "1918010")
        self.assertEqual(record["TranslationStack"][4]["Explode"], "Y")
        self.assertEqual(record["TranslationStack"][4].tag, "TermSet")
        self.assertEqual(record["TranslationStack"][5], "OR")
        self.assertEqual(record["TranslationStack"][5].tag, "OP")
        self.assertEqual(record["TranslationStack"][6]["Term"], "cancer[Text Word]")
        self.assertEqual(record["TranslationStack"][6]["Field"], "Text Word")
        self.assertEqual(record["TranslationStack"][6]["Count"], "638849")
        self.assertEqual(record["TranslationStack"][6]["Explode"], "Y")
        self.assertEqual(record["TranslationStack"][6].tag, "TermSet")
        self.assertEqual(record["TranslationStack"][7], "OR")
        self.assertEqual(record["TranslationStack"][7].tag, "OP")
        self.assertEqual(record["TranslationStack"][8], "GROUP")
        self.assertEqual(record["TranslationStack"][8].tag, "OP")
        self.assertEqual(record["TranslationStack"][9]["Term"], "2008/02/16[EDAT]")
        self.assertEqual(record["TranslationStack"][9]["Field"], "EDAT")
        self.assertEqual(record["TranslationStack"][9]["Count"], "-1")
        self.assertEqual(record["TranslationStack"][9]["Explode"], "Y")
        self.assertEqual(record["TranslationStack"][9].tag, "TermSet")
        self.assertEqual(record["TranslationStack"][10]["Term"], "2008/04/16[EDAT]")
        self.assertEqual(record["TranslationStack"][10]["Field"], "EDAT")
        self.assertEqual(record["TranslationStack"][10]["Count"], "-1")
        self.assertEqual(record["TranslationStack"][10]["Explode"], "Y")
        self.assertEqual(record["TranslationStack"][10].tag, "TermSet")
        self.assertEqual(record["TranslationStack"][11], "RANGE")
        self.assertEqual(record["TranslationStack"][11].tag, "OP")
        self.assertEqual(record["TranslationStack"][12], "AND")
        self.assertEqual(record["TranslationStack"][12].tag, "OP")
        self.assertEqual(
            record["QueryTranslation"],
            '(("neoplasms"[TIAB] NOT Medline[SB]) OR "neoplasms"[MeSH Terms] OR cancer[Text Word]) AND 2008/02/16[EDAT] : 2008/04/16[EDAT]',
        )

    def test_pubmed3(self):
        """Test parsing XML returned by ESearch from PubMed (third test)."""
        # Search in PubMed for the journal PNAS Volume 97, and retrieve
        # 6 IDs starting at ID 7.
        # To create the XML file, use
        # >>> Bio.Entrez.esearch(db="pubmed", term="PNAS[ta] AND 97[vi]",
        #                        retstart=6, retmax=6)
        with open("Entrez/esearch3.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record["Count"], "2652")
        self.assertEqual(record["RetMax"], "6")
        self.assertEqual(record["RetStart"], "6")
        self.assertEqual(len(record["IdList"]), 6)
        self.assertEqual(record["IdList"][0], "11121077")
        self.assertEqual(record["IdList"][1], "11121076")
        self.assertEqual(record["IdList"][2], "11121075")
        self.assertEqual(record["IdList"][3], "11121074")
        self.assertEqual(record["IdList"][4], "11121073")
        self.assertEqual(record["IdList"][5], "11121072")
        self.assertEqual(len(record["TranslationSet"]), 1)
        self.assertEqual(record["TranslationSet"][0]["From"], "PNAS[ta]")
        self.assertEqual(
            record["TranslationSet"][0]["To"],
            '"Proc Natl Acad Sci U S A"[Journal:__jrid6653]',
        )
        self.assertEqual(len(record["TranslationStack"]), 3)
        self.assertEqual(
            record["TranslationStack"][0]["Term"], '"Proc Natl Acad Sci U S A"[Journal]'
        )
        self.assertEqual(record["TranslationStack"][0]["Field"], "Journal")
        self.assertEqual(record["TranslationStack"][0]["Count"], "91806")
        self.assertEqual(record["TranslationStack"][0]["Explode"], "Y")
        self.assertEqual(record["TranslationStack"][0].tag, "TermSet")
        self.assertEqual(record["TranslationStack"][1]["Term"], "97[vi]")
        self.assertEqual(record["TranslationStack"][1]["Field"], "vi")
        self.assertEqual(record["TranslationStack"][1]["Count"], "58681")
        self.assertEqual(record["TranslationStack"][1]["Explode"], "Y")
        self.assertEqual(record["TranslationStack"][1].tag, "TermSet")
        self.assertEqual(record["TranslationStack"][2], "AND")
        self.assertEqual(record["TranslationStack"][2].tag, "OP")
        self.assertEqual(
            record["QueryTranslation"], '"Proc Natl Acad Sci U S A"[Journal] AND 97[vi]'
        )

    def test_journals(self):
        """Test parsing XML returned by ESearch from the Journals database."""
        # Search in Journals for the term obstetrics.
        # To create the XML file, use
        # >>> Bio.Entrez.esearch(db="journals", term="obstetrics")
        with open("Entrez/esearch4.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record["Count"], "177")
        self.assertEqual(record["RetMax"], "20")
        self.assertEqual(record["RetStart"], "0")
        self.assertEqual(len(record["IdList"]), 20)
        self.assertEqual(record["IdList"][0], "75")
        self.assertEqual(record["IdList"][1], "138")
        self.assertEqual(record["IdList"][2], "136")
        self.assertEqual(record["IdList"][3], "137")
        self.assertEqual(record["IdList"][4], "139")
        self.assertEqual(record["IdList"][5], "140")
        self.assertEqual(record["IdList"][6], "355")
        self.assertEqual(record["IdList"][7], "354")
        self.assertEqual(record["IdList"][8], "27731")
        self.assertEqual(record["IdList"][9], "439")
        self.assertEqual(record["IdList"][10], "564")
        self.assertEqual(record["IdList"][11], "617")
        self.assertEqual(record["IdList"][12], "749")
        self.assertEqual(record["IdList"][13], "735")
        self.assertEqual(record["IdList"][14], "815")
        self.assertEqual(record["IdList"][15], "905")
        self.assertEqual(record["IdList"][16], "903")
        self.assertEqual(record["IdList"][17], "932")
        self.assertEqual(record["IdList"][18], "933")
        self.assertEqual(record["IdList"][19], "875")
        self.assertEqual(len(record["TranslationSet"]), 0)
        self.assertEqual(len(record["TranslationStack"]), 2)
        self.assertEqual(
            record["TranslationStack"][0]["Term"], "obstetrics[All Fields]"
        )
        self.assertEqual(record["TranslationStack"][0]["Field"], "All Fields")
        self.assertEqual(record["TranslationStack"][0]["Count"], "177")
        self.assertEqual(record["TranslationStack"][0]["Explode"], "Y")
        self.assertEqual(record["TranslationStack"][0].tag, "TermSet")
        self.assertEqual(record["TranslationStack"][1], "GROUP")
        self.assertEqual(record["TranslationStack"][1].tag, "OP")
        self.assertEqual(record["QueryTranslation"], "obstetrics[All Fields]")

    def test_pmc(self):
        """Test parsing XML returned by ESearch from PubMed Central."""
        # Search in PubMed Central for stem cells in free fulltext articles.
        # To create the XML file, use
        # >>> Bio.Entrez.esearch(db="pmc",
        #                        term="stem cells AND free fulltext[filter]")
        with open("Entrez/esearch5.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record["Count"], "23492")
        self.assertEqual(record["RetMax"], "20")
        self.assertEqual(record["RetStart"], "0")
        self.assertEqual(len(record["IdList"]), 20)
        self.assertEqual(record["IdList"][0], "1894783")
        self.assertEqual(record["IdList"][1], "2064507")
        self.assertEqual(record["IdList"][2], "520747")
        self.assertEqual(record["IdList"][3], "2043120")
        self.assertEqual(record["IdList"][4], "2118723")
        self.assertEqual(record["IdList"][5], "1815228")
        self.assertEqual(record["IdList"][6], "1253596")
        self.assertEqual(record["IdList"][7], "2077853")
        self.assertEqual(record["IdList"][8], "1308908")
        self.assertEqual(record["IdList"][9], "2233634")
        self.assertEqual(record["IdList"][10], "556262")
        self.assertEqual(record["IdList"][11], "1925137")
        self.assertEqual(record["IdList"][12], "1860068")
        self.assertEqual(record["IdList"][13], "1626529")
        self.assertEqual(record["IdList"][14], "2217616")
        self.assertEqual(record["IdList"][15], "1584276")
        self.assertEqual(record["IdList"][16], "2000702")
        self.assertEqual(record["IdList"][17], "186324")
        self.assertEqual(record["IdList"][18], "1959362")
        self.assertEqual(record["IdList"][19], "1413911")
        self.assertEqual(len(record["TranslationSet"]), 1)
        self.assertEqual(record["TranslationSet"][0]["From"], "stem cells")
        self.assertEqual(
            record["TranslationSet"][0]["To"],
            '("stem cells"[MeSH Terms] OR stem cells[Acknowledgments] OR stem cells[Figure/Table Caption] OR stem cells[Section Title] OR stem cells[Body - All Words] OR stem cells[Title] OR stem cells[Abstract])',
        )
        self.assertEqual(len(record["TranslationStack"]), 16)
        self.assertEqual(
            record["TranslationStack"][0]["Term"], '"stem cells"[MeSH Terms]'
        )
        self.assertEqual(record["TranslationStack"][0]["Field"], "MeSH Terms")
        self.assertEqual(record["TranslationStack"][0]["Count"], "12224")
        self.assertEqual(record["TranslationStack"][0]["Explode"], "Y")
        self.assertEqual(record["TranslationStack"][0].tag, "TermSet")
        self.assertEqual(
            record["TranslationStack"][1]["Term"], "stem cells[Acknowledgments]"
        )
        self.assertEqual(record["TranslationStack"][1]["Field"], "Acknowledgments")
        self.assertEqual(record["TranslationStack"][1]["Count"], "79")
        self.assertEqual(record["TranslationStack"][1]["Explode"], "Y")
        self.assertEqual(record["TranslationStack"][1].tag, "TermSet")
        self.assertEqual(record["TranslationStack"][2], "OR")
        self.assertEqual(record["TranslationStack"][2].tag, "OP")
        self.assertEqual(
            record["TranslationStack"][3]["Term"], "stem cells[Figure/Table Caption]"
        )
        self.assertEqual(record["TranslationStack"][3]["Field"], "Figure/Table Caption")
        self.assertEqual(record["TranslationStack"][3]["Count"], "806")
        self.assertEqual(record["TranslationStack"][3]["Explode"], "Y")
        self.assertEqual(record["TranslationStack"][3].tag, "TermSet")
        self.assertEqual(record["TranslationStack"][4], "OR")
        self.assertEqual(record["TranslationStack"][4].tag, "OP")
        self.assertEqual(
            record["TranslationStack"][5]["Term"], "stem cells[Section Title]"
        )
        self.assertEqual(record["TranslationStack"][5]["Field"], "Section Title")
        self.assertEqual(record["TranslationStack"][5]["Count"], "522")
        self.assertEqual(record["TranslationStack"][5]["Explode"], "Y")
        self.assertEqual(record["TranslationStack"][5].tag, "TermSet")
        self.assertEqual(record["TranslationStack"][6], "OR")
        self.assertEqual(record["TranslationStack"][6].tag, "OP")
        self.assertEqual(
            record["TranslationStack"][7]["Term"], "stem cells[Body - All Words]"
        )
        self.assertEqual(record["TranslationStack"][7]["Field"], "Body - All Words")
        self.assertEqual(record["TranslationStack"][7]["Count"], "13936")
        self.assertEqual(record["TranslationStack"][7]["Explode"], "Y")
        self.assertEqual(record["TranslationStack"][7].tag, "TermSet")
        self.assertEqual(record["TranslationStack"][8], "OR")
        self.assertEqual(record["TranslationStack"][8].tag, "OP")
        self.assertEqual(record["TranslationStack"][9]["Term"], "stem cells[Title]")
        self.assertEqual(record["TranslationStack"][9]["Field"], "Title")
        self.assertEqual(record["TranslationStack"][9]["Count"], "1005")
        self.assertEqual(record["TranslationStack"][9]["Explode"], "Y")
        self.assertEqual(record["TranslationStack"][9].tag, "TermSet")
        self.assertEqual(record["TranslationStack"][10], "OR")
        self.assertEqual(record["TranslationStack"][10].tag, "OP")
        self.assertEqual(record["TranslationStack"][11]["Term"], "stem cells[Abstract]")
        self.assertEqual(record["TranslationStack"][11]["Field"], "Abstract")
        self.assertEqual(record["TranslationStack"][11]["Count"], "2503")
        self.assertEqual(record["TranslationStack"][11]["Explode"], "Y")
        self.assertEqual(record["TranslationStack"][11].tag, "TermSet")
        self.assertEqual(record["TranslationStack"][12], "OR")
        self.assertEqual(record["TranslationStack"][12].tag, "OP")
        self.assertEqual(record["TranslationStack"][13], "GROUP")
        self.assertEqual(record["TranslationStack"][13].tag, "OP")
        self.assertEqual(
            record["TranslationStack"][14]["Term"], "free fulltext[filter]"
        )
        self.assertEqual(record["TranslationStack"][14]["Field"], "filter")
        self.assertEqual(record["TranslationStack"][14]["Count"], "1412839")
        self.assertEqual(record["TranslationStack"][14]["Explode"], "Y")
        self.assertEqual(record["TranslationStack"][14].tag, "TermSet")
        self.assertEqual(record["TranslationStack"][15], "AND")
        self.assertEqual(record["TranslationStack"][15].tag, "OP")
        self.assertEqual(
            record["QueryTranslation"],
            '("stem cells"[MeSH Terms] OR stem cells[Acknowledgments] OR stem cells[Figure/Table Caption] OR stem cells[Section Title] OR stem cells[Body - All Words] OR stem cells[Title] OR stem cells[Abstract]) AND free fulltext[filter]',
        )

    def test_nucleotide(self):
        """Test parsing XML returned by ESearch from the Nucleotide database."""
        # Search in Nucleotide for a property of the sequence,
        # To create the XML file, use
        # >>> Bio.Entrez.esearch(db="nucleotide", term="biomol trna[prop]")
        with open("Entrez/esearch6.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record["Count"], "699")
        self.assertEqual(record["RetMax"], "20")
        self.assertEqual(record["RetStart"], "0")
        self.assertEqual(len(record["IdList"]), 20)
        self.assertEqual(record["IdList"][0], "220161")
        self.assertEqual(record["IdList"][1], "220160")
        self.assertEqual(record["IdList"][2], "220159")
        self.assertEqual(record["IdList"][3], "220263")
        self.assertEqual(record["IdList"][4], "220162")
        self.assertEqual(record["IdList"][5], "159885659")
        self.assertEqual(record["IdList"][6], "156572228")
        self.assertEqual(record["IdList"][7], "2648075")
        self.assertEqual(record["IdList"][8], "287595")
        self.assertEqual(record["IdList"][9], "402544")
        self.assertEqual(record["IdList"][10], "402506")
        self.assertEqual(record["IdList"][11], "402505")
        self.assertEqual(record["IdList"][12], "287594")
        self.assertEqual(record["IdList"][13], "287593")
        self.assertEqual(record["IdList"][14], "287592")
        self.assertEqual(record["IdList"][15], "287591")
        self.assertEqual(record["IdList"][16], "287590")
        self.assertEqual(record["IdList"][17], "287589")
        self.assertEqual(record["IdList"][18], "287588")
        self.assertEqual(record["IdList"][19], "287587")
        self.assertEqual(len(record["TranslationSet"]), 0)
        self.assertEqual(record["QueryTranslation"], "")

    def test_protein(self):
        """Test parsing XML returned by ESearch from the Protein database."""
        # Search in Protein for a molecular weight
        # To create the XML file, use
        # >>> Bio.Entrez.esearch(db="protein", term="200020[molecular weight]")
        with open("Entrez/esearch7.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record["Count"], "3")
        self.assertEqual(record["RetMax"], "3")
        self.assertEqual(record["RetStart"], "0")
        self.assertEqual(len(record["IdList"]), 3)
        self.assertEqual(record["IdList"][0], "16766766")
        self.assertEqual(record["IdList"][1], "16422035")
        self.assertEqual(record["IdList"][2], "4104812")
        self.assertEqual(len(record["TranslationSet"]), 0)
        self.assertEqual(len(record["TranslationStack"]), 2)
        self.assertEqual(
            record["TranslationStack"][0]["Term"], "000200020[molecular weight]"
        )
        self.assertEqual(record["TranslationStack"][0]["Field"], "molecular weight")
        self.assertEqual(record["TranslationStack"][0]["Count"], "3")
        self.assertEqual(record["TranslationStack"][0]["Explode"], "Y")
        self.assertEqual(record["TranslationStack"][0].tag, "TermSet")
        self.assertEqual(record["TranslationStack"][1], "GROUP")
        self.assertEqual(record["TranslationStack"][1].tag, "OP")
        self.assertEqual(record["QueryTranslation"], "000200020[molecular weight]")

    def test_notfound(self):
        """Test parsing XML returned by ESearch when no items were found."""
        # To create the XML file, use
        # >>> Bio.Entrez.esearch(db="protein", term="abcXYZ")
        with open("Entrez/esearch8.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record["Count"], "0")
        self.assertEqual(record["RetMax"], "0")
        self.assertEqual(record["RetStart"], "0")
        self.assertEqual(len(record["IdList"]), 0)
        self.assertEqual(len(record["TranslationSet"]), 0)
        self.assertEqual(record["QueryTranslation"], "")
        self.assertEqual(len(record["ErrorList"]), 2)
        self.assertIn("PhraseNotFound", record["ErrorList"])
        self.assertIn("FieldNotFound", record["ErrorList"])
        self.assertEqual(len(record["ErrorList"]["PhraseNotFound"]), 1)
        self.assertEqual(len(record["ErrorList"]["FieldNotFound"]), 0)
        self.assertEqual(record["ErrorList"]["PhraseNotFound"][0], "abcXYZ")
        self.assertEqual(len(record["WarningList"]), 3)
        self.assertIn("PhraseIgnored", record["WarningList"])
        self.assertIn("QuotedPhraseNotFound", record["WarningList"])
        self.assertIn("OutputMessage", record["WarningList"])
        self.assertEqual(len(record["WarningList"]["PhraseIgnored"]), 0)
        self.assertEqual(len(record["WarningList"]["QuotedPhraseNotFound"]), 0)
        self.assertEqual(len(record["WarningList"]["OutputMessage"]), 1)
        self.assertEqual(record["WarningList"]["OutputMessage"][0], "No items found.")


class EPostTest(unittest.TestCase):
    """Tests for parsing XML output returned by EPost."""

    # Don't know how to get an InvalidIdList in the XML returned by EPost;
    # unable to test if we are parsing it correctly.
    def test_epost(self):
        """Test parsing XML returned by EPost."""
        # To create the XML file, use
        # >>> Bio.Entrez.epost(db="pubmed", id="11237011")
        with open("Entrez/epost1.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record["QueryKey"], "1")
        self.assertEqual(
            record["WebEnv"],
            "0zYsuLk3zG_lRMkblPBEqnT8nIENUGw4HAy8xXChTnoVm7GEnWY71jv3nz@1FC077F3806DE010_0042SID",
        )

    def test_wrong(self):
        """Test parsing XML returned by EPost with incorrect arguments."""
        # To create the XML file, use
        # >>> Bio.Entrez.epost(db="nothing")
        with open("Entrez/epost2.xml", "rb") as stream:
            self.assertRaises(RuntimeError, Entrez.read, stream)
        with open("Entrez/epost2.xml", "rb") as stream:
            record = Entrez.read(stream, ignore_errors=True)
        self.assertEqual(len(record), 1)
        self.assertEqual(len(record.attributes), 0)
        self.assertEqual(record["ERROR"], "Wrong DB name")
        self.assertEqual(record["ERROR"].tag, "ERROR")

    def test_invalid(self):
        """Test parsing XML returned by EPost with invalid id (overflow tag)."""
        # To create the XML file, use
        # >>> Bio.Entrez.epost(db="pubmed", id=99999999999999999999999999999999)
        with open("Entrez/epost3.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record["InvalidIdList"], ["-1"])
        self.assertEqual(record["QueryKey"], "1")
        self.assertEqual(
            record["WebEnv"],
            "08AIUeBsfIk6BfdzKnd3GM2RtCudczC9jm5aeb4US0o7azCTQCeCsr-xg0@1EDE54E680D03C40_0011SID",
        )


class ESummaryTest(unittest.TestCase):
    """Tests for parsing XML output returned by ESummary."""

    # Items have a type, which can be
    # (Integer|Date|String|Structure|List|Flags|Qualifier|Enumerator|Unknown)
    # I don't have an XML file where the type "Flags", "Qualifier",
    # "Enumerator", or "Unknown" is used, so they are not tested here.
    def test_pubmed(self):
        """Test parsing XML returned by ESummary from PubMed."""
        # In PubMed display records for PMIDs 11850928 and 11482001 in
        # xml retrieval mode
        # To create the XML file, use
        # >>> Bio.Entrez.esummary(db="pubmed", id=["11850928","11482001"],
        #                         retmode="xml")
        with open("Entrez/esummary1.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record[0]["Id"], "11850928")
        self.assertEqual(record[0]["PubDate"], "1965 Aug")
        self.assertEqual(record[0]["EPubDate"], "")
        self.assertEqual(record[0]["Source"], "Arch Dermatol")
        self.assertEqual(len(record[0]["AuthorList"]), 2)
        self.assertEqual(record[0]["AuthorList"][0], "LoPresti PJ")
        self.assertEqual(record[0]["AuthorList"][1], "Hambrick GW Jr")
        self.assertEqual(record[0]["LastAuthor"], "Hambrick GW Jr")
        self.assertEqual(
            record[0]["Title"],
            "Zirconium granuloma following treatment of rhus dermatitis.",
        )
        self.assertEqual(record[0]["Volume"], "92")
        self.assertEqual(record[0]["Issue"], "2")
        self.assertEqual(record[0]["Pages"], "188-91")
        self.assertEqual(record[0]["LangList"], ["English"])
        self.assertEqual(record[0]["NlmUniqueID"], "0372433")
        self.assertEqual(record[0]["ISSN"], "0003-987X")
        self.assertEqual(record[0]["ESSN"], "1538-3652")
        self.assertEqual(len(record[0]["PubTypeList"]), 1)
        self.assertEqual(record[0]["PubTypeList"][0], "Journal Article")
        self.assertEqual(record[0]["RecordStatus"], "PubMed - indexed for MEDLINE")
        self.assertEqual(record[0]["PubStatus"], "ppublish")
        self.assertEqual(len(record[0]["ArticleIds"]), 2)
        self.assertEqual(record[0]["ArticleIds"]["pubmed"], ["11850928"])
        self.assertEqual(record[0]["ArticleIds"]["medline"], [])
        self.assertEqual(len(record[0]["History"]), 2)
        self.assertEqual(record[0]["History"]["pubmed"], ["1965/08/01 00:00"])
        self.assertEqual(record[0]["History"]["medline"], ["2002/03/09 10:01"])
        self.assertEqual(len(record[0]["References"]), 0)
        self.assertEqual(record[0]["HasAbstract"], 1)
        self.assertEqual(record[0]["PmcRefCount"], 0)
        self.assertEqual(record[0]["FullJournalName"], "Archives of dermatology")
        self.assertEqual(record[0]["ELocationID"], "")
        self.assertEqual(record[0]["SO"], "1965 Aug;92(2):188-91")

        self.assertEqual(record[1]["Id"], "11482001")
        self.assertEqual(record[1]["PubDate"], "2001 Jun")
        self.assertEqual(record[1]["EPubDate"], "")
        self.assertEqual(record[1]["Source"], "Adverse Drug React Toxicol Rev")
        self.assertEqual(len(record[1]["AuthorList"]), 3)
        self.assertEqual(record[1]["AuthorList"][0], "Mantle D")
        self.assertEqual(record[1]["AuthorList"][1], "Gok MA")
        self.assertEqual(record[1]["AuthorList"][2], "Lennard TW")
        self.assertEqual(record[1]["LastAuthor"], "Lennard TW")
        self.assertEqual(
            record[1]["Title"],
            "Adverse and beneficial effects of plant extracts on skin and skin disorders.",
        )
        self.assertEqual(record[1]["Volume"], "20")
        self.assertEqual(record[1]["Issue"], "2")
        self.assertEqual(record[1]["Pages"], "89-103")
        self.assertEqual(len(record[1]["LangList"]), 1)
        self.assertEqual(record[1]["LangList"][0], "English")
        self.assertEqual(record[1]["NlmUniqueID"], "9109474")
        self.assertEqual(record[1]["ISSN"], "0964-198X")
        self.assertEqual(record[1]["ESSN"], "")
        self.assertEqual(len(record[1]["PubTypeList"]), 2)
        self.assertEqual(record[1]["PubTypeList"][0], "Journal Article")
        self.assertEqual(record[1]["PubTypeList"][1], "Review")
        self.assertEqual(record[1]["RecordStatus"], "PubMed - indexed for MEDLINE")
        self.assertEqual(record[1]["PubStatus"], "ppublish")
        self.assertEqual(len(record[1]["ArticleIds"]), 2)
        self.assertEqual(record[1]["ArticleIds"]["pubmed"], ["11482001"])
        self.assertEqual(record[1]["ArticleIds"]["medline"], [])
        self.assertEqual(len(record[1]["History"]), 2)
        self.assertEqual(record[1]["History"]["pubmed"], ["2001/08/03 10:00"])
        self.assertEqual(record[1]["History"]["medline"], ["2002/01/23 10:01"])
        self.assertEqual(len(record[1]["References"]), 0)
        self.assertEqual(record[1]["HasAbstract"], 1)
        self.assertEqual(record[1]["PmcRefCount"], 0)
        self.assertEqual(
            record[1]["FullJournalName"],
            "Adverse drug reactions and toxicological reviews",
        )
        self.assertEqual(record[1]["ELocationID"], "")
        self.assertEqual(record[1]["SO"], "2001 Jun;20(2):89-103")

    def test_journals(self):
        """Test parsing XML returned by ESummary from the Journals database."""
        # In Journals display records for journal IDs 27731,439,735,905
        # To create the XML file, use
        # >>> Bio.Entrez.esummary(db="journals", id="27731,439,735,905")
        with open("Entrez/esummary2.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record[0]["Id"], "27731")
        self.assertEqual(
            record[0]["Title"],
            "The American journal of obstetrics and diseases of women and children",
        )
        self.assertEqual(record[0]["MedAbbr"], "Am J Obstet Dis Women Child")
        self.assertEqual(record[0]["IsoAbbr"], "")
        self.assertEqual(record[0]["NlmId"], "14820330R")
        self.assertEqual(record[0]["pISSN"], "0894-5543")
        self.assertEqual(record[0]["eISSN"], "")
        self.assertEqual(record[0]["PublicationStartYear"], "1868")
        self.assertEqual(record[0]["PublicationEndYear"], "1919")
        self.assertEqual(
            record[0]["Publisher"], "W.A. Townsend & Adams, $c [1868-1919]"
        )
        self.assertEqual(record[0]["Language"], "eng")
        self.assertEqual(record[0]["Country"], "United States")
        self.assertEqual(len(record[0]["BroadHeading"]), 0)
        self.assertEqual(record[0]["ContinuationNotes"], "")

        self.assertEqual(record[1]["Id"], "439")
        self.assertEqual(
            record[1]["Title"], "American journal of obstetrics and gynecology"
        )
        self.assertEqual(record[1]["MedAbbr"], "Am J Obstet Gynecol")
        self.assertEqual(record[1]["IsoAbbr"], "Am. J. Obstet. Gynecol.")
        self.assertEqual(record[1]["NlmId"], "0370476")
        self.assertEqual(record[1]["pISSN"], "0002-9378")
        self.assertEqual(record[1]["eISSN"], "1097-6868")
        self.assertEqual(record[1]["PublicationStartYear"], "1920")
        self.assertEqual(record[1]["PublicationEndYear"], "")
        self.assertEqual(record[1]["Publisher"], "Elsevier,")
        self.assertEqual(record[1]["Language"], "eng")
        self.assertEqual(record[1]["Country"], "United States")
        self.assertEqual(len(record[1]["BroadHeading"]), 2)
        self.assertEqual(record[1]["BroadHeading"][0], "Gynecology")
        self.assertEqual(record[1]["BroadHeading"][1], "Obstetrics")
        self.assertEqual(
            record[1]["ContinuationNotes"],
            "Continues: American journal of obstetrics and diseases of women and children. ",
        )

        self.assertEqual(record[2]["Id"], "735")
        self.assertEqual(record[2]["Title"], "Archives of gynecology and obstetrics")
        self.assertEqual(record[2]["MedAbbr"], "Arch Gynecol Obstet")
        self.assertEqual(record[2]["IsoAbbr"], "Arch. Gynecol. Obstet.")
        self.assertEqual(record[2]["NlmId"], "8710213")
        self.assertEqual(record[2]["pISSN"], "0932-0067")
        self.assertEqual(record[2]["eISSN"], "1432-0711")
        self.assertEqual(record[2]["PublicationStartYear"], "1987")
        self.assertEqual(record[2]["PublicationEndYear"], "")
        self.assertEqual(record[2]["Publisher"], "Springer Verlag")
        self.assertEqual(record[2]["Language"], "eng")
        self.assertEqual(record[2]["Country"], "Germany")
        self.assertEqual(len(record[2]["BroadHeading"]), 2)
        self.assertEqual(record[2]["BroadHeading"][0], "Gynecology")
        self.assertEqual(record[2]["BroadHeading"][1], "Obstetrics")
        self.assertEqual(
            record[2]["ContinuationNotes"], "Continues: Archives of gynecology. "
        )

        self.assertEqual(record[3]["Id"], "905")
        self.assertEqual(
            record[3]["Title"],
            "Asia-Oceania journal of obstetrics and gynaecology / AOFOG",
        )
        self.assertEqual(record[3]["MedAbbr"], "Asia Oceania J Obstet Gynaecol")
        self.assertEqual(record[3]["IsoAbbr"], "")
        self.assertEqual(record[3]["NlmId"], "8102781")
        self.assertEqual(record[3]["pISSN"], "0389-2328")
        self.assertEqual(record[3]["eISSN"], "")
        self.assertEqual(record[3]["PublicationStartYear"], "1980")
        self.assertEqual(record[3]["PublicationEndYear"], "1994")
        self.assertEqual(record[3]["Publisher"], "University Of Tokyo Press")
        self.assertEqual(record[3]["Language"], "eng")
        self.assertEqual(record[3]["Country"], "Japan")
        self.assertEqual(len(record[3]["BroadHeading"]), 2)
        self.assertEqual(record[3]["BroadHeading"][0], "Gynecology")
        self.assertEqual(record[3]["BroadHeading"][1], "Obstetrics")
        self.assertEqual(
            record[3]["ContinuationNotes"],
            "Continues: Journal of the Asian Federation of Obstetrics and Gynaecology. Continued by: Journal of obstetrics and gynaecology (Tokyo, Japan). ",
        )

    def test_protein(self):
        """Test parsing XML returned by ESummary from the Protein database."""
        # In Protein display records for GIs 28800982 and 28628843 in xml retrieval mode
        # To create the XML file, use
        # >>> Bio.Entrez.esummary(db="protein", id="28800982,28628843", retmode="xml")
        with open("Entrez/esummary3.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record[0]["Id"], "28800982")
        self.assertEqual(record[0]["Caption"], "AAO47091")
        self.assertEqual(record[0]["Title"], "hemochromatosis [Homo sapiens]")
        self.assertEqual(record[0]["Extra"], "gi|28800982|gb|AAO47091.1|[28800982]")
        self.assertEqual(record[0]["Gi"], 28800982)
        self.assertEqual(record[0]["CreateDate"], "2003/03/03")
        self.assertEqual(record[0]["UpdateDate"], "2003/03/03")
        self.assertEqual(record[0]["Flags"], 0)
        self.assertEqual(record[0]["TaxId"], 9606)
        self.assertEqual(record[0]["Length"], 268)
        self.assertEqual(record[0]["Status"], "live")
        self.assertEqual(record[0]["ReplacedBy"], "")
        self.assertEqual(record[0]["Comment"], "  ")

        self.assertEqual(record[1]["Id"], "28628843")
        self.assertEqual(record[1]["Caption"], "AAO49381")
        self.assertEqual(
            record[1]["Title"], "erythroid associated factor [Homo sapiens]"
        )
        self.assertEqual(
            record[1]["Extra"], "gi|28628843|gb|AAO49381.1|AF485325_1[28628843]"
        )
        self.assertEqual(record[1]["Gi"], 28628843)
        self.assertEqual(record[1]["CreateDate"], "2003/03/02")
        self.assertEqual(record[1]["UpdateDate"], "2003/03/02")
        self.assertEqual(record[1]["Flags"], 0)
        self.assertEqual(record[1]["TaxId"], 9606)
        self.assertEqual(record[1]["Length"], 102)
        self.assertEqual(record[1]["Status"], "live")
        self.assertEqual(record[1]["ReplacedBy"], "")
        self.assertEqual(record[1]["Comment"], "  ")

    def test_nucleotide(self):
        """Test parsing XML returned by ESummary from the Nucleotide database."""
        # In Nucleotide display records for GIs 28864546 and 28800981
        # in xml retrieval mode
        # To create the XML file, use
        # >>> Bio.Entrez.esummary(db="nucleotide", id="28864546,28800981",
        #                         retmode="xml")
        with open("Entrez/esummary4.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record[0]["Id"], "28864546")
        self.assertEqual(record[0]["Caption"], "AY207443")
        self.assertEqual(
            record[0]["Title"],
            "Homo sapiens alpha hemoglobin (HBZP) pseudogene 3' UTR/AluJo repeat breakpoint junction",
        )
        self.assertEqual(record[0]["Extra"], "gi|28864546|gb|AY207443.1|[28864546]")
        self.assertEqual(record[0]["Gi"], 28864546)
        self.assertEqual(record[0]["CreateDate"], "2003/03/05")
        self.assertEqual(record[0]["UpdateDate"], "2003/03/05")
        self.assertEqual(record[0]["Flags"], 0)
        self.assertEqual(record[0]["TaxId"], 9606)
        self.assertEqual(record[0]["Length"], 491)
        self.assertEqual(record[0]["Status"], "live")
        self.assertEqual(record[0]["ReplacedBy"], "")
        self.assertEqual(record[0]["Comment"], "  ")

        self.assertEqual(record[1]["Id"], "28800981")
        self.assertEqual(record[1]["Caption"], "AY205604")
        self.assertEqual(
            record[1]["Title"], "Homo sapiens hemochromatosis (HFE) mRNA, partial cds"
        )
        self.assertEqual(record[1]["Extra"], "gi|28800981|gb|AY205604.1|[28800981]")
        self.assertEqual(record[1]["Gi"], 28800981)
        self.assertEqual(record[1]["CreateDate"], "2003/03/03")
        self.assertEqual(record[1]["UpdateDate"], "2003/03/03")
        self.assertEqual(record[1]["Flags"], 0)
        self.assertEqual(record[1]["TaxId"], 9606)
        self.assertEqual(record[1]["Length"], 860)
        self.assertEqual(record[1]["Status"], "live")
        self.assertEqual(record[1]["ReplacedBy"], "")
        self.assertEqual(record[1]["Comment"], "  ")

    def test_structure(self):
        """Test parsing XML returned by ESummary from the Structure database."""
        # In Nucleotide display records for GIs 28864546 and 28800981
        # in xml retrieval mode
        # To create the XML file, use
        # >>> Bio.Entrez.esummary(db="structure", id=["19923","12120"],
        #                         retmode="xml")
        with open("Entrez/esummary5.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record[0]["Id"], "19923")
        self.assertEqual(record[0]["PdbAcc"], "1L5J")
        self.assertEqual(
            record[0]["PdbDescr"], "Crystal Structure Of E. Coli Aconitase B"
        )
        self.assertEqual(record[0]["EC"], "4.2.1.3")
        self.assertEqual(record[0]["Resolution"], "2.4")
        self.assertEqual(record[0]["ExpMethod"], "X-Ray Diffraction")
        self.assertEqual(record[0]["PdbClass"], "Lyase")
        self.assertEqual(record[0]["PdbReleaseDate"], "2007/8/27")
        self.assertEqual(record[0]["PdbDepositDate"], "2002/3/7")
        self.assertEqual(record[0]["DepositDate"], "2007/10/25")
        self.assertEqual(record[0]["ModifyDate"], "2007/10/25")
        self.assertEqual(record[0]["LigCode"], "F3S|TRA")
        self.assertEqual(record[0]["LigCount"], "2")
        self.assertEqual(record[0]["ModProteinResCount"], "0")
        self.assertEqual(record[0]["ModDNAResCount"], "0")
        self.assertEqual(record[0]["ModRNAResCount"], "0")
        self.assertEqual(record[0]["ProteinChainCount"], "2")
        self.assertEqual(record[0]["DNAChainCount"], "0")
        self.assertEqual(record[0]["RNAChainCount"], "0")

        self.assertEqual(record[1]["Id"], "12120")
        self.assertEqual(record[1]["PdbAcc"], "1B0K")
        self.assertEqual(
            record[1]["PdbDescr"], "S642a:fluorocitrate Complex Of Aconitase"
        )
        self.assertEqual(record[1]["EC"], "4.2.1.3")
        self.assertEqual(record[1]["Resolution"], "2.5")
        self.assertEqual(record[1]["ExpMethod"], "X-Ray Diffraction")
        self.assertEqual(record[1]["PdbClass"], "Lyase")
        self.assertEqual(record[1]["PdbReleaseDate"], "2007/8/27")
        self.assertEqual(record[1]["PdbDepositDate"], "1998/11/11")
        self.assertEqual(record[1]["DepositDate"], "2007/10/07")
        self.assertEqual(record[1]["ModifyDate"], "2007/10/07")
        self.assertEqual(record[1]["LigCode"], "FLC|O|SF4")
        self.assertEqual(record[1]["LigCount"], "3")
        self.assertEqual(record[1]["ModProteinResCount"], "0")
        self.assertEqual(record[1]["ModDNAResCount"], "0")
        self.assertEqual(record[1]["ModRNAResCount"], "0")
        self.assertEqual(record[1]["ProteinChainCount"], "1")
        self.assertEqual(record[1]["DNAChainCount"], "0")
        self.assertEqual(record[1]["RNAChainCount"], "0")

    def test_taxonomy(self):
        """Test parsing XML returned by ESummary from the Taxonomy database."""
        # In Taxonomy display records for TAXIDs 9913 and 30521 in
        # xml retrieval mode
        # To create the XML file, use
        # >>> Bio.Entrez.esummary(db="taxonomy", id=["9913","30521"],
        #                         retmode="xml")
        with open("Entrez/esummary6.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record[0]["Id"], "9913")
        self.assertEqual(record[0]["Rank"], "species")
        self.assertEqual(record[0]["Division"], "even-toed ungulates")
        self.assertEqual(record[0]["ScientificName"], "Bos taurus")
        self.assertEqual(record[0]["CommonName"], "cattle")
        self.assertEqual(record[0]["TaxId"], 9913)
        self.assertEqual(record[0]["NucNumber"], 2264214)
        self.assertEqual(record[0]["ProtNumber"], 55850)
        self.assertEqual(record[0]["StructNumber"], 1517)
        self.assertEqual(record[0]["GenNumber"], 31)
        self.assertEqual(record[0]["GeneNumber"], 29651)
        self.assertEqual(record[0]["Genus"], "")
        self.assertEqual(record[0]["Species"], "")
        self.assertEqual(record[0]["Subsp"], "")

        self.assertEqual(record[1]["Id"], "30521")
        self.assertEqual(record[1]["Rank"], "species")
        self.assertEqual(record[1]["Division"], "even-toed ungulates")
        self.assertEqual(record[1]["ScientificName"], "Bos grunniens")
        self.assertEqual(record[1]["CommonName"], "domestic yak")
        self.assertEqual(record[1]["TaxId"], 30521)
        self.assertEqual(record[1]["NucNumber"], 560)
        self.assertEqual(record[1]["ProtNumber"], 254)
        self.assertEqual(record[1]["StructNumber"], 0)
        self.assertEqual(record[1]["GenNumber"], 1)
        self.assertEqual(record[1]["GeneNumber"], 13)
        self.assertEqual(record[1]["Genus"], "")
        self.assertEqual(record[1]["Species"], "")
        self.assertEqual(record[1]["Subsp"], "")

    def test_unists(self):
        """Test parsing XML returned by ESummary from the UniSTS database."""
        # In UniSTS display records for IDs 254085 and 254086 in xml
        # retrieval mode
        # To create the XML file, use
        # >>> Bio.Entrez.esummary(db="unists", id=["254085","254086"],
        #                         retmode="xml")
        with open("Entrez/esummary7.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record[0]["Id"], "254085")
        self.assertEqual(record[0]["Marker_Name"], "SE234324")
        self.assertEqual(len(record[0]["Map_Gene_Summary_List"]), 1)
        self.assertEqual(record[0]["Map_Gene_Summary_List"][0]["Org"], "Sus scrofa")
        self.assertEqual(record[0]["Map_Gene_Summary_List"][0]["Chr"], " chromosome 7")
        self.assertEqual(record[0]["Map_Gene_Summary_List"][0]["Locus"], "")
        self.assertEqual(
            record[0]["EPCR_Summary"], "Found by e-PCR in sequences from Sus scrofa."
        )
        self.assertEqual(record[0]["LocusId"], "")

        self.assertEqual(record[1]["Id"], "254086")
        self.assertEqual(record[1]["Marker_Name"], "SE259162")
        self.assertEqual(len(record[1]["Map_Gene_Summary_List"]), 1)
        self.assertEqual(record[1]["Map_Gene_Summary_List"][0]["Org"], "Sus scrofa")
        self.assertEqual(record[1]["Map_Gene_Summary_List"][0]["Chr"], " chromosome 12")
        self.assertEqual(record[1]["Map_Gene_Summary_List"][0]["Locus"], "")
        self.assertEqual(
            record[1]["EPCR_Summary"], "Found by e-PCR in sequences from Sus scrofa."
        )
        self.assertEqual(record[1]["LocusId"], "")

    def test_wrong(self):
        """Test parsing XML returned by ESummary with incorrect arguments."""
        # To create the XML file, use
        # >>> Bio.Entrez.esummary()
        with open("Entrez/esummary8.xml", "rb") as stream:
            self.assertRaises(RuntimeError, Entrez.read, stream)
        with open("Entrez/esummary8.xml", "rb") as stream:
            record = Entrez.read(stream, ignore_errors=True)
        self.assertEqual(len(record), 1)
        self.assertEqual(len(record.attributes), 0)
        self.assertEqual(record[0], "Neither query_key nor id specified")
        self.assertEqual(record[0].tag, "ERROR")

    def test_integer_none(self):
        """Test parsing ESummary XML where an Integer is not defined."""
        # To create the XML file, use
        # >>> Entrez.esummary(db='pccompound', id='7488')
        with open("Entrez/esummary9.xml", "rb") as stream:
            records = Entrez.read(stream)
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record["Id"], "7488")
        self.assertEqual(record["CID"], 7488)
        self.assertEqual(record["SourceNameList"], [])
        self.assertEqual(record["SourceIDList"], [])
        self.assertEqual(len(record["SourceCategoryList"]), 8)
        self.assertEqual(record["SourceCategoryList"][0], "Chemical Vendors")
        self.assertEqual(record["SourceCategoryList"][1], "Research and Development")
        self.assertEqual(record["SourceCategoryList"][2], "Curation Efforts")
        self.assertEqual(record["SourceCategoryList"][3], "Governmental Organizations")
        self.assertEqual(record["SourceCategoryList"][4], "Legacy Depositors")
        self.assertEqual(record["SourceCategoryList"][5], "Subscription Services")
        self.assertEqual(record["SourceCategoryList"][6], "Journal Publishers")
        self.assertEqual(record["SourceCategoryList"][7], "NIH Initiatives")
        self.assertEqual(record["CreateDate"], "2005/03/26 00:00")
        self.assertEqual(len(record["SynonymList"]), 77)
        self.assertEqual(record["SynonymList"][0], "Terephthaloyl chloride")
        self.assertEqual(record["SynonymList"][1], "100-20-9")
        self.assertEqual(record["SynonymList"][2], "Terephthaloyl dichloride")
        self.assertEqual(record["SynonymList"][3], "1,4-BENZENEDICARBONYL DICHLORIDE")
        self.assertEqual(record["SynonymList"][4], "Terephthalic acid dichloride")
        self.assertEqual(record["SynonymList"][5], "Terephthalic dichloride")
        self.assertEqual(record["SynonymList"][6], "p-Phthaloyl chloride")
        self.assertEqual(record["SynonymList"][7], "Terephthalic acid chloride")
        self.assertEqual(record["SynonymList"][8], "p-Phthalyl dichloride")
        self.assertEqual(record["SynonymList"][9], "p-Phthaloyl dichloride")
        self.assertEqual(record["SynonymList"][10], "Terephthalyl dichloride")
        self.assertEqual(record["SynonymList"][11], "1,4-Benzenedicarbonyl chloride")
        self.assertEqual(record["SynonymList"][12], "p-Phenylenedicarbonyl dichloride")
        self.assertEqual(record["SynonymList"][13], "benzene-1,4-dicarbonyl chloride")
        self.assertEqual(record["SynonymList"][14], "NSC 41885")
        self.assertEqual(record["SynonymList"][15], "terephthaloylchloride")
        self.assertEqual(record["SynonymList"][16], "UNII-G247CO9608")
        self.assertEqual(record["SynonymList"][17], "HSDB 5332")
        self.assertEqual(record["SynonymList"][18], "EINECS 202-829-5")
        self.assertEqual(record["SynonymList"][19], "BRN 0607796")
        self.assertEqual(record["SynonymList"][20], "LXEJRKJRKIFVNY-UHFFFAOYSA-N")
        self.assertEqual(record["SynonymList"][21], "MFCD00000693")
        self.assertEqual(record["SynonymList"][22], "G247CO9608")
        self.assertEqual(record["SynonymList"][23], "DSSTox_CID_6653")
        self.assertEqual(record["SynonymList"][24], "DSSTox_RID_78175")
        self.assertEqual(record["SynonymList"][25], "DSSTox_GSID_26653")
        self.assertEqual(record["SynonymList"][26], "Q-201791")
        self.assertEqual(record["SynonymList"][27], "Terephthaloyl chloride, 99+%")
        self.assertEqual(record["SynonymList"][28], "CAS-100-20-9")
        self.assertEqual(record["SynonymList"][29], "CCRIS 8626")
        self.assertEqual(record["SynonymList"][30], "p-Phthalyl chloride")
        self.assertEqual(record["SynonymList"][31], "terephthalic chloride")
        self.assertEqual(record["SynonymList"][32], "tere-phthaloyl chloride")
        self.assertEqual(record["SynonymList"][33], "AC1L1OVG")
        self.assertEqual(record["SynonymList"][34], "ACMC-2097nf")
        self.assertEqual(record["SynonymList"][35], "EC 202-829-5")
        self.assertEqual(record["SynonymList"][36], "1,4-Dichloroformyl benzene")
        self.assertEqual(record["SynonymList"][37], "SCHEMBL68148")
        self.assertEqual(
            record["SynonymList"][38], "4-09-00-03318 (Beilstein Handbook Reference)"
        )
        self.assertEqual(record["SynonymList"][39], "KSC174E9T")
        self.assertEqual(record["SynonymList"][40], "CHEMBL1893301")
        self.assertEqual(record["SynonymList"][41], "DTXSID7026653")
        self.assertEqual(record["SynonymList"][42], "KS-00000VAD")
        self.assertEqual(record["SynonymList"][43], "benzene-1,4-dicarbonyl dichloride")
        self.assertEqual(record["SynonymList"][44], "MolPort-003-926-079")
        self.assertEqual(record["SynonymList"][45], "BCP27385")
        self.assertEqual(record["SynonymList"][46], "NSC41885")
        self.assertEqual(record["SynonymList"][47], "Tox21_201899")
        self.assertEqual(record["SynonymList"][48], "Tox21_303166")
        self.assertEqual(record["SynonymList"][49], "ANW-14185")
        self.assertEqual(record["SynonymList"][50], "NSC-41885")
        self.assertEqual(record["SynonymList"][51], "ZINC38141445")
        self.assertEqual(record["SynonymList"][52], "AKOS015890038")
        self.assertEqual(record["SynonymList"][53], "FCH1319904")
        self.assertEqual(record["SynonymList"][54], "MCULE-9481285116")
        self.assertEqual(record["SynonymList"][55], "RP25985")
        self.assertEqual(
            record["SynonymList"][56], "Terephthaloyl chloride, >=99%, flakes"
        )
        self.assertEqual(record["SynonymList"][57], "NCGC00164045-01")
        self.assertEqual(record["SynonymList"][58], "NCGC00164045-02")
        self.assertEqual(record["SynonymList"][59], "NCGC00257127-01")
        self.assertEqual(record["SynonymList"][60], "NCGC00259448-01")
        self.assertEqual(record["SynonymList"][61], "AN-24545")
        self.assertEqual(record["SynonymList"][62], "I764")
        self.assertEqual(record["SynonymList"][63], "KB-10499")
        self.assertEqual(record["SynonymList"][64], "OR315758")
        self.assertEqual(record["SynonymList"][65], "SC-19185")
        self.assertEqual(record["SynonymList"][66], "LS-148753")
        self.assertEqual(record["SynonymList"][67], "RT-000669")
        self.assertEqual(record["SynonymList"][68], "ST51037908")
        self.assertEqual(record["SynonymList"][69], "6804-EP1441224A2")
        self.assertEqual(record["SynonymList"][70], "I01-5090")
        self.assertEqual(
            record["SynonymList"][71],
            "InChI=1/C8H4Cl2O2/c9-7(11)5-1-2-6(4-3-5)8(10)12/h1-4",
        )
        self.assertEqual(record["SynonymList"][72], "106158-15-0")
        self.assertEqual(record["SynonymList"][73], "108454-76-8")
        self.assertEqual(record["SynonymList"][74], "1640987-72-9")
        self.assertEqual(record["SynonymList"][75], "188665-55-6")
        self.assertEqual(record["SynonymList"][76], "1927884-58-9")
        self.assertEqual(len(record["MeSHHeadingList"]), 1)
        self.assertEqual(record["MeSHHeadingList"][0], "terephthaloyl chloride")
        self.assertEqual(len(record["MeSHTermList"]), 5)
        self.assertEqual(record["MeSHTermList"][0], "p-phthaloyl dichloride")
        self.assertEqual(record["MeSHTermList"][1], "terephthaloyl dichloride")
        self.assertEqual(record["MeSHTermList"][2], "1,4-benzenedicarbonyl dichloride")
        self.assertEqual(record["MeSHTermList"][3], "1,4-phthaloyl dichloride")
        self.assertEqual(record["MeSHTermList"][4], "terephthaloyl chloride")
        self.assertEqual(len(record["PharmActionList"]), 0)
        self.assertEqual(record["CommentList"], [])
        self.assertEqual(record["IUPACName"], "benzene-1,4-dicarbonyl chloride")
        self.assertEqual(record["CanonicalSmiles"], "C1=CC(=CC=C1C(=O)Cl)C(=O)Cl")
        self.assertEqual(record["IsomericSmiles"], "C1=CC(=CC=C1C(=O)Cl)C(=O)Cl")
        self.assertEqual(record["RotatableBondCount"], 2)
        self.assertEqual(record["MolecularFormula"], "C8H4Cl2O2")
        self.assertEqual(record["MolecularWeight"], "203.018")
        self.assertEqual(record["TotalFormalCharge"], 0)
        self.assertEqual(record["XLogP"], "4")
        self.assertEqual(record["HydrogenBondDonorCount"], 0)
        self.assertEqual(record["HydrogenBondAcceptorCount"], 2)
        self.assertEqual(record["Complexity"], "173.000")
        self.assertEqual(record["HeavyAtomCount"], 12)
        self.assertEqual(record["AtomChiralCount"], 0)
        self.assertEqual(record["AtomChiralDefCount"], 0)
        self.assertEqual(record["AtomChiralUndefCount"], 0)
        self.assertEqual(record["BondChiralCount"], 0)
        self.assertEqual(record["BondChiralDefCount"], 0)
        self.assertEqual(record["BondChiralUndefCount"], 0)
        self.assertEqual(record["IsotopeAtomCount"], 0)
        self.assertEqual(record["CovalentUnitCount"], 1)
        self.assertEqual(record["TautomerCount"], None)  # noqa: A502
        self.assertEqual(record["SubstanceIDList"], [])
        self.assertEqual(record["TPSA"], "34.1")
        self.assertEqual(record["AssaySourceNameList"], [])
        self.assertEqual(record["MinAC"], "")
        self.assertEqual(record["MaxAC"], "")
        self.assertEqual(record["MinTC"], "")
        self.assertEqual(record["MaxTC"], "")
        self.assertEqual(record["ActiveAidCount"], 1)
        self.assertEqual(record["InactiveAidCount"], None)
        self.assertEqual(record["TotalAidCount"], 243)
        self.assertEqual(record["InChIKey"], "LXEJRKJRKIFVNY-UHFFFAOYSA-N")
        self.assertEqual(
            record["InChI"], "InChI=1S/C8H4Cl2O2/c9-7(11)5-1-2-6(4-3-5)8(10)12/h1-4H"
        )


class ELinkTest(unittest.TestCase):
    """Tests for parsing XML output returned by ELink."""

    def test_pubmed1(self):
        """Test parsing pubmed links returned by ELink (first test)."""
        # Retrieve IDs from PubMed for PMID 9298984 to the PubMed database
        # To create the XML file, use
        # >>> Bio.Entrez.elink(dbfrom="pubmed", id="9298984", cmd="neighbor")
        with open("Entrez/elink1.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(len(record), 1)
        self.assertEqual(len(record[0]), 5)
        self.assertEqual(record[0]["DbFrom"], "pubmed")
        self.assertEqual(record[0]["IdList"], ["9298984"])
        self.assertEqual(len(record[0]["LinkSetDb"]), 8)
        self.assertEqual(record[0]["LinkSetDb"][0]["DbTo"], "pubmed")
        self.assertEqual(record[0]["LinkSetDb"][0]["LinkName"], "pubmed_pubmed")
        self.assertEqual(len(record[0]["LinkSetDb"][0]["Link"]), 97)
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][0]["Id"], "9298984")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][1]["Id"], "8794856")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][2]["Id"], "9700164")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][3]["Id"], "7914521")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][4]["Id"], "9914369")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][5]["Id"], "1339459")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][6]["Id"], "11590237")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][7]["Id"], "12686595")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][8]["Id"], "20980244")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][9]["Id"], "11146659")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][10]["Id"], "8978614")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][11]["Id"], "9074495")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][12]["Id"], "10893249")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][13]["Id"], "2211822")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][14]["Id"], "15371539")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][15]["Id"], "10402457")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][16]["Id"], "10806105")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][17]["Id"], "10545493")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][18]["Id"], "15915585")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][19]["Id"], "10523511")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][20]["Id"], "12515822")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][21]["Id"], "9869638")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][22]["Id"], "11483958")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][23]["Id"], "11685532")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][24]["Id"], "9490715")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][25]["Id"], "1691829")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][26]["Id"], "9425896")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][27]["Id"], "12080088")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][28]["Id"], "12034769")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][29]["Id"], "9852156")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][30]["Id"], "8923204")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][31]["Id"], "7690762")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][32]["Id"], "17895365")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][33]["Id"], "9378750")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][34]["Id"], "11146661")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][35]["Id"], "18202360")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][36]["Id"], "10985388")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][37]["Id"], "11266459")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][38]["Id"], "2022189")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][39]["Id"], "8056842")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][40]["Id"], "11914278")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][41]["Id"], "15616189")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][42]["Id"], "18936247")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][43]["Id"], "17222555")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][44]["Id"], "7585942")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][45]["Id"], "9735366")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][46]["Id"], "11179694")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][47]["Id"], "21118145")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][48]["Id"], "16732327")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][49]["Id"], "14522947")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][50]["Id"], "11352945")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][51]["Id"], "16839185")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][52]["Id"], "11267866")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][53]["Id"], "10898791")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][54]["Id"], "12388768")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][55]["Id"], "16741559")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][56]["Id"], "11252055")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][57]["Id"], "7904902")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][58]["Id"], "17182852")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][59]["Id"], "9606208")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][60]["Id"], "15268859")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][61]["Id"], "18460473")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][62]["Id"], "11266451")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][63]["Id"], "10398680")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][64]["Id"], "16516834")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][65]["Id"], "12235289")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][66]["Id"], "16585270")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][67]["Id"], "1541637")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][68]["Id"], "18923084")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][69]["Id"], "16510521")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][70]["Id"], "8175879")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][71]["Id"], "11715021")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][72]["Id"], "8548823")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][73]["Id"], "15485811")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][74]["Id"], "11092768")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][75]["Id"], "7790358")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][76]["Id"], "11102811")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][77]["Id"], "15824131")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][78]["Id"], "16802858")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][79]["Id"], "17333235")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][80]["Id"], "9258677")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][81]["Id"], "17525528")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][82]["Id"], "9396743")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][83]["Id"], "12514103")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][84]["Id"], "16219694")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][85]["Id"], "10428958")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][86]["Id"], "14699129")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][87]["Id"], "2211824")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][88]["Id"], "11369198")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][89]["Id"], "15075237")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][90]["Id"], "14972679")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][91]["Id"], "7730407")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][92]["Id"], "9009204")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][93]["Id"], "11402064")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][94]["Id"], "22685323")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][95]["Id"], "24038651")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][96]["Id"], "23746972")
        self.assertEqual(record[0]["LinkSetDb"][1]["Link"][0]["Id"], "9298984")
        self.assertEqual(record[0]["LinkSetDb"][2]["Link"][0]["Id"], "20439434")
        self.assertEqual(record[0]["LinkSetDb"][2]["Link"][1]["Id"], "19273145")
        self.assertEqual(record[0]["LinkSetDb"][2]["Link"][2]["Id"], "19177000")
        self.assertEqual(record[0]["LinkSetDb"][2]["Link"][3]["Id"], "18936247")
        self.assertEqual(record[0]["LinkSetDb"][2]["Link"][4]["Id"], "18268100")
        self.assertEqual(record[0]["LinkSetDb"][2]["Link"][5]["Id"], "17699596")
        self.assertEqual(record[0]["LinkSetDb"][2]["Link"][6]["Id"], "16563186")
        self.assertEqual(record[0]["LinkSetDb"][2]["Link"][7]["Id"], "16505164")
        self.assertEqual(record[0]["LinkSetDb"][2]["Link"][8]["Id"], "16107559")
        self.assertEqual(record[0]["LinkSetDb"][2]["Link"][9]["Id"], "15824131")
        self.assertEqual(record[0]["LinkSetDb"][2]["Link"][10]["Id"], "15029241")
        self.assertEqual(record[0]["LinkSetDb"][2]["Link"][11]["Id"], "12686595")
        self.assertEqual(record[0]["LinkSetDb"][2]["Link"][12]["Id"], "11756470")
        self.assertEqual(record[0]["LinkSetDb"][2]["Link"][13]["Id"], "11553716")
        self.assertEqual(record[0]["LinkSetDb"][2]["Link"][14]["Id"], "11500386")
        self.assertEqual(record[0]["LinkSetDb"][2]["Link"][15]["Id"], "11402076")
        self.assertEqual(record[0]["LinkSetDb"][2]["Link"][16]["Id"], "11331754")
        self.assertEqual(record[0]["LinkSetDb"][2]["Link"][17]["Id"], "10545493")
        self.assertEqual(record[0]["LinkSetDb"][2]["Link"][18]["Id"], "10402457")
        self.assertEqual(record[0]["LinkSetDb"][2]["Link"][19]["Id"], "10402425")
        self.assertEqual(record[0]["LinkSetDb"][2]["Link"][20]["Id"], "9914368")
        self.assertEqual(record[0]["LinkSetDb"][2]["Link"][21]["Id"], "9763420")
        self.assertEqual(record[0]["LinkSetDb"][2]["Link"][22]["Id"], "9700166")
        self.assertEqual(record[0]["LinkSetDb"][2]["Link"][23]["Id"], "9700164")
        self.assertEqual(record[0]["LinkSetDb"][3]["Link"][0]["Id"], "9298984")
        self.assertEqual(record[0]["LinkSetDb"][3]["Link"][1]["Id"], "8794856")
        self.assertEqual(record[0]["LinkSetDb"][3]["Link"][2]["Id"], "9700164")
        self.assertEqual(record[0]["LinkSetDb"][3]["Link"][3]["Id"], "7914521")
        self.assertEqual(record[0]["LinkSetDb"][3]["Link"][4]["Id"], "9914369")
        self.assertEqual(record[0]["LinkSetDb"][3]["Link"][5]["Id"], "1339459")
        self.assertEqual(record[0]["LinkSetDb"][4]["Link"][0]["Id"], "9298984")
        self.assertEqual(record[0]["LinkSetDb"][4]["Link"][1]["Id"], "8794856")
        self.assertEqual(record[0]["LinkSetDb"][4]["Link"][2]["Id"], "9700164")
        self.assertEqual(record[0]["LinkSetDb"][4]["Link"][3]["Id"], "7914521")
        self.assertEqual(record[0]["LinkSetDb"][4]["Link"][4]["Id"], "9914369")
        self.assertEqual(record[0]["LinkSetDb"][4]["Link"][5]["Id"], "1339459")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][0]["Id"], "14732139")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][1]["Id"], "8909532")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][2]["Id"], "8898221")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][3]["Id"], "8824189")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][4]["Id"], "8824188")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][5]["Id"], "8794856")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][6]["Id"], "8763498")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][7]["Id"], "8706132")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][8]["Id"], "8706131")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][9]["Id"], "8647893")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][10]["Id"], "8617505")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][11]["Id"], "8560259")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][12]["Id"], "8521491")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][13]["Id"], "8505381")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][14]["Id"], "8485583")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][15]["Id"], "8416984")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][16]["Id"], "8267981")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][17]["Id"], "8143084")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][18]["Id"], "8023161")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][19]["Id"], "8005447")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][20]["Id"], "7914521")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][21]["Id"], "7906398")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][22]["Id"], "7860624")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][23]["Id"], "7854443")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][24]["Id"], "7854422")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][25]["Id"], "7846151")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][26]["Id"], "7821090")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][27]["Id"], "7758115")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][28]["Id"], "7739381")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][29]["Id"], "7704412")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][30]["Id"], "7698647")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][31]["Id"], "7664339")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][32]["Id"], "7642709")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][33]["Id"], "7642708")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][34]["Id"], "7579695")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][35]["Id"], "7542657")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][36]["Id"], "7502067")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][37]["Id"], "7172865")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][38]["Id"], "6966403")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][39]["Id"], "6793236")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][40]["Id"], "6684600")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][41]["Id"], "3928429")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][42]["Id"], "3670292")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][43]["Id"], "2686123")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][44]["Id"], "2683077")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][45]["Id"], "2512302")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][46]["Id"], "2498337")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][47]["Id"], "2195725")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][48]["Id"], "2185478")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][49]["Id"], "2139718")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][50]["Id"], "2139717")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][51]["Id"], "2022189")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][52]["Id"], "1999466")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][53]["Id"], "1684022")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][54]["Id"], "1406971")
        self.assertEqual(record[0]["LinkSetDb"][5]["Link"][55]["Id"], "1339459")
        self.assertEqual(record[0]["LinkSetDb"][6]["Link"][0]["Id"], "9298984")
        self.assertEqual(record[0]["LinkSetDb"][7]["Link"][0]["Id"], "9298984")

    def test_nucleotide(self):
        """Test parsing Nucleotide to Protein links returned by ELink."""
        # Retrieve IDs from Nucleotide for GI  48819, 7140345 to Protein
        # To create the XML file, use
        # >>> Bio.Entrez.elink(dbfrom="nucleotide", db="protein",
        #                      id="48819,7140345")
        with open("Entrez/elink2.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(len(record), 1)
        self.assertEqual(len(record[0]), 5)
        self.assertEqual(record[0]["DbFrom"], "nuccore")
        self.assertEqual(record[0]["IdList"], ["48819", "7140345"])
        self.assertEqual(len(record[0]["LinkSetDb"]), 2)
        self.assertEqual(len(record[0]["LinkSetDb"][0]), 3)
        self.assertEqual(record[0]["LinkSetDb"][0]["DbTo"], "protein")
        self.assertEqual(record[0]["LinkSetDb"][0]["LinkName"], "nuccore_protein")
        self.assertEqual(len(record[0]["LinkSetDb"][0]["Link"]), 1)
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][0]["Id"], "48820")
        self.assertEqual(record[0]["LinkSetDb"][1]["DbTo"], "protein")
        self.assertEqual(record[0]["LinkSetDb"][1]["LinkName"], "nuccore_protein_cds")
        self.assertEqual(len(record[0]["LinkSetDb"][1]["Link"]), 16)
        self.assertEqual(record[0]["LinkSetDb"][1]["Link"][0]["Id"], "16950486")
        self.assertEqual(record[0]["LinkSetDb"][1]["Link"][1]["Id"], "16950485")
        self.assertEqual(record[0]["LinkSetDb"][1]["Link"][2]["Id"], "15145457")
        self.assertEqual(record[0]["LinkSetDb"][1]["Link"][3]["Id"], "15145456")
        self.assertEqual(record[0]["LinkSetDb"][1]["Link"][4]["Id"], "15145455")
        self.assertEqual(record[0]["LinkSetDb"][1]["Link"][5]["Id"], "7331953")
        self.assertEqual(record[0]["LinkSetDb"][1]["Link"][6]["Id"], "7331951")
        self.assertEqual(record[0]["LinkSetDb"][1]["Link"][7]["Id"], "7331950")
        self.assertEqual(record[0]["LinkSetDb"][1]["Link"][8]["Id"], "7331949")
        self.assertEqual(record[0]["LinkSetDb"][1]["Link"][9]["Id"], "7331948")
        self.assertEqual(record[0]["LinkSetDb"][1]["Link"][10]["Id"], "7331947")
        self.assertEqual(record[0]["LinkSetDb"][1]["Link"][11]["Id"], "7331946")
        self.assertEqual(record[0]["LinkSetDb"][1]["Link"][12]["Id"], "7331945")
        self.assertEqual(record[0]["LinkSetDb"][1]["Link"][13]["Id"], "7331944")
        self.assertEqual(record[0]["LinkSetDb"][1]["Link"][14]["Id"], "7331943")
        self.assertEqual(record[0]["LinkSetDb"][1]["Link"][15]["Id"], "48820")

    def test_pubmed2(self):
        """Test parsing pubmed links returned by ELink (second test)."""
        # Retrieve PubMed related articles for PMIDs 11812492 11774222
        # with a publication date from 1995 to the present
        # To create the XML file, use
        # >>> Bio.Entrez.elink(dbfrom="pubmed", id="11812492,11774222",
        #                      db="pubmed", mindate="1995", datetype="pdat")
        with open("Entrez/elink3.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(len(record), 1)
        self.assertEqual(record[0]["DbFrom"], "pubmed")
        self.assertEqual(len(record[0]["IdList"]), 2)
        self.assertEqual(record[0]["IdList"][0], "11812492")
        self.assertEqual(record[0]["IdList"][1], "11774222")
        self.assertEqual(record[0]["LinkSetDb"][0]["DbTo"], "pubmed")
        self.assertEqual(record[0]["LinkSetDb"][0]["LinkName"], "pubmed_pubmed")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][0]["Id"], "24356117")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][1]["Id"], "24304891")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][2]["Id"], "24234437")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][3]["Id"], "24200819")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][4]["Id"], "24190075")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][5]["Id"], "24185697")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][6]["Id"], "24146634")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][7]["Id"], "24144118")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][8]["Id"], "24077701")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][9]["Id"], "24071059")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][10]["Id"], "24053607")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][11]["Id"], "24044755")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][12]["Id"], "24012123")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][13]["Id"], "23960254")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][14]["Id"], "23759724")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][15]["Id"], "23733469")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][16]["Id"], "23717556")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][17]["Id"], "23593519")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][18]["Id"], "23593012")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][19]["Id"], "23525074")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][20]["Id"], "23482460")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][21]["Id"], "23475938")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][22]["Id"], "23472225")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][23]["Id"], "23324387")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][24]["Id"], "23281896")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][25]["Id"], "23262214")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][26]["Id"], "23251587")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][27]["Id"], "23213446")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][28]["Id"], "23210448")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][29]["Id"], "23193291")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][30]["Id"], "23193260")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][31]["Id"], "23077805")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][32]["Id"], "23055615")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][33]["Id"], "23049857")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][34]["Id"], "23041355")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][35]["Id"], "23028321")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][36]["Id"], "22957693")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][37]["Id"], "22919073")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][38]["Id"], "22815933")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][39]["Id"], "22737589")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][40]["Id"], "22645363")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][41]["Id"], "22583769")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][42]["Id"], "22583543")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][43]["Id"], "22530989")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][44]["Id"], "22497736")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][45]["Id"], "22398250")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][46]["Id"], "22392278")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][47]["Id"], "22369494")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][48]["Id"], "22321609")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][49]["Id"], "22281013")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][50]["Id"], "22214329")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][51]["Id"], "22140592")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][52]["Id"], "22140107")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][53]["Id"], "22098559")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][54]["Id"], "22084196")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][55]["Id"], "22072969")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][56]["Id"], "22039151")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][57]["Id"], "22032328")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][58]["Id"], "21992066")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][59]["Id"], "21966105")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][60]["Id"], "21944995")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][61]["Id"], "21827871")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][62]["Id"], "21789233")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][63]["Id"], "21782817")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][64]["Id"], "21731626")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][65]["Id"], "23508470")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][66]["Id"], "21629728")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][67]["Id"], "21606368")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][68]["Id"], "21573076")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][69]["Id"], "21523552")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][70]["Id"], "21520341")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][71]["Id"], "21367872")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][72]["Id"], "21350051")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][73]["Id"], "21324604")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][74]["Id"], "21283610")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][75]["Id"], "21154707")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][76]["Id"], "21131495")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][77]["Id"], "21097891")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][78]["Id"], "21047535")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][79]["Id"], "21037260")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][80]["Id"], "20975904")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][81]["Id"], "20946650")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][82]["Id"], "20823861")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][83]["Id"], "20730111")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][84]["Id"], "20689574")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][85]["Id"], "20672376")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][86]["Id"], "20671203")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][87]["Id"], "20670087")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][88]["Id"], "20639550")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][89]["Id"], "20624716")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][90]["Id"], "20603211")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][91]["Id"], "20597434")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][92]["Id"], "20585501")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][93]["Id"], "20543958")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][94]["Id"], "20398331")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][95]["Id"], "20375450")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][96]["Id"], "20362581")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][97]["Id"], "20083406")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][98]["Id"], "19958475")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][99]["Id"], "20047494")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][100]["Id"], "20036185")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][101]["Id"], "20034492")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][102]["Id"], "20005876")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][103]["Id"], "19954456")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][104]["Id"], "19943957")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][105]["Id"], "19806204")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][106]["Id"], "19768586")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][107]["Id"], "19728865")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][108]["Id"], "19722191")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][109]["Id"], "19620973")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][110]["Id"], "19597542")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][111]["Id"], "19507503")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][112]["Id"], "19504759")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][113]["Id"], "19389774")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][114]["Id"], "19352421")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][115]["Id"], "19342283")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][116]["Id"], "19306393")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][117]["Id"], "19238236")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][118]["Id"], "19154594")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][119]["Id"], "19114486")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][120]["Id"], "19105187")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][121]["Id"], "19073702")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][122]["Id"], "19098027")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][123]["Id"], "19063745")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][124]["Id"], "19043737")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][125]["Id"], "19025664")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][126]["Id"], "19002498")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][127]["Id"], "18981050")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][128]["Id"], "18953038")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][129]["Id"], "18952001")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][130]["Id"], "18847484")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][131]["Id"], "18801163")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][132]["Id"], "18796476")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][133]["Id"], "18713719")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][134]["Id"], "18637161")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][135]["Id"], "18629076")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][136]["Id"], "18628874")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][137]["Id"], "18562339")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][138]["Id"], "18562031")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][139]["Id"], "18550617")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][140]["Id"], "18544553")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][141]["Id"], "18539347")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][142]["Id"], "18538871")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][143]["Id"], "18492133")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][144]["Id"], "18439691")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][145]["Id"], "18386064")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][146]["Id"], "18377816")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][147]["Id"], "18307806")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][148]["Id"], "18180957")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][149]["Id"], "18073380")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][150]["Id"], "18070518")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][151]["Id"], "18064491")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][152]["Id"], "18029361")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][153]["Id"], "18027007")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][154]["Id"], "18025705")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][155]["Id"], "18025704")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][156]["Id"], "18000556")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][157]["Id"], "17988782")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][158]["Id"], "17921498")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][159]["Id"], "17885136")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][160]["Id"], "17877839")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][161]["Id"], "17761848")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][162]["Id"], "17584494")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][163]["Id"], "17562224")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][164]["Id"], "17518759")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][165]["Id"], "17470297")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][166]["Id"], "17401150")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][167]["Id"], "17400791")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][168]["Id"], "17306254")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][169]["Id"], "17254505")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][170]["Id"], "17221864")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][171]["Id"], "17202370")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][172]["Id"], "17142236")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][173]["Id"], "17135206")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][174]["Id"], "17135198")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][175]["Id"], "17135185")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][176]["Id"], "17062145")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][177]["Id"], "17059604")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][178]["Id"], "17040125")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][179]["Id"], "17038195")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][180]["Id"], "16907992")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][181]["Id"], "16874317")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][182]["Id"], "16845079")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][183]["Id"], "16818783")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][184]["Id"], "16701248")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][185]["Id"], "16697384")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][186]["Id"], "16672453")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][187]["Id"], "16616613")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][188]["Id"], "16551372")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][189]["Id"], "16423288")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][190]["Id"], "16406333")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][191]["Id"], "22485434")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][192]["Id"], "16381974")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][193]["Id"], "16381973")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][194]["Id"], "16381840")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][195]["Id"], "16351753")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][196]["Id"], "16278157")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][197]["Id"], "16269725")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][198]["Id"], "16103603")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][199]["Id"], "16085497")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][200]["Id"], "16005284")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][201]["Id"], "16002116")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][202]["Id"], "15997407")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][203]["Id"], "15984913")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][204]["Id"], "15980532")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][205]["Id"], "15977173")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][206]["Id"], "15944077")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][207]["Id"], "15839745")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][208]["Id"], "15828434")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][209]["Id"], "15827081")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][210]["Id"], "15780005")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][211]["Id"], "15774024")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][212]["Id"], "15774022")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][213]["Id"], "15710433")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][214]["Id"], "15687015")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][215]["Id"], "15643605")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][216]["Id"], "15630619")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][217]["Id"], "22469090")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][218]["Id"], "19325849")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][219]["Id"], "15608286")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][220]["Id"], "15608284")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][221]["Id"], "15608257")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][222]["Id"], "15608233")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][223]["Id"], "15608226")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][224]["Id"], "15608212")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][225]["Id"], "15546336")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][226]["Id"], "15478601")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][227]["Id"], "15474306")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][228]["Id"], "15383308")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][229]["Id"], "15383292")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][230]["Id"], "15336912")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][231]["Id"], "15322925")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][232]["Id"], "15287587")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][233]["Id"], "15270538")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][234]["Id"], "15238684")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][235]["Id"], "15215374")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][236]["Id"], "15111095")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][237]["Id"], "15037105")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][238]["Id"], "15024419")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][239]["Id"], "14998511")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][240]["Id"], "14702162")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][241]["Id"], "14695526")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][242]["Id"], "14695451")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][243]["Id"], "14681478")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][244]["Id"], "14681474")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][245]["Id"], "14681471")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][246]["Id"], "14681353")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][247]["Id"], "14681351")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][248]["Id"], "14662922")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][249]["Id"], "12886019")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][250]["Id"], "12860672")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][251]["Id"], "12856318")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][252]["Id"], "12819149")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][253]["Id"], "12816546")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][254]["Id"], "12743802")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][255]["Id"], "12701381")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][256]["Id"], "12632152")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][257]["Id"], "12625936")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][258]["Id"], "12537121")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][259]["Id"], "12467974")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][260]["Id"], "12436197")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][261]["Id"], "12435493")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][262]["Id"], "12402526")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][263]["Id"], "12387845")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][264]["Id"], "12386340")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][265]["Id"], "12372145")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][266]["Id"], "12234534")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][267]["Id"], "12208043")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][268]["Id"], "12203989")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][269]["Id"], "12203988")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][270]["Id"], "12083398")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][271]["Id"], "11988510")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][272]["Id"], "11925998")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][273]["Id"], "11908756")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][274]["Id"], "11825250")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][275]["Id"], "11812492")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][276]["Id"], "11802378")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][277]["Id"], "11791238")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][278]["Id"], "11783003")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][279]["Id"], "11774222")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][280]["Id"], "11774221")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][281]["Id"], "11758285")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][282]["Id"], "11752345")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][283]["Id"], "11741630")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][284]["Id"], "11731507")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][285]["Id"], "11668631")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][286]["Id"], "11668619")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][287]["Id"], "11516587")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][288]["Id"], "11480780")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][289]["Id"], "11472559")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][290]["Id"], "11472553")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][291]["Id"], "11462837")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][292]["Id"], "11456466")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][293]["Id"], "11446511")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][294]["Id"], "11443570")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][295]["Id"], "11414208")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][296]["Id"], "11403387")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][297]["Id"], "11384164")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][298]["Id"], "11357826")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][299]["Id"], "11355885")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][300]["Id"], "11328780")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][301]["Id"], "11279516")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][302]["Id"], "11269648")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][303]["Id"], "11240843")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][304]["Id"], "11214099")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][305]["Id"], "11197770")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][306]["Id"], "11092731")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][307]["Id"], "11038309")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][308]["Id"], "11015564")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][309]["Id"], "10963611")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][310]["Id"], "10902212")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][311]["Id"], "10899154")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][312]["Id"], "10856373")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][313]["Id"], "10851186")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][314]["Id"], "10782070")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][315]["Id"], "10770808")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][316]["Id"], "10731564")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][317]["Id"], "10637631")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][318]["Id"], "11125122")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][319]["Id"], "11125071")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][320]["Id"], "11125059")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][321]["Id"], "10612825")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][322]["Id"], "10612824")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][323]["Id"], "10612821")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][324]["Id"], "10612820")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][325]["Id"], "10592273")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][326]["Id"], "10592272")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][327]["Id"], "10592263")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][328]["Id"], "10592200")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][329]["Id"], "10592169")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][330]["Id"], "10587943")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][331]["Id"], "10587942")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][332]["Id"], "10511685")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][333]["Id"], "10511682")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][334]["Id"], "10511680")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][335]["Id"], "10484179")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][336]["Id"], "10466136")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][337]["Id"], "10466135")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][338]["Id"], "10447503")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][339]["Id"], "10407783")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][340]["Id"], "10407677")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][341]["Id"], "10407668")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][342]["Id"], "10366827")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][343]["Id"], "10359795")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][344]["Id"], "10221636")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][345]["Id"], "10092480")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][346]["Id"], "10075567")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][347]["Id"], "10066467")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][348]["Id"], "9921679")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][349]["Id"], "9847220")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][350]["Id"], "9830540")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][351]["Id"], "9775388")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][352]["Id"], "9685316")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][353]["Id"], "9625791")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][354]["Id"], "9571806")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][355]["Id"], "9455480")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][356]["Id"], "9421619")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][357]["Id"], "9274032")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][358]["Id"], "9169870")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][359]["Id"], "9047337")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][360]["Id"], "8719164")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][361]["Id"], "7729881")

    def test_medline(self):
        """Test parsing medline indexed articles returned by ELink."""
        # Retrieve MEDLINE indexed only related articles for PMID 12242737
        # To create the XML file, use
        # >>> Bio.Entrez.elink(dbfrom="pubmed", id="12242737", db="pubmed",
        #                      term="medline[sb]")
        with open("Entrez/elink4.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(len(record), 1)
        self.assertEqual(record[0]["DbFrom"], "pubmed")
        self.assertEqual(record[0]["IdList"], ["12242737"])
        self.assertEqual(record[0]["LinkSetDb"][0]["DbTo"], "pubmed")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][0]["Id"], "23255877")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][1]["Id"], "22688104")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][2]["Id"], "22661362")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][3]["Id"], "22648258")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][4]["Id"], "22521021")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][5]["Id"], "22424988")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][6]["Id"], "22369817")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][7]["Id"], "22368911")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][8]["Id"], "22194507")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][9]["Id"], "22156652")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][10]["Id"], "22109321")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][11]["Id"], "21991829")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][12]["Id"], "21984464")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][13]["Id"], "21944608")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][14]["Id"], "21908142")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][15]["Id"], "21715237")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][16]["Id"], "21694530")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][17]["Id"], "21531047")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][18]["Id"], "21153952")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][19]["Id"], "21102533")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][20]["Id"], "20860230")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][21]["Id"], "20718377")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][22]["Id"], "20674629")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][23]["Id"], "20542260")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][24]["Id"], "20533237")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][25]["Id"], "20457774")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][26]["Id"], "20016426")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][27]["Id"], "19843737")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][28]["Id"], "19777916")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][29]["Id"], "19616724")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][30]["Id"], "19524781")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][31]["Id"], "19318006")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][32]["Id"], "19306944")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][33]["Id"], "19253206")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][34]["Id"], "19132488")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][35]["Id"], "18853843")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][36]["Id"], "18774058")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][37]["Id"], "18706783")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][38]["Id"], "18625354")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][39]["Id"], "18582671")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][40]["Id"], "18554854")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][41]["Id"], "18299362")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][42]["Id"], "18279648")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][43]["Id"], "18247070")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][44]["Id"], "18021675")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][45]["Id"], "17875143")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][46]["Id"], "17875142")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][47]["Id"], "17879696")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][48]["Id"], "17674062")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][49]["Id"], "17658095")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][50]["Id"], "17602359")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][51]["Id"], "17601500")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][52]["Id"], "17543650")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][53]["Id"], "17466477")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][54]["Id"], "17464254")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][55]["Id"], "17453494")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][56]["Id"], "17429670")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][57]["Id"], "17376366")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][58]["Id"], "17354190")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][59]["Id"], "17325998")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][60]["Id"], "17320773")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][61]["Id"], "17268692")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][62]["Id"], "17259035")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][63]["Id"], "17243036")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][64]["Id"], "17193860")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][65]["Id"], "17174054")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][66]["Id"], "17157468")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][67]["Id"], "17040637")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][68]["Id"], "16999328")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][69]["Id"], "16988291")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][70]["Id"], "16580806")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][71]["Id"], "16566645")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][72]["Id"], "16552382")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][73]["Id"], "16362812")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][74]["Id"], "16357381")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][75]["Id"], "16338316")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][76]["Id"], "16133609")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][77]["Id"], "16096604")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][78]["Id"], "15788584")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][79]["Id"], "15642291")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][80]["Id"], "15635471")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][81]["Id"], "15529836")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][82]["Id"], "15505294")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][83]["Id"], "15300544")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][84]["Id"], "15279747")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][85]["Id"], "15278705")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][86]["Id"], "15236131")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][87]["Id"], "15143223")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][88]["Id"], "15141648")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][89]["Id"], "15136027")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][90]["Id"], "15094630")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][91]["Id"], "15022983")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][92]["Id"], "15008163")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][93]["Id"], "14872380")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][94]["Id"], "14702442")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][95]["Id"], "14661668")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][96]["Id"], "14661666")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][97]["Id"], "14661663")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][98]["Id"], "14661661")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][99]["Id"], "14661306")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][100]["Id"], "14650118")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][101]["Id"], "14528718")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][102]["Id"], "12949462")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][103]["Id"], "12878072")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][104]["Id"], "12876813")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][105]["Id"], "12822521")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][106]["Id"], "12744499")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][107]["Id"], "12744498")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][108]["Id"], "12733684")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][109]["Id"], "12719915")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][110]["Id"], "12592155")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][111]["Id"], "12563154")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][112]["Id"], "12361530")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][113]["Id"], "12352163")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][114]["Id"], "12242737")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][115]["Id"], "12226761")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][116]["Id"], "12164574")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][117]["Id"], "11973504")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][118]["Id"], "11973040")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][119]["Id"], "11907356")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][120]["Id"], "11868066")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][121]["Id"], "11789473")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][122]["Id"], "11781922")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][123]["Id"], "11775722")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][124]["Id"], "11762248")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][125]["Id"], "11740602")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][126]["Id"], "11702119")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][127]["Id"], "11669077")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][128]["Id"], "11578071")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][129]["Id"], "11443295")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][130]["Id"], "11409026")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][131]["Id"], "11368937")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][132]["Id"], "11329662")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][133]["Id"], "11329658")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][134]["Id"], "11329656")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][135]["Id"], "11329655")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][136]["Id"], "11329162")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][137]["Id"], "11274884")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][138]["Id"], "11218011")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][139]["Id"], "11125632")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][140]["Id"], "11027076")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][141]["Id"], "11016058")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][142]["Id"], "10803203")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][143]["Id"], "10761553")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][144]["Id"], "10749221")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][145]["Id"], "10688065")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][146]["Id"], "10688063")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][147]["Id"], "10665303")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][148]["Id"], "10575758")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][149]["Id"], "10499712")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][150]["Id"], "10499697")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][151]["Id"], "10499696")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][152]["Id"], "10475937")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][153]["Id"], "10222521")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][154]["Id"], "10222515")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][155]["Id"], "10222514")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][156]["Id"], "10051883")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][157]["Id"], "10024396")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][158]["Id"], "9847909")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][159]["Id"], "9793138")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][160]["Id"], "9757294")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][161]["Id"], "9725288")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][162]["Id"], "9658901")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][163]["Id"], "9575723")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][164]["Id"], "9510579")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][165]["Id"], "9456947")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][166]["Id"], "9391495")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][167]["Id"], "9317094")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][168]["Id"], "9314960")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][169]["Id"], "9314959")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][170]["Id"], "9269670")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][171]["Id"], "9193407")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][172]["Id"], "9125660")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][173]["Id"], "9016217")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][174]["Id"], "8976943")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][175]["Id"], "8819381")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][176]["Id"], "8855688")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][177]["Id"], "8903064")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][178]["Id"], "8903059")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][179]["Id"], "8903058")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][180]["Id"], "8599783")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][181]["Id"], "8794574")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][182]["Id"], "7892443")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][183]["Id"], "8153333")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][184]["Id"], "8290724")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][185]["Id"], "8338105")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][186]["Id"], "1481295")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][187]["Id"], "1539132")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][188]["Id"], "2047316")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][189]["Id"], "1943587")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][190]["Id"], "2222794")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][191]["Id"], "2584497")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][192]["Id"], "3288780")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][193]["Id"], "3213296")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][194]["Id"], "4058411")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][195]["Id"], "3905087")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][196]["Id"], "6482054")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][197]["Id"], "6473764")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][198]["Id"], "6217136")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][199]["Id"], "7068417")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][200]["Id"], "7326186")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][201]["Id"], "6940010")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][202]["Id"], "7330196")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][203]["Id"], "7423836")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][204]["Id"], "7415301")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][205]["Id"], "7408592")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][206]["Id"], "531835")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][207]["Id"], "663071")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][208]["Id"], "616459")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][209]["Id"], "4818442")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][210]["Id"], "4848922")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][211]["Id"], "4808999")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][212]["Id"], "5046513")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][213]["Id"], "5512349")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][214]["Id"], "6072516")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][215]["Id"], "5594242")
        self.assertEqual(record[0]["LinkSetDb"][0]["Link"][216]["Id"], "5998281")
        self.assertEqual(record[0]["LinkSetDb"][0]["LinkName"], "pubmed_pubmed")

    def test_pubmed3(self):
        """Test parsing pubmed link returned by ELink (third test)."""
        # Create a hyperlink to the first link available for PMID 10611131
        # in PubMed
        # To create the XML file, use
        # >>> Bio.Entrez.elink(dbfrom="pubmed", id="10611131", cmd="prlinks")

        with open("Entrez/elink5.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(len(record), 1)
        self.assertEqual(len(record[0]), 5)
        self.assertEqual(record[0]["DbFrom"], "pubmed")
        self.assertEqual(len(record[0]["LinkSetDb"]), 0)
        self.assertEqual(len(record[0]["LinkSetDbHistory"]), 0)
        self.assertEqual(len(record[0]["ERROR"]), 0)
        self.assertEqual(len(record[0]["IdUrlList"]), 2)
        self.assertEqual(len(record[0]["IdUrlList"]["FirstChars"]), 0)
        self.assertEqual(len(record[0]["IdUrlList"]["IdUrlSet"]), 1)

        self.assertEqual(record[0]["IdUrlList"]["IdUrlSet"][0]["Id"], "10611131")
        self.assertEqual(len(record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"]), 1)
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][0]["Url"],
            "http://brain.oxfordjournals.org/cgi/pmidlookup?view=long&pmid=10611131",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][0]["IconUrl"],
            "//www.ncbi.nlm.nih.gov/corehtml/query/egifs/http:--highwire.stanford.edu-icons-externalservices-pubmed-custom-oxfordjournals_final_free.gif",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][0]["SubjectType"],
            ["publishers/providers"],
        )
        self.assertEqual(
            len(record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][0]["Attribute"]), 3
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][0]["Attribute"][0],
            "free resource",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][0]["Attribute"][1],
            "full-text online",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][0]["Attribute"][2],
            "publisher of information in url",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][0]["Provider"]["Name"],
            "HighWire",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][0]["Provider"]["NameAbbr"],
            "HighWire",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][0]["Provider"]["Id"], "3051"
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][0]["Provider"]["Url"],
            "http://highwire.stanford.edu",
        )

    def test_pubmed4(self):
        """Test parsing pubmed links returned by ELink (fourth test)."""
        # List all available links in PubMed, except for libraries, for
        # PMIDs 12085856 and 12085853
        # To create the XML file, use
        # >>> Bio.Entrez.elink(dbfrom="pubmed", id="12085856,12085853", cmd="llinks")
        with open("Entrez/elink6.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record[0]["DbFrom"], "pubmed")
        self.assertEqual(len(record[0]["IdUrlList"]), 2)
        self.assertEqual(record[0]["IdUrlList"]["IdUrlSet"][0]["Id"], "12085856")
        self.assertEqual(len(record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"]), 2)
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][0]["Category"], ["Medical"]
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][0]["Url"],
            "http://www.nlm.nih.gov/medlineplus/coronaryarterybypasssurgery.html",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][0]["Attribute"],
            ["free resource"],
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][0]["SubjectType"],
            ["consumer health"],
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][0]["IconUrl"],
            "//www.ncbi.nlm.nih.gov/corehtml/query/egifs/http:--www.nlm.nih.gov-medlineplus-images-linkout_sm.gif",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][0]["Provider"]["Name"],
            "MedlinePlus Health Information",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][0]["Provider"]["NameAbbr"],
            "MEDPLUS",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][0]["Provider"]["Id"], "3162"
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][0]["Provider"]["Url"],
            "http://medlineplus.gov/",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][0]["Provider"]["IconUrl"],
            "http://www.nlm.nih.gov/medlineplus/images/linkout_sm.gif",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][0]["LinkName"],
            "Coronary Artery Bypass Surgery",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][1]["Category"],
            ["Education"],
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][1]["Attribute"],
            ["free resource"],
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][1]["SubjectType"],
            ["online tutorials/courses"],
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][1]["Url"],
            "http://symptomresearch.nih.gov/chapter_1/index.htm",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][1]["Provider"]["Name"],
            "New England Research Institutes Inc.",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][1]["Provider"]["NameAbbr"],
            "NERI",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][1]["Provider"]["Id"], "3291"
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][0]["ObjUrl"][1]["Provider"]["Url"],
            "http://www.symptomresearch.com",
        )
        self.assertEqual(len(record[0]["IdUrlList"]["IdUrlSet"][1]), 2)
        self.assertEqual(record[0]["IdUrlList"]["IdUrlSet"][1]["Id"], "12085853")
        self.assertEqual(len(record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"]), 3)
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][0]["Category"], ["Medical"]
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][0]["Url"],
            "http://www.nlm.nih.gov/medlineplus/arrhythmia.html",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][0]["IconUrl"],
            "//www.ncbi.nlm.nih.gov/corehtml/query/egifs/http:--www.nlm.nih.gov-medlineplus-images-linkout_sm.gif",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][0]["Attribute"],
            ["free resource"],
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][0]["SubjectType"],
            ["consumer health"],
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][0]["LinkName"], "Arrhythmia"
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][0]["Provider"]["Name"],
            "MedlinePlus Health Information",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][0]["Provider"]["NameAbbr"],
            "MEDPLUS",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][0]["Provider"]["Id"], "3162"
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][0]["Provider"]["Url"],
            "http://medlineplus.gov/",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][1]["Category"], ["Medical"]
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][1]["Attribute"],
            ["free resource"],
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][1]["Url"],
            "http://www.nlm.nih.gov/medlineplus/exerciseandphysicalfitness.html",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][1]["IconUrl"],
            "//www.ncbi.nlm.nih.gov/corehtml/query/egifs/http:--www.nlm.nih.gov-medlineplus-images-linkout_sm.gif",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][1]["LinkName"],
            "Exercise and Physical Fitness",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][1]["SubjectType"],
            ["consumer health"],
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][1]["Provider"]["Name"],
            "MedlinePlus Health Information",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][1]["Provider"]["NameAbbr"],
            "MEDPLUS",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][1]["Provider"]["Id"], "3162"
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][1]["Provider"]["Url"],
            "http://medlineplus.gov/",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][2]["Category"], ["Medical"]
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][2]["Attribute"],
            ["free resource"],
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][2]["Url"],
            "http://www.nlm.nih.gov/medlineplus/pacemakersandimplantabledefibrillators.html",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][2]["IconUrl"],
            "//www.ncbi.nlm.nih.gov/corehtml/query/egifs/http:--www.nlm.nih.gov-medlineplus-images-linkout_sm.gif",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][2]["LinkName"],
            "Pacemakers and Implantable Defibrillators",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][2]["SubjectType"],
            ["consumer health"],
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][2]["Provider"]["Name"],
            "MedlinePlus Health Information",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][2]["Provider"]["NameAbbr"],
            "MEDPLUS",
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][2]["Provider"]["Id"], "3162"
        )
        self.assertEqual(
            record[0]["IdUrlList"]["IdUrlSet"][1]["ObjUrl"][2]["Provider"]["Url"],
            "http://medlineplus.gov/",
        )

    def test_pubmed5(self):
        """Test parsing pubmed links returned by ELink (fifth test)."""
        # List Entrez database links for PubMed PMIDs 12169658 and 11748140
        # To create the XML file, use
        # >>> Bio.Entrez.elink(dbfrom="pubmed", id="12169658,11748140",
        #                      cmd="acheck")
        with open("Entrez/elink7.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(len(record), 1)
        self.assertEqual(record[0]["DbFrom"], "pubmed")
        self.assertEqual(len(record[0]["IdCheckList"]), 2)
        self.assertEqual(record[0]["IdCheckList"]["IdLinkSet"][0]["Id"], "12169658")
        self.assertEqual(len(record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"]), 19)
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][0]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][0]["DbTo"],
            "biosystems",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][0]["LinkName"],
            "pubmed_biosystems",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][0]["MenuTag"],
            "BioSystem Links",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][0]["HtmlTag"],
            "BioSystems",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][0]["Priority"], "128"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][1]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][1]["DbTo"], "books"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][1]["LinkName"],
            "pubmed_books_refs",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][1]["MenuTag"],
            "Cited in Books",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][1]["HtmlTag"],
            "Cited in Books",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][1]["Priority"], "185"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][2]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][2]["DbTo"], "cdd"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][2]["LinkName"],
            "pubmed_cdd",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][2]["MenuTag"],
            "Domain Links",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][2]["HtmlTag"],
            "Domains",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][2]["Priority"], "130"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][3]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][3]["DbTo"], "gene"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][3]["LinkName"],
            "pubmed_gene",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][3]["MenuTag"],
            "Gene Links",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][3]["HtmlTag"], "Gene"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][3]["Priority"], "128"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][4]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][4]["DbTo"],
            "geoprofiles",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][4]["LinkName"],
            "pubmed_geoprofiles",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][4]["MenuTag"],
            "GEO Profile Links",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][4]["HtmlTag"],
            "GEO Profiles",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][4]["Priority"], "170"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][5]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][5]["DbTo"],
            "homologene",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][5]["LinkName"],
            "pubmed_homologene",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][5]["MenuTag"],
            "HomoloGene Links",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][5]["HtmlTag"],
            "HomoloGene",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][5]["Priority"], "128"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][6]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][6]["DbTo"], "medgen"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][6]["LinkName"],
            "pubmed_medgen",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][6]["MenuTag"], "MedGen"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][6]["HtmlTag"], "MedGen"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][6]["Priority"], "128"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][7]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][7]["DbTo"], "nuccore"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][7]["LinkName"],
            "pubmed_nuccore",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][7]["MenuTag"],
            "Nucleotide Links",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][7]["HtmlTag"],
            "Nucleotide",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][7]["Priority"], "128"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][8]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][8]["DbTo"], "nuccore"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][8]["LinkName"],
            "pubmed_nuccore_refseq",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][8]["MenuTag"],
            "Nucleotide (RefSeq) Links",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][8]["HtmlTag"],
            "Nucleotide (RefSeq)",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][8]["Priority"], "128"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][9]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][9]["DbTo"], "nuccore"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][9]["LinkName"],
            "pubmed_nuccore_weighted",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][9]["MenuTag"],
            "Nucleotide (Weighted) Links",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][9]["HtmlTag"],
            "Nucleotide (Weighted)",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][9]["Priority"], "128"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][10]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][10]["DbTo"],
            "pcsubstance",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][10]["LinkName"],
            "pubmed_pcsubstance_mesh",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][10]["MenuTag"],
            "Substance (MeSH Keyword)",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][10]["HtmlTag"],
            "Substance (MeSH Keyword)",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][10]["Priority"], "128"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][11]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][11]["DbTo"], "pmc"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][11]["LinkName"],
            "pubmed_pmc_refs",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][11]["MenuTag"],
            "Cited in PMC",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][11]["HtmlTag"],
            "Cited in PMC",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][11]["Priority"], "180"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][12]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][12]["DbTo"], "protein"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][12]["LinkName"],
            "pubmed_protein",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][12]["MenuTag"],
            "Protein Links",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][12]["HtmlTag"],
            "Protein",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][12]["Priority"], "140"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][13]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][13]["DbTo"], "protein"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][13]["LinkName"],
            "pubmed_protein_refseq",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][13]["MenuTag"],
            "Protein (RefSeq) Links",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][13]["HtmlTag"],
            "Protein (RefSeq)",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][13]["Priority"], "128"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][14]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][14]["DbTo"], "protein"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][14]["LinkName"],
            "pubmed_protein_weighted",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][14]["MenuTag"],
            "Protein (Weighted) Links",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][14]["HtmlTag"],
            "Protein (Weighted)",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][14]["Priority"], "128"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][15]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][15]["DbTo"], "pubmed"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][15]["LinkName"],
            "pubmed_pubmed",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][15]["MenuTag"],
            "Related Citations",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][15]["HtmlTag"],
            "Related Citations",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][15]["Priority"], "1"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][16]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][16]["DbTo"], "taxonomy"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][16]["LinkName"],
            "pubmed_taxonomy_entrez",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][16]["MenuTag"],
            "Taxonomy via GenBank",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][16]["HtmlTag"],
            "Taxonomy via GenBank",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][16]["Priority"], "128"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][17]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][17]["DbTo"], "unigene"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][17]["LinkName"],
            "pubmed_unigene",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][17]["MenuTag"],
            "UniGene Links",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][17]["HtmlTag"],
            "UniGene",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][17]["Priority"], "128"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][18]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][18]["DbTo"], "LinkOut"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][18]["LinkName"],
            "ExternalLink",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][18]["MenuTag"],
            "LinkOut",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][18]["HtmlTag"],
            "LinkOut",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][0]["LinkInfo"][18]["Priority"], "255"
        )
        self.assertEqual(record[0]["IdCheckList"]["IdLinkSet"][1]["Id"], "11748140")
        self.assertEqual(len(record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"]), 15)
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][0]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][0]["DbTo"],
            "biosystems",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][0]["LinkName"],
            "pubmed_biosystems",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][0]["MenuTag"],
            "BioSystem Links",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][0]["HtmlTag"],
            "BioSystems",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][0]["Priority"], "128"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][1]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][1]["DbTo"], "books"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][1]["LinkName"],
            "pubmed_books_refs",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][1]["MenuTag"],
            "Cited in Books",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][1]["HtmlTag"],
            "Cited in Books",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][1]["Priority"], "185"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][2]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][2]["DbTo"], "gene"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][2]["LinkName"],
            "pubmed_gene",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][2]["MenuTag"],
            "Gene Links",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][2]["HtmlTag"], "Gene"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][2]["Priority"], "128"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][3]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][3]["DbTo"],
            "geoprofiles",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][3]["LinkName"],
            "pubmed_geoprofiles",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][3]["MenuTag"],
            "GEO Profile Links",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][3]["HtmlTag"],
            "GEO Profiles",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][3]["Priority"], "170"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][4]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][4]["DbTo"], "nuccore"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][4]["LinkName"],
            "pubmed_nuccore",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][4]["MenuTag"],
            "Nucleotide Links",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][4]["HtmlTag"],
            "Nucleotide",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][4]["Priority"], "128"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][5]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][5]["DbTo"], "nuccore"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][5]["LinkName"],
            "pubmed_nuccore_refseq",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][5]["MenuTag"],
            "Nucleotide (RefSeq) Links",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][5]["HtmlTag"],
            "Nucleotide (RefSeq)",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][5]["Priority"], "128"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][6]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][6]["DbTo"], "nuccore"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][6]["LinkName"],
            "pubmed_nuccore_weighted",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][6]["MenuTag"],
            "Nucleotide (Weighted) Links",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][6]["HtmlTag"],
            "Nucleotide (Weighted)",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][6]["Priority"], "128"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][7]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][7]["DbTo"], "pmc"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][7]["LinkName"],
            "pubmed_pmc_refs",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][7]["MenuTag"],
            "Cited in PMC",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][7]["HtmlTag"],
            "Cited in PMC",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][7]["Priority"], "180"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][8]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][8]["DbTo"], "protein"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][8]["LinkName"],
            "pubmed_protein",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][8]["MenuTag"],
            "Protein Links",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][8]["HtmlTag"],
            "Protein",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][8]["Priority"], "140"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][9]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][9]["DbTo"], "protein"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][9]["LinkName"],
            "pubmed_protein_refseq",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][9]["MenuTag"],
            "Protein (RefSeq) Links",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][9]["HtmlTag"],
            "Protein (RefSeq)",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][9]["Priority"], "128"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][10]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][10]["DbTo"], "protein"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][10]["LinkName"],
            "pubmed_protein_weighted",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][10]["MenuTag"],
            "Protein (Weighted) Links",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][10]["HtmlTag"],
            "Protein (Weighted)",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][10]["Priority"], "128"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][11]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][11]["DbTo"], "pubmed"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][11]["LinkName"],
            "pubmed_pubmed",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][11]["MenuTag"],
            "Related Citations",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][11]["HtmlTag"],
            "Related Citations",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][11]["Priority"], "1"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][12]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][12]["DbTo"], "taxonomy"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][12]["LinkName"],
            "pubmed_taxonomy_entrez",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][12]["MenuTag"],
            "Taxonomy via GenBank",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][12]["HtmlTag"],
            "Taxonomy via GenBank",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][12]["Priority"], "128"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][13]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][13]["DbTo"], "unigene"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][13]["LinkName"],
            "pubmed_unigene",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][13]["MenuTag"],
            "UniGene Links",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][13]["HtmlTag"],
            "UniGene",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][13]["Priority"], "128"
        )
        self.assertEqual(
            len(record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][14]), 5
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][14]["DbTo"], "LinkOut"
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][14]["LinkName"],
            "ExternalLink",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][14]["MenuTag"],
            "LinkOut",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][14]["HtmlTag"],
            "LinkOut",
        )
        self.assertEqual(
            record[0]["IdCheckList"]["IdLinkSet"][1]["LinkInfo"][14]["Priority"], "255"
        )

    def test_pubmed6(self):
        """Test parsing pubmed links returned by ELink (sixth test)."""
        # Check for the existence of a Related Articles link for PMID
        # 12068369.
        # To create the XML file, use
        # >>> Bio.Entrez.elink(dbfrom="pubmed", id="12068369", cmd="ncheck")

        with open("Entrez/elink8.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(len(record), 1)
        self.assertEqual(record[0]["DbFrom"], "pubmed")
        self.assertEqual(len(record[0]["IdCheckList"]), 2)
        self.assertEqual(len(record[0]["IdCheckList"]["Id"]), 1)
        self.assertEqual(record[0]["IdCheckList"]["Id"][0], "12068369")
        self.assertEqual(len(record[0]["IdCheckList"]["Id"][0].attributes), 1)
        self.assertEqual(
            record[0]["IdCheckList"]["Id"][0].attributes["HasNeighbor"], "Y"
        )
        self.assertEqual(len(record[0]["IdCheckList"]["IdLinkSet"]), 0)


class EGQueryTest(unittest.TestCase):
    """Tests for parsing XML output returned by EGQuery."""

    def test_egquery1(self):
        """Test parsing XML output returned by EGQuery (first test)."""
        # Display counts in XML for stem cells in each Entrez database
        # To create the XML file, use
        # >>> Bio.Entrez.egquery(term="stem cells")
        with open("Entrez/egquery1.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record["Term"], "stem cells")
        self.assertEqual(record["eGQueryResult"][0]["DbName"], "pubmed")
        self.assertEqual(record["eGQueryResult"][0]["MenuName"], "PubMed")
        self.assertEqual(record["eGQueryResult"][0]["Count"], "392")
        self.assertEqual(record["eGQueryResult"][0]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][1]["DbName"], "pmc")
        self.assertEqual(record["eGQueryResult"][1]["MenuName"], "PMC")
        self.assertEqual(record["eGQueryResult"][1]["Count"], "173")
        self.assertEqual(record["eGQueryResult"][1]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][2]["DbName"], "journals")
        self.assertEqual(record["eGQueryResult"][2]["MenuName"], "Journals")
        self.assertEqual(record["eGQueryResult"][2]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][2]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][3]["DbName"], "mesh")
        self.assertEqual(record["eGQueryResult"][3]["MenuName"], "MeSH")
        self.assertEqual(record["eGQueryResult"][3]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][3]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][4]["DbName"], "books")
        self.assertEqual(record["eGQueryResult"][4]["MenuName"], "Books")
        self.assertEqual(record["eGQueryResult"][4]["Count"], "10")
        self.assertEqual(record["eGQueryResult"][4]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][5]["DbName"], "omim")
        self.assertEqual(record["eGQueryResult"][5]["MenuName"], "OMIM")
        self.assertEqual(record["eGQueryResult"][5]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][5]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][6]["DbName"], "omia")
        self.assertEqual(record["eGQueryResult"][6]["MenuName"], "OMIA")
        self.assertEqual(record["eGQueryResult"][6]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][6]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][7]["DbName"], "ncbisearch")
        self.assertEqual(record["eGQueryResult"][7]["MenuName"], "NCBI Web Site")
        self.assertEqual(record["eGQueryResult"][7]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][7]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][8]["DbName"], "nuccore")
        self.assertEqual(record["eGQueryResult"][8]["MenuName"], "CoreNucleotide")
        self.assertEqual(record["eGQueryResult"][8]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][8]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][9]["DbName"], "nucgss")
        self.assertEqual(record["eGQueryResult"][9]["MenuName"], "GSS")
        self.assertEqual(record["eGQueryResult"][9]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][9]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][10]["DbName"], "nucest")
        self.assertEqual(record["eGQueryResult"][10]["MenuName"], "EST")
        self.assertEqual(record["eGQueryResult"][10]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][10]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][11]["DbName"], "protein")
        self.assertEqual(record["eGQueryResult"][11]["MenuName"], "Protein")
        self.assertEqual(record["eGQueryResult"][11]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][11]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][12]["DbName"], "genome")
        self.assertEqual(record["eGQueryResult"][12]["MenuName"], "Genome")
        self.assertEqual(record["eGQueryResult"][12]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][12]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][13]["DbName"], "structure")
        self.assertEqual(record["eGQueryResult"][13]["MenuName"], "Structure")
        self.assertEqual(record["eGQueryResult"][13]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][13]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][14]["DbName"], "taxonomy")
        self.assertEqual(record["eGQueryResult"][14]["MenuName"], "Taxonomy")
        self.assertEqual(record["eGQueryResult"][14]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][14]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][15]["DbName"], "snp")
        self.assertEqual(record["eGQueryResult"][15]["MenuName"], "SNP")
        self.assertEqual(record["eGQueryResult"][15]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][15]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][16]["DbName"], "gene")
        self.assertEqual(record["eGQueryResult"][16]["MenuName"], "Gene")
        self.assertEqual(record["eGQueryResult"][16]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][16]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][17]["DbName"], "unigene")
        self.assertEqual(record["eGQueryResult"][17]["MenuName"], "UniGene")
        self.assertEqual(record["eGQueryResult"][17]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][17]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][18]["DbName"], "cdd")
        self.assertEqual(record["eGQueryResult"][18]["MenuName"], "Conserved Domains")
        self.assertEqual(record["eGQueryResult"][18]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][18]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][19]["DbName"], "domains")
        self.assertEqual(record["eGQueryResult"][19]["MenuName"], "3D Domains")
        self.assertEqual(record["eGQueryResult"][19]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][19]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][20]["DbName"], "unists")
        self.assertEqual(record["eGQueryResult"][20]["MenuName"], "UniSTS")
        self.assertEqual(record["eGQueryResult"][20]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][20]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][21]["DbName"], "popset")
        self.assertEqual(record["eGQueryResult"][21]["MenuName"], "PopSet")
        self.assertEqual(record["eGQueryResult"][21]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][21]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][22]["DbName"], "geo")
        self.assertEqual(record["eGQueryResult"][22]["MenuName"], "GEO Profiles")
        self.assertEqual(record["eGQueryResult"][22]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][22]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][23]["DbName"], "gds")
        self.assertEqual(record["eGQueryResult"][23]["MenuName"], "GEO DataSets")
        self.assertEqual(record["eGQueryResult"][23]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][23]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][24]["DbName"], "homologene")
        self.assertEqual(record["eGQueryResult"][24]["MenuName"], "HomoloGene")
        self.assertEqual(record["eGQueryResult"][24]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][24]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][25]["DbName"], "cancerchromosomes")
        self.assertEqual(record["eGQueryResult"][25]["MenuName"], "CancerChromosomes")
        self.assertEqual(record["eGQueryResult"][25]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][25]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][26]["DbName"], "pccompound")
        self.assertEqual(record["eGQueryResult"][26]["MenuName"], "PubChem Compound")
        self.assertEqual(record["eGQueryResult"][26]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][26]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][27]["DbName"], "pcsubstance")
        self.assertEqual(record["eGQueryResult"][27]["MenuName"], "PubChem Substance")
        self.assertEqual(record["eGQueryResult"][27]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][27]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][28]["DbName"], "pcassay")
        self.assertEqual(record["eGQueryResult"][28]["MenuName"], "PubChem BioAssay")
        self.assertEqual(record["eGQueryResult"][28]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][28]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][29]["DbName"], "nlmcatalog")
        self.assertEqual(record["eGQueryResult"][29]["MenuName"], "NLM Catalog")
        self.assertEqual(record["eGQueryResult"][29]["Count"], "2")
        self.assertEqual(record["eGQueryResult"][29]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][30]["DbName"], "gensat")
        self.assertEqual(record["eGQueryResult"][30]["MenuName"], "GENSAT")
        self.assertEqual(record["eGQueryResult"][30]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][30]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][31]["DbName"], "probe")
        self.assertEqual(record["eGQueryResult"][31]["MenuName"], "Probe")
        self.assertEqual(record["eGQueryResult"][31]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][31]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][32]["DbName"], "genomeprj")
        self.assertEqual(record["eGQueryResult"][32]["MenuName"], "Genome Project")
        self.assertEqual(record["eGQueryResult"][32]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][32]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][33]["DbName"], "gap")
        self.assertEqual(record["eGQueryResult"][33]["MenuName"], "dbGaP")
        self.assertEqual(record["eGQueryResult"][33]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][33]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][34]["DbName"], "proteinclusters")
        self.assertEqual(record["eGQueryResult"][34]["MenuName"], "Protein Clusters")
        self.assertEqual(record["eGQueryResult"][34]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][34]["Status"], "Term or Database is not found"
        )

    def test_egquery2(self):
        """Test parsing XML output returned by EGQuery (second test)."""
        # Display counts in XML for brca1 or brca2 for each Entrez database
        # To create the XML file, use
        # >>> Bio.Entrez.egquery(term="brca1 OR brca2")
        with open("Entrez/egquery2.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record["Term"], "brca1 OR brca2")
        self.assertEqual(record["eGQueryResult"][0]["DbName"], "pubmed")
        self.assertEqual(record["eGQueryResult"][0]["MenuName"], "PubMed")
        self.assertEqual(record["eGQueryResult"][0]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][0]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][1]["DbName"], "pmc")
        self.assertEqual(record["eGQueryResult"][1]["MenuName"], "PMC")
        self.assertEqual(record["eGQueryResult"][1]["Count"], "2739")
        self.assertEqual(record["eGQueryResult"][1]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][2]["DbName"], "journals")
        self.assertEqual(record["eGQueryResult"][2]["MenuName"], "Journals")
        self.assertEqual(record["eGQueryResult"][2]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][2]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][3]["DbName"], "mesh")
        self.assertEqual(record["eGQueryResult"][3]["MenuName"], "MeSH")
        self.assertEqual(record["eGQueryResult"][3]["Count"], "29")
        self.assertEqual(record["eGQueryResult"][3]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][4]["DbName"], "books")
        self.assertEqual(record["eGQueryResult"][4]["MenuName"], "Books")
        self.assertEqual(record["eGQueryResult"][4]["Count"], "392")
        self.assertEqual(record["eGQueryResult"][4]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][5]["DbName"], "omim")
        self.assertEqual(record["eGQueryResult"][5]["MenuName"], "OMIM")
        self.assertEqual(record["eGQueryResult"][5]["Count"], "149")
        self.assertEqual(record["eGQueryResult"][5]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][6]["DbName"], "omia")
        self.assertEqual(record["eGQueryResult"][6]["MenuName"], "OMIA")
        self.assertEqual(record["eGQueryResult"][6]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][6]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][7]["DbName"], "ncbisearch")
        self.assertEqual(record["eGQueryResult"][7]["MenuName"], "NCBI Web Site")
        self.assertEqual(record["eGQueryResult"][7]["Count"], "13")
        self.assertEqual(record["eGQueryResult"][7]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][8]["DbName"], "nuccore")
        self.assertEqual(record["eGQueryResult"][8]["MenuName"], "CoreNucleotide")
        self.assertEqual(record["eGQueryResult"][8]["Count"], "4917")
        self.assertEqual(record["eGQueryResult"][8]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][9]["DbName"], "nucgss")
        self.assertEqual(record["eGQueryResult"][9]["MenuName"], "GSS")
        self.assertEqual(record["eGQueryResult"][9]["Count"], "184")
        self.assertEqual(record["eGQueryResult"][9]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][10]["DbName"], "nucest")
        self.assertEqual(record["eGQueryResult"][10]["MenuName"], "EST")
        self.assertEqual(record["eGQueryResult"][10]["Count"], "600")
        self.assertEqual(record["eGQueryResult"][10]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][11]["DbName"], "protein")
        self.assertEqual(record["eGQueryResult"][11]["MenuName"], "Protein")
        self.assertEqual(record["eGQueryResult"][11]["Count"], "6779")
        self.assertEqual(record["eGQueryResult"][11]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][12]["DbName"], "genome")
        self.assertEqual(record["eGQueryResult"][12]["MenuName"], "Genome")
        self.assertEqual(record["eGQueryResult"][12]["Count"], "44")
        self.assertEqual(record["eGQueryResult"][12]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][13]["DbName"], "structure")
        self.assertEqual(record["eGQueryResult"][13]["MenuName"], "Structure")
        self.assertEqual(record["eGQueryResult"][13]["Count"], "29")
        self.assertEqual(record["eGQueryResult"][13]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][14]["DbName"], "taxonomy")
        self.assertEqual(record["eGQueryResult"][14]["MenuName"], "Taxonomy")
        self.assertEqual(record["eGQueryResult"][14]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][14]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][15]["DbName"], "snp")
        self.assertEqual(record["eGQueryResult"][15]["MenuName"], "SNP")
        self.assertEqual(record["eGQueryResult"][15]["Count"], "2013")
        self.assertEqual(record["eGQueryResult"][15]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][16]["DbName"], "gene")
        self.assertEqual(record["eGQueryResult"][16]["MenuName"], "Gene")
        self.assertEqual(record["eGQueryResult"][16]["Count"], "1775")
        self.assertEqual(record["eGQueryResult"][16]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][17]["DbName"], "unigene")
        self.assertEqual(record["eGQueryResult"][17]["MenuName"], "UniGene")
        self.assertEqual(record["eGQueryResult"][17]["Count"], "207")
        self.assertEqual(record["eGQueryResult"][17]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][18]["DbName"], "cdd")
        self.assertEqual(record["eGQueryResult"][18]["MenuName"], "Conserved Domains")
        self.assertEqual(record["eGQueryResult"][18]["Count"], "17")
        self.assertEqual(record["eGQueryResult"][18]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][19]["DbName"], "domains")
        self.assertEqual(record["eGQueryResult"][19]["MenuName"], "3D Domains")
        self.assertEqual(record["eGQueryResult"][19]["Count"], "131")
        self.assertEqual(record["eGQueryResult"][19]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][20]["DbName"], "unists")
        self.assertEqual(record["eGQueryResult"][20]["MenuName"], "UniSTS")
        self.assertEqual(record["eGQueryResult"][20]["Count"], "198")
        self.assertEqual(record["eGQueryResult"][20]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][21]["DbName"], "popset")
        self.assertEqual(record["eGQueryResult"][21]["MenuName"], "PopSet")
        self.assertEqual(record["eGQueryResult"][21]["Count"], "43")
        self.assertEqual(record["eGQueryResult"][21]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][22]["DbName"], "geo")
        self.assertEqual(record["eGQueryResult"][22]["MenuName"], "GEO Profiles")
        self.assertEqual(record["eGQueryResult"][22]["Count"], "128692")
        self.assertEqual(record["eGQueryResult"][22]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][23]["DbName"], "gds")
        self.assertEqual(record["eGQueryResult"][23]["MenuName"], "GEO DataSets")
        self.assertEqual(record["eGQueryResult"][23]["Count"], "21")
        self.assertEqual(record["eGQueryResult"][23]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][24]["DbName"], "homologene")
        self.assertEqual(record["eGQueryResult"][24]["MenuName"], "HomoloGene")
        self.assertEqual(record["eGQueryResult"][24]["Count"], "50")
        self.assertEqual(record["eGQueryResult"][24]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][25]["DbName"], "cancerchromosomes")
        self.assertEqual(record["eGQueryResult"][25]["MenuName"], "CancerChromosomes")
        self.assertEqual(record["eGQueryResult"][25]["Count"], "18")
        self.assertEqual(record["eGQueryResult"][25]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][26]["DbName"], "pccompound")
        self.assertEqual(record["eGQueryResult"][26]["MenuName"], "PubChem Compound")
        self.assertEqual(record["eGQueryResult"][26]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][26]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][27]["DbName"], "pcsubstance")
        self.assertEqual(record["eGQueryResult"][27]["MenuName"], "PubChem Substance")
        self.assertEqual(record["eGQueryResult"][27]["Count"], "26")
        self.assertEqual(record["eGQueryResult"][27]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][28]["DbName"], "pcassay")
        self.assertEqual(record["eGQueryResult"][28]["MenuName"], "PubChem BioAssay")
        self.assertEqual(record["eGQueryResult"][28]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][28]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][29]["DbName"], "nlmcatalog")
        self.assertEqual(record["eGQueryResult"][29]["MenuName"], "NLM Catalog")
        self.assertEqual(record["eGQueryResult"][29]["Count"], "31")
        self.assertEqual(record["eGQueryResult"][29]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][30]["DbName"], "gensat")
        self.assertEqual(record["eGQueryResult"][30]["MenuName"], "GENSAT")
        self.assertEqual(record["eGQueryResult"][30]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][30]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][31]["DbName"], "probe")
        self.assertEqual(record["eGQueryResult"][31]["MenuName"], "Probe")
        self.assertEqual(record["eGQueryResult"][31]["Count"], "1410")
        self.assertEqual(record["eGQueryResult"][31]["Status"], "Ok")
        self.assertEqual(record["eGQueryResult"][32]["DbName"], "genomeprj")
        self.assertEqual(record["eGQueryResult"][32]["MenuName"], "Genome Project")
        self.assertEqual(record["eGQueryResult"][32]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][32]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][33]["DbName"], "gap")
        self.assertEqual(record["eGQueryResult"][33]["MenuName"], "dbGaP")
        self.assertEqual(record["eGQueryResult"][33]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][33]["Status"], "Term or Database is not found"
        )
        self.assertEqual(record["eGQueryResult"][34]["DbName"], "proteinclusters")
        self.assertEqual(record["eGQueryResult"][34]["MenuName"], "Protein Clusters")
        self.assertEqual(record["eGQueryResult"][34]["Count"], "0")
        self.assertEqual(
            record["eGQueryResult"][34]["Status"], "Term or Database is not found"
        )


class ESpellTest(unittest.TestCase):
    """Tests for parsing XML output returned by ESpell."""

    def test_espell(self):
        """Test parsing XML output returned by ESpell."""
        # Request suggestions for the PubMed search biopythooon
        # To create the XML file, use
        # >>> Bio.Entrez.espell(db="pubmed", term="biopythooon")
        with open("Entrez/espell.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record["Database"], "pubmed")
        self.assertEqual(record["Query"], "biopythooon")
        self.assertEqual(record["CorrectedQuery"], "biopython")
        self.assertEqual(len(record["SpelledQuery"]), 1)
        self.assertEqual(record["SpelledQuery"][0], "biopython")
        self.assertEqual(record["SpelledQuery"][0].tag, "Replaced")


class EFetchTest(unittest.TestCase):
    """Tests for parsing XML output returned by EFetch."""

    def test_pubmed1(self):
        """Test parsing XML returned by EFetch, PubMed database (first test)."""
        # In PubMed display PMIDs 12091962 and 9997 in xml retrieval mode
        # and abstract retrieval type.
        # To create the XML file, use
        # >>> Bio.Entrez.efetch(db='pubmed', id='12091962,9997',
        #                       retmode='xml', rettype='abstract')
        with open("Entrez/pubmed1.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record[0]["MedlineCitation"].attributes["Owner"], "KIE")
        self.assertEqual(record[0]["MedlineCitation"].attributes["Status"], "MEDLINE")
        self.assertEqual(record[0]["MedlineCitation"]["PMID"], "12091962")
        self.assertEqual(record[0]["MedlineCitation"]["DateCreated"]["Year"], "1991")
        self.assertEqual(record[0]["MedlineCitation"]["DateCreated"]["Month"], "01")
        self.assertEqual(record[0]["MedlineCitation"]["DateCreated"]["Day"], "22")
        self.assertEqual(record[0]["MedlineCitation"]["DateCompleted"]["Year"], "1991")
        self.assertEqual(record[0]["MedlineCitation"]["DateCompleted"]["Month"], "01")
        self.assertEqual(record[0]["MedlineCitation"]["DateCompleted"]["Day"], "22")
        self.assertEqual(record[0]["MedlineCitation"]["DateRevised"]["Year"], "2007")
        self.assertEqual(record[0]["MedlineCitation"]["DateRevised"]["Month"], "11")
        self.assertEqual(record[0]["MedlineCitation"]["DateRevised"]["Day"], "15")
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"].attributes["PubModel"], "Print"
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["Journal"]["ISSN"], "1043-1578"
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["Journal"]["ISSN"].attributes[
                "IssnType"
            ],
            "Print",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["Journal"][
                "JournalIssue"
            ].attributes["CitedMedium"],
            "Print",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["Journal"]["JournalIssue"][
                "Volume"
            ],
            "17",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["Journal"]["JournalIssue"]["Issue"],
            "1",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["Journal"]["JournalIssue"][
                "PubDate"
            ]["Year"],
            "1990",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["Journal"]["JournalIssue"][
                "PubDate"
            ]["Season"],
            "Spring",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["Journal"]["Title"],
            "Social justice (San Francisco, Calif.)",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["ArticleTitle"],
            "The treatment of AIDS behind the walls of correctional facilities.",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["Pagination"]["MedlinePgn"],
            "113-25",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"].attributes[
                "CompleteYN"
            ],
            "Y",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][0].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][0]["LastName"],
            "Olivero",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][0]["ForeName"],
            "J Michael",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][0]["Initials"], "JM"
        )
        self.assertEqual(record[0]["MedlineCitation"]["Article"]["Language"], ["eng"])
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["PublicationTypeList"],
            ["Journal Article", "Review"],
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MedlineJournalInfo"]["Country"],
            "United States",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MedlineJournalInfo"]["MedlineTA"],
            "Soc Justice",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MedlineJournalInfo"]["NlmUniqueID"], "9891830"
        )
        self.assertEqual(record[0]["MedlineCitation"]["CitationSubset"], ["E"])
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][0]["DescriptorName"],
            "AIDS Serodiagnosis",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][0][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][1]["DescriptorName"],
            "Acquired Immunodeficiency Syndrome",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][1][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "Y",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][2]["DescriptorName"],
            "Civil Rights",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][2][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][3]["DescriptorName"],
            "HIV Seropositivity",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][3][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "Y",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][4]["DescriptorName"],
            "Humans",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][4][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][5]["DescriptorName"],
            "Jurisprudence",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][5][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "Y",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][6]["DescriptorName"],
            "Law Enforcement",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][6][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][7]["DescriptorName"],
            "Mass Screening",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][7][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][8]["DescriptorName"],
            "Minority Groups",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][8][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][9]["DescriptorName"],
            "Organizational Policy",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][9][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][10]["DescriptorName"],
            "Patient Care",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][10][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][11]["DescriptorName"],
            "Prejudice",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][11][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][12]["DescriptorName"],
            "Prisoners",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][12][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "Y",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][13]["DescriptorName"],
            "Public Policy",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][13][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "Y",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][14]["DescriptorName"],
            "Quarantine",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][14][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][15]["DescriptorName"],
            "Social Control, Formal",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][15][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][16]["DescriptorName"],
            "Statistics as Topic",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][16][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][17]["DescriptorName"],
            "Stereotyping",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][17][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][18]["DescriptorName"],
            "United States",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][18][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(record[0]["MedlineCitation"]["NumberOfReferences"], "63")
        self.assertEqual(record[0]["MedlineCitation"]["OtherID"][0], "31840")
        self.assertEqual(
            record[0]["MedlineCitation"]["OtherID"][0].attributes["Source"], "KIE"
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["KeywordList"][0].attributes["Owner"], "KIE"
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["KeywordList"][0][0],
            "Health Care and Public Health",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["KeywordList"][0][0].attributes[
                "MajorTopicYN"
            ],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["KeywordList"][0][1], "Legal Approach"
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["KeywordList"][0][1].attributes[
                "MajorTopicYN"
            ],
            "N",
        )
        self.assertEqual(record[0]["MedlineCitation"]["GeneralNote"][0], "14 fn.")
        self.assertEqual(
            record[0]["MedlineCitation"]["GeneralNote"][0].attributes["Owner"], "KIE"
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["GeneralNote"][1],
            "KIE BoB Subject Heading: AIDS",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["GeneralNote"][1].attributes["Owner"], "KIE"
        )
        self.assertEqual(record[0]["MedlineCitation"]["GeneralNote"][2], "63 refs.")
        self.assertEqual(
            record[0]["MedlineCitation"]["GeneralNote"][2].attributes["Owner"], "KIE"
        )
        self.assertEqual(
            record[0]["PubmedData"]["History"][0][0].attributes["PubStatus"], "pubmed"
        )
        self.assertEqual(record[0]["PubmedData"]["History"][0][0]["Year"], "1990")
        self.assertEqual(record[0]["PubmedData"]["History"][0][0]["Month"], "4")
        self.assertEqual(record[0]["PubmedData"]["History"][0][0]["Day"], "1")
        self.assertEqual(record[0]["PubmedData"]["History"][0][0]["Hour"], "0")
        self.assertEqual(record[0]["PubmedData"]["History"][0][0]["Minute"], "0")
        self.assertEqual(
            record[0]["PubmedData"]["History"][0][1].attributes["PubStatus"], "medline"
        )
        self.assertEqual(record[0]["PubmedData"]["History"][0][1]["Year"], "2002")
        self.assertEqual(record[0]["PubmedData"]["History"][0][1]["Month"], "7")
        self.assertEqual(record[0]["PubmedData"]["History"][0][1]["Day"], "16")
        self.assertEqual(record[0]["PubmedData"]["History"][0][1]["Hour"], "10")
        self.assertEqual(record[0]["PubmedData"]["History"][0][1]["Minute"], "1")
        self.assertEqual(record[0]["PubmedData"]["PublicationStatus"], "ppublish")
        self.assertEqual(len(record[0]["PubmedData"]["ArticleIdList"]), 1)
        self.assertEqual(record[0]["PubmedData"]["ArticleIdList"][0], "12091962")
        self.assertEqual(
            record[0]["PubmedData"]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(record[1]["MedlineCitation"].attributes["Owner"], "NLM")
        self.assertEqual(record[1]["MedlineCitation"].attributes["Status"], "MEDLINE")
        self.assertEqual(record[1]["MedlineCitation"]["PMID"], "9997")
        self.assertEqual(record[1]["MedlineCitation"]["DateCreated"]["Year"], "1976")
        self.assertEqual(record[1]["MedlineCitation"]["DateCreated"]["Month"], "12")
        self.assertEqual(record[1]["MedlineCitation"]["DateCreated"]["Day"], "30")
        self.assertEqual(record[1]["MedlineCitation"]["DateCompleted"]["Year"], "1976")
        self.assertEqual(record[1]["MedlineCitation"]["DateCompleted"]["Month"], "12")
        self.assertEqual(record[1]["MedlineCitation"]["DateCompleted"]["Day"], "30")
        self.assertEqual(record[1]["MedlineCitation"]["DateRevised"]["Year"], "2003")
        self.assertEqual(record[1]["MedlineCitation"]["DateRevised"]["Month"], "11")
        self.assertEqual(record[1]["MedlineCitation"]["DateRevised"]["Day"], "14")
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"].attributes["PubModel"], "Print"
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["Journal"]["ISSN"], "0006-3002"
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["Journal"]["ISSN"].attributes[
                "IssnType"
            ],
            "Print",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["Journal"][
                "JournalIssue"
            ].attributes["CitedMedium"],
            "Print",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["Journal"]["JournalIssue"][
                "Volume"
            ],
            "446",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["Journal"]["JournalIssue"]["Issue"],
            "1",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["Journal"]["JournalIssue"][
                "PubDate"
            ]["Year"],
            "1976",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["Journal"]["JournalIssue"][
                "PubDate"
            ]["Month"],
            "Sep",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["Journal"]["JournalIssue"][
                "PubDate"
            ]["Day"],
            "28",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["Journal"]["Title"],
            "Biochimica et biophysica acta",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["Journal"]["ISOAbbreviation"],
            "Biochim. Biophys. Acta",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["ArticleTitle"],
            "Magnetic studies of Chromatium flavocytochrome C552. A mechanism for heme-flavin interaction.",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["Pagination"]["MedlinePgn"],
            "179-91",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["Abstract"]["AbstractText"],
            "Electron paramagnetic resonance and magnetic susceptibility studies of Chromatium flavocytochrome C552 and its diheme flavin-free subunit at temperatures below 45 degrees K are reported. The results show that in the intact protein and the subunit the two low-spin (S = 1/2) heme irons are distinguishable, giving rise to separate EPR signals. In the intact protein only, one of the heme irons exists in two different low spin environments in the pH range 5.5 to 10.5, while the other remains in a constant environment. Factors influencing the variable heme iron environment also influence flavin reactivity, indicating the existence of a mechanism for heme-flavin interaction.",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"].attributes[
                "CompleteYN"
            ],
            "Y",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][0].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][0]["LastName"],
            "Strekas",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][0]["ForeName"], "T C"
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][0]["Initials"], "TC"
        )
        self.assertEqual(record[1]["MedlineCitation"]["Article"]["Language"], ["eng"])
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["PublicationTypeList"],
            ["Journal Article"],
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MedlineJournalInfo"]["Country"], "NETHERLANDS"
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MedlineJournalInfo"]["MedlineTA"],
            "Biochim Biophys Acta",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MedlineJournalInfo"]["NlmUniqueID"], "0217513"
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["ChemicalList"][0]["RegistryNumber"], "0"
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["ChemicalList"][0]["NameOfSubstance"],
            "Cytochrome c Group",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["ChemicalList"][1]["RegistryNumber"], "0"
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["ChemicalList"][1]["NameOfSubstance"],
            "Flavins",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["ChemicalList"][2]["RegistryNumber"],
            "14875-96-8",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["ChemicalList"][2]["NameOfSubstance"], "Heme"
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["ChemicalList"][3]["RegistryNumber"],
            "7439-89-6",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["ChemicalList"][3]["NameOfSubstance"], "Iron"
        )
        self.assertEqual(record[1]["MedlineCitation"]["CitationSubset"], ["IM"])
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][0]["DescriptorName"],
            "Binding Sites",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][0][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][1]["DescriptorName"],
            "Chromatium",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][1][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][1]["QualifierName"][0],
            "enzymology",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][1]["QualifierName"][
                0
            ].attributes["MajorTopicYN"],
            "Y",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][2]["DescriptorName"],
            "Cytochrome c Group",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][2][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "Y",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][3]["DescriptorName"],
            "Electron Spin Resonance Spectroscopy",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][3][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][4]["DescriptorName"],
            "Flavins",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][4][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][5]["DescriptorName"], "Heme"
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][5][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][6]["DescriptorName"],
            "Hydrogen-Ion Concentration",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][6][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][7]["DescriptorName"], "Iron"
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][7][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][7]["QualifierName"][0],
            "analysis",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][7]["QualifierName"][
                0
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][8]["DescriptorName"],
            "Magnetics",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][8][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][9]["DescriptorName"],
            "Oxidation-Reduction",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][9][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][10]["DescriptorName"],
            "Protein Binding",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][10][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][11]["DescriptorName"],
            "Protein Conformation",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][11][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][12]["DescriptorName"],
            "Temperature",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MeshHeadingList"][12][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[1]["PubmedData"]["History"][0][0].attributes["PubStatus"], "pubmed"
        )
        self.assertEqual(record[1]["PubmedData"]["History"][0][0]["Year"], "1976")
        self.assertEqual(record[1]["PubmedData"]["History"][0][0]["Month"], "9")
        self.assertEqual(record[1]["PubmedData"]["History"][0][0]["Day"], "28")
        self.assertEqual(
            record[1]["PubmedData"]["History"][0][1].attributes["PubStatus"], "medline"
        )
        self.assertEqual(record[1]["PubmedData"]["History"][0][1]["Year"], "1976")
        self.assertEqual(record[1]["PubmedData"]["History"][0][1]["Month"], "9")
        self.assertEqual(record[1]["PubmedData"]["History"][0][1]["Day"], "28")
        self.assertEqual(record[1]["PubmedData"]["History"][0][1]["Hour"], "0")
        self.assertEqual(record[1]["PubmedData"]["History"][0][1]["Minute"], "1")
        self.assertEqual(record[1]["PubmedData"]["PublicationStatus"], "ppublish")
        self.assertEqual(len(record[1]["PubmedData"]["ArticleIdList"]), 1)
        self.assertEqual(record[1]["PubmedData"]["ArticleIdList"][0], "9997")
        self.assertEqual(
            record[1]["PubmedData"]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )

    def test_pubmed2(self):
        """Test parsing XML returned by EFetch, PubMed database (second test)."""
        # In PubMed display PMIDs in xml retrieval mode.
        # To create the XML file, use
        # >>> Bio.Entrez.efetch(db='pubmed', id="11748933,11700088",
        #                       retmode="xml")
        with open("Entrez/pubmed2.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record[0]["MedlineCitation"].attributes["Owner"], "NLM")
        self.assertEqual(record[0]["MedlineCitation"].attributes["Status"], "MEDLINE")
        self.assertEqual(record[0]["MedlineCitation"]["PMID"], "11748933")
        self.assertEqual(record[0]["MedlineCitation"]["DateCreated"]["Year"], "2001")
        self.assertEqual(record[0]["MedlineCitation"]["DateCreated"]["Month"], "12")
        self.assertEqual(record[0]["MedlineCitation"]["DateCreated"]["Day"], "25")
        self.assertEqual(record[0]["MedlineCitation"]["DateCompleted"]["Year"], "2002")
        self.assertEqual(record[0]["MedlineCitation"]["DateCompleted"]["Month"], "03")
        self.assertEqual(record[0]["MedlineCitation"]["DateCompleted"]["Day"], "04")
        self.assertEqual(record[0]["MedlineCitation"]["DateRevised"]["Year"], "2006")
        self.assertEqual(record[0]["MedlineCitation"]["DateRevised"]["Month"], "11")
        self.assertEqual(record[0]["MedlineCitation"]["DateRevised"]["Day"], "15")
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"].attributes["PubModel"], "Print"
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["Journal"]["ISSN"], "0011-2240"
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["Journal"]["ISSN"].attributes[
                "IssnType"
            ],
            "Print",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["Journal"][
                "JournalIssue"
            ].attributes["CitedMedium"],
            "Print",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["Journal"]["JournalIssue"][
                "Volume"
            ],
            "42",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["Journal"]["JournalIssue"]["Issue"],
            "4",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["Journal"]["JournalIssue"][
                "PubDate"
            ]["Year"],
            "2001",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["Journal"]["JournalIssue"][
                "PubDate"
            ]["Month"],
            "Jun",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["Journal"]["Title"], "Cryobiology"
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["Journal"]["ISOAbbreviation"],
            "Cryobiology",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["ArticleTitle"],
            "Is cryopreservation a homogeneous process? Ultrastructure and motility of untreated, prefreezing, and postthawed spermatozoa of Diplodus puntazzo (Cetti).",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["Pagination"]["MedlinePgn"],
            "244-55",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["Abstract"]["AbstractText"],
            "This study subdivides the cryopreservation procedure for Diplodus puntazzo spermatozoa into three key phases, fresh, prefreezing (samples equilibrated in cryosolutions), and postthawed stages, and examines the ultrastructural anomalies and motility profiles of spermatozoa in each stage, with different cryodiluents. Two simple cryosolutions were evaluated: 0.17 M sodium chloride containing a final concentration of 15% dimethyl sulfoxide (Me(2)SO) (cryosolution A) and 0.1 M sodium citrate containing a final concentration of 10% Me(2)SO (cryosolution B). Ultrastructural anomalies of the plasmatic and nuclear membranes of the sperm head were common and the severity of the cryoinjury differed significantly between the pre- and the postfreezing phases and between the two cryosolutions. In spermatozoa diluted with cryosolution A, during the prefreezing phase, the plasmalemma of 61% of the cells was absent or damaged compared with 24% in the fresh sample (P < 0.001). In spermatozoa diluted with cryosolution B, there was a pronounced increase in the number of cells lacking the head plasmatic membrane from the prefreezing to the postthawed stages (from 32 to 52%, P < 0.01). In both cryosolutions, damages to nuclear membrane were significantly higher after freezing (cryosolution A: 8 to 23%, P < 0.01; cryosolution B: 5 to 38%, P < 0.001). With cryosolution A, the after-activation motility profile confirmed a consistent drop from fresh at the prefreezing stage, whereas freezing and thawing did not affect the motility much further and 50% of the cells were immotile by 60-90 s after activation. With cryosolution B, only the postthawing stage showed a sharp drop of motility profile. This study suggests that the different phases of the cryoprocess should be investigated to better understand the process of sperm damage.",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["Abstract"]["CopyrightInformation"],
            "Copyright 2001 Elsevier Science.",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["Affiliation"],
            "Dipartimento di Scienze Ambientali, Universit\xe0 degli Studi della Tuscia, 01100 Viterbo, Italy.",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"].attributes[
                "CompleteYN"
            ],
            "Y",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][0].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][0]["LastName"],
            "Taddei",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][0]["ForeName"], "A R"
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][0]["Initials"], "AR"
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][1].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][1]["LastName"],
            "Barbato",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][1]["ForeName"], "F"
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][1]["Initials"], "F"
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][2].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][2]["LastName"],
            "Abelli",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][2]["ForeName"], "L"
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][2]["Initials"], "L"
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][3].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][3]["LastName"],
            "Canese",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][3]["ForeName"], "S"
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][3]["Initials"], "S"
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][4].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][4]["LastName"],
            "Moretti",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][4]["ForeName"], "F"
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][4]["Initials"], "F"
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][5].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][5]["LastName"], "Rana"
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][5]["ForeName"], "K J"
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][5]["Initials"], "KJ"
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][6].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][6]["LastName"],
            "Fausto",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][6]["ForeName"], "A M"
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][6]["Initials"], "AM"
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][7].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][7]["LastName"],
            "Mazzini",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][7]["ForeName"], "M"
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["AuthorList"][7]["Initials"], "M"
        )
        self.assertEqual(record[0]["MedlineCitation"]["Article"]["Language"], ["eng"])
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["PublicationTypeList"][0],
            "Journal Article",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["Article"]["PublicationTypeList"][1],
            "Research Support, Non-U.S. Gov't",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MedlineJournalInfo"]["Country"],
            "United States",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MedlineJournalInfo"]["MedlineTA"],
            "Cryobiology",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MedlineJournalInfo"]["NlmUniqueID"], "0006252"
        )
        self.assertEqual(record[0]["MedlineCitation"]["CitationSubset"], ["IM"])
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][0]["DescriptorName"],
            "Animals",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][0][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][1]["DescriptorName"],
            "Cell Membrane",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][1][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][1]["QualifierName"][0],
            "ultrastructure",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][1]["QualifierName"][
                0
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][2]["DescriptorName"],
            "Cryopreservation",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][2][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][2]["QualifierName"][0],
            "methods",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][2]["QualifierName"][
                0
            ].attributes["MajorTopicYN"],
            "Y",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][3]["DescriptorName"], "Male"
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][3][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][4]["DescriptorName"],
            "Microscopy, Electron",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][4][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][5]["DescriptorName"],
            "Microscopy, Electron, Scanning",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][5][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][6]["DescriptorName"],
            "Nuclear Envelope",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][6][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][6]["QualifierName"][0],
            "ultrastructure",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][6]["QualifierName"][
                0
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][7]["DescriptorName"],
            "Sea Bream",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][7][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][7]["QualifierName"][0],
            "anatomy & histology",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][7]["QualifierName"][
                0
            ].attributes["MajorTopicYN"],
            "Y",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][7]["QualifierName"][1],
            "physiology",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][7]["QualifierName"][
                1
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][8]["DescriptorName"],
            "Semen Preservation",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][8][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][8]["QualifierName"][0],
            "adverse effects",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][8]["QualifierName"][
                0
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][8]["QualifierName"][1],
            "methods",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][8]["QualifierName"][
                1
            ].attributes["MajorTopicYN"],
            "Y",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][9]["DescriptorName"],
            "Sperm Motility",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][9][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "Y",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][10]["DescriptorName"],
            "Spermatozoa",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][10][
                "DescriptorName"
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][10]["QualifierName"][0],
            "physiology",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][10]["QualifierName"][
                0
            ].attributes["MajorTopicYN"],
            "N",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][10]["QualifierName"][1],
            "ultrastructure",
        )
        self.assertEqual(
            record[0]["MedlineCitation"]["MeshHeadingList"][10]["QualifierName"][
                1
            ].attributes["MajorTopicYN"],
            "Y",
        )
        self.assertEqual(
            record[0]["PubmedData"]["History"][0][0].attributes["PubStatus"], "pubmed"
        )
        self.assertEqual(record[0]["PubmedData"]["History"][0][0]["Year"], "2001")
        self.assertEqual(record[0]["PubmedData"]["History"][0][0]["Month"], "12")
        self.assertEqual(record[0]["PubmedData"]["History"][0][0]["Day"], "26")
        self.assertEqual(record[0]["PubmedData"]["History"][0][0]["Hour"], "10")
        self.assertEqual(record[0]["PubmedData"]["History"][0][0]["Minute"], "0")
        self.assertEqual(
            record[0]["PubmedData"]["History"][0][1].attributes["PubStatus"], "medline"
        )
        self.assertEqual(record[0]["PubmedData"]["History"][0][1]["Year"], "2002")
        self.assertEqual(record[0]["PubmedData"]["History"][0][1]["Month"], "3")
        self.assertEqual(record[0]["PubmedData"]["History"][0][1]["Day"], "5")
        self.assertEqual(record[0]["PubmedData"]["History"][0][1]["Hour"], "10")
        self.assertEqual(record[0]["PubmedData"]["History"][0][1]["Minute"], "1")
        self.assertEqual(record[0]["PubmedData"]["PublicationStatus"], "ppublish")
        self.assertEqual(record[0]["PubmedData"]["ArticleIdList"][0], "11748933")
        self.assertEqual(
            record[0]["PubmedData"]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            record[0]["PubmedData"]["ArticleIdList"][1], "10.1006/cryo.2001.2328"
        )
        self.assertEqual(
            record[0]["PubmedData"]["ArticleIdList"][1].attributes["IdType"], "doi"
        )
        self.assertEqual(
            record[0]["PubmedData"]["ArticleIdList"][2], "S0011-2240(01)92328-4"
        )
        self.assertEqual(
            record[0]["PubmedData"]["ArticleIdList"][2].attributes["IdType"], "pii"
        )

        self.assertEqual(record[1]["MedlineCitation"].attributes["Owner"], "NLM")
        self.assertEqual(
            record[1]["MedlineCitation"].attributes["Status"], "PubMed-not-MEDLINE"
        )
        self.assertEqual(record[1]["MedlineCitation"]["PMID"], "11700088")
        self.assertEqual(record[1]["MedlineCitation"]["DateCreated"]["Year"], "2001")
        self.assertEqual(record[1]["MedlineCitation"]["DateCreated"]["Month"], "11")
        self.assertEqual(record[1]["MedlineCitation"]["DateCreated"]["Day"], "08")
        self.assertEqual(record[1]["MedlineCitation"]["DateCompleted"]["Year"], "2001")
        self.assertEqual(record[1]["MedlineCitation"]["DateCompleted"]["Month"], "12")
        self.assertEqual(record[1]["MedlineCitation"]["DateCompleted"]["Day"], "20")
        self.assertEqual(record[1]["MedlineCitation"]["DateRevised"]["Year"], "2003")
        self.assertEqual(record[1]["MedlineCitation"]["DateRevised"]["Month"], "10")
        self.assertEqual(record[1]["MedlineCitation"]["DateRevised"]["Day"], "31")
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"].attributes["PubModel"], "Print"
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["Journal"]["ISSN"], "1090-7807"
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["Journal"]["ISSN"].attributes[
                "IssnType"
            ],
            "Print",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["Journal"][
                "JournalIssue"
            ].attributes["CitedMedium"],
            "Print",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["Journal"]["JournalIssue"][
                "Volume"
            ],
            "153",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["Journal"]["JournalIssue"]["Issue"],
            "1",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["Journal"]["JournalIssue"][
                "PubDate"
            ]["Year"],
            "2001",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["Journal"]["JournalIssue"][
                "PubDate"
            ]["Month"],
            "Nov",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["Journal"]["Title"],
            "Journal of magnetic resonance (San Diego, Calif. : 1997)",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["Journal"]["ISOAbbreviation"],
            "J. Magn. Reson.",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["ArticleTitle"],
            "Proton MRI of (13)C distribution by J and chemical shift editing.",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["Pagination"]["MedlinePgn"],
            "117-23",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["Abstract"]["AbstractText"],
            "The sensitivity of (13)C NMR imaging can be considerably favored by detecting the (1)H nuclei bound to (13)C nuclei via scalar J-interaction (X-filter). However, the J-editing approaches have difficulty in discriminating between compounds with similar J-constant as, for example, different glucose metabolites. In such cases, it is almost impossible to get J-edited images of a single-compound distribution, since the various molecules are distinguishable only via their chemical shift. In a recent application of J-editing to high-resolution spectroscopy, it has been shown that a more efficient chemical selectivity could be obtained by utilizing the larger chemical shift range of (13)C. This has been made by introducing frequency-selective (13)C pulses that allow a great capability of indirect chemical separation. Here a double-resonance imaging approach is proposed, based on both J-editing and (13)C chemical shift editing, which achieves a powerful chemical selectivity and is able to produce full maps of specific chemical compounds. Results are presented on a multicompartments sample containing solutions of glucose and lactic and glutamic acid in water.",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["Abstract"]["CopyrightInformation"],
            "Copyright 2001 Academic Press.",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["Affiliation"],
            "INFM and Department of Physics, University of L'Aquila, I-67100 L'Aquila, Italy.",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"].attributes[
                "CompleteYN"
            ],
            "Y",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][0].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][0]["LastName"],
            "Casieri",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][0]["ForeName"], "C"
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][0]["Initials"], "C"
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][1].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][1]["LastName"],
            "Testa",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][1]["ForeName"], "C"
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][1]["Initials"], "C"
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][2].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][2]["LastName"],
            "Carpinelli",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][2]["ForeName"], "G"
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][2]["Initials"], "G"
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][3].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][3]["LastName"],
            "Canese",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][3]["ForeName"], "R"
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][3]["Initials"], "R"
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][4].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][4]["LastName"], "Podo"
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][4]["ForeName"], "F"
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][4]["Initials"], "F"
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][5].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][5]["LastName"],
            "De Luca",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][5]["ForeName"], "F"
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["AuthorList"][5]["Initials"], "F"
        )
        self.assertEqual(record[1]["MedlineCitation"]["Article"]["Language"], ["eng"])
        self.assertEqual(
            record[1]["MedlineCitation"]["Article"]["PublicationTypeList"][0],
            "Journal Article",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MedlineJournalInfo"]["Country"],
            "United States",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MedlineJournalInfo"]["MedlineTA"],
            "J Magn Reson",
        )
        self.assertEqual(
            record[1]["MedlineCitation"]["MedlineJournalInfo"]["NlmUniqueID"], "9707935"
        )
        self.assertEqual(
            record[1]["PubmedData"]["History"][0][0].attributes["PubStatus"], "pubmed"
        )
        self.assertEqual(record[1]["PubmedData"]["History"][0][0]["Year"], "2001")
        self.assertEqual(record[1]["PubmedData"]["History"][0][0]["Month"], "11")
        self.assertEqual(record[1]["PubmedData"]["History"][0][0]["Day"], "9")
        self.assertEqual(record[1]["PubmedData"]["History"][0][0]["Hour"], "10")
        self.assertEqual(record[1]["PubmedData"]["History"][0][0]["Minute"], "0")
        self.assertEqual(
            record[1]["PubmedData"]["History"][0][1].attributes["PubStatus"], "medline"
        )
        self.assertEqual(record[1]["PubmedData"]["History"][0][1]["Year"], "2001")
        self.assertEqual(record[1]["PubmedData"]["History"][0][1]["Month"], "11")
        self.assertEqual(record[1]["PubmedData"]["History"][0][1]["Day"], "9")
        self.assertEqual(record[1]["PubmedData"]["History"][0][1]["Hour"], "10")
        self.assertEqual(record[1]["PubmedData"]["History"][0][1]["Minute"], "1")
        self.assertEqual(record[1]["PubmedData"]["PublicationStatus"], "ppublish")
        self.assertEqual(record[1]["PubmedData"]["ArticleIdList"][0], "11700088")
        self.assertEqual(
            record[1]["PubmedData"]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            record[1]["PubmedData"]["ArticleIdList"][1], "10.1006/jmre.2001.2429"
        )
        self.assertEqual(
            record[1]["PubmedData"]["ArticleIdList"][1].attributes["IdType"], "doi"
        )
        self.assertEqual(
            record[1]["PubmedData"]["ArticleIdList"][2], "S1090-7807(01)92429-2"
        )
        self.assertEqual(
            record[1]["PubmedData"]["ArticleIdList"][2].attributes["IdType"], "pii"
        )

    def test_pubmed_html_tags(self):
        """Test parsing XML returned by EFetch, PubMed database with HTML tags."""
        # In PubMed display PMIDs in xml retrieval mode.
        # To create the XML file, use
        # >>> Bio.Entrez.efetch(db='pubmed', retmode='xml', id='29106400')
        with open("Entrez/pubmed4.xml", "rb") as stream:
            records = Entrez.read(stream)
        self.assertEqual(len(records), 2)
        self.assertEqual(len(records["PubmedBookArticle"]), 0)
        self.assertEqual(len(records["PubmedArticle"]), 1)
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"].attributes["Status"],
            "MEDLINE",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"].attributes["Owner"], "NLM"
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["PMID"], "27797938"
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["PMID"].attributes[
                "Version"
            ],
            "1",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["DateCompleted"]["Year"],
            "2017",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["DateCompleted"]["Month"],
            "08",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["DateCompleted"]["Day"], "03"
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["DateRevised"]["Year"],
            "2018",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["DateRevised"]["Month"], "04"
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["DateRevised"]["Day"], "17"
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"].attributes[
                "PubModel"
            ],
            "Print-Electronic",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"]["Journal"][
                "ISSN"
            ],
            "1468-3288",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"]["Journal"][
                "ISSN"
            ].attributes["IssnType"],
            "Electronic",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"]["Journal"][
                "JournalIssue"
            ].attributes["CitedMedium"],
            "Internet",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"]["Journal"][
                "JournalIssue"
            ]["Volume"],
            "66",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"]["Journal"][
                "JournalIssue"
            ]["Issue"],
            "6",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"]["Journal"][
                "JournalIssue"
            ]["PubDate"]["Year"],
            "2017",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"]["Journal"][
                "JournalIssue"
            ]["PubDate"]["Month"],
            "06",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"]["Journal"][
                "Title"
            ],
            "Gut",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"]["Journal"][
                "ISOAbbreviation"
            ],
            "Gut",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"]["ArticleTitle"],
            "Leucocyte telomere length, genetic variants at the <i>TERT</i> gene region and risk of pancreatic cancer.",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"]["Pagination"][
                "MedlinePgn"
            ],
            "1116-1122",
        )
        self.assertEqual(
            len(
                records["PubmedArticle"][0]["MedlineCitation"]["Article"]["ELocationID"]
            ),
            1,
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"]["ELocationID"][0],
            "10.1136/gutjnl-2016-312510",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"]["ELocationID"][
                0
            ].attributes["EIdType"],
            "doi",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"]["ELocationID"][
                0
            ].attributes["ValidYN"],
            "Y",
        )
        self.assertEqual(
            len(records["PubmedArticle"][0]["MedlineCitation"]["Article"]["Abstract"]),
            2,
        )
        self.assertEqual(
            len(
                records["PubmedArticle"][0]["MedlineCitation"]["Article"]["Abstract"][
                    "AbstractText"
                ]
            ),
            4,
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"]["Abstract"][
                "AbstractText"
            ][0],
            "Telomere shortening occurs as an early event in pancreatic tumorigenesis, and genetic variants at the telomerase reverse transcriptase (<i>TERT</i>) gene region have been associated with pancreatic cancer risk. However, it is unknown whether prediagnostic leucocyte telomere length is associated with subsequent risk of pancreatic cancer.",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"]["Abstract"][
                "AbstractText"
            ][0].attributes["Label"],
            "OBJECTIVE",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"]["Abstract"][
                "AbstractText"
            ][1],
            "We measured prediagnostic leucocyte telomere length in 386 pancreatic cancer cases and 896 matched controls from five prospective US cohorts. ORs and 95% CIs were calculated using conditional logistic regression. Matching factors included year of birth, cohort (which also matches on sex), smoking status, fasting status and month/year of blood collection. We additionally examined single-nucleotide polymorphisms (SNPs) at the <i>TERT</i> region in relation to pancreatic cancer risk and leucocyte telomere length using logistic and linear regression, respectively.",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"]["Abstract"][
                "AbstractText"
            ][1].attributes["Label"],
            "DESIGN",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"]["Abstract"][
                "AbstractText"
            ][2],
            "Shorter prediagnostic leucocyte telomere length was associated with higher risk of pancreatic cancer (comparing extreme quintiles of telomere length, OR 1.72; 95% CI 1.07 to 2.78; p<sub>trend</sub>=0.048). Results remained unchanged after adjustment for diabetes, body mass index and physical activity. Three SNPs at <i>TERT</i> (linkage disequilibrium r<sup>2</sup><0.25) were associated with pancreatic cancer risk, including rs401681 (per minor allele OR 1.33; 95% CI 1.12 to 1.59; p=0.002), rs2736100 (per minor allele OR 1.36; 95% CI 1.13 to 1.63; p=0.001) and rs2736098 (per minor allele OR 0.75; 95% CI 0.63 to 0.90; p=0.002). The minor allele for rs401681 was associated with shorter telomere length (p=0.023).",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"]["Abstract"][
                "AbstractText"
            ][2].attributes["Label"],
            "RESULTS",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"]["Abstract"][
                "AbstractText"
            ][3],
            "Prediagnostic leucocyte telomere length and genetic variants at the <i>TERT</i> gene region were associated with risk of pancreatic cancer.",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"]["Abstract"][
                "AbstractText"
            ][3].attributes["Label"],
            "CONCLUSIONS",
        )
        self.assertEqual(
            len(
                records["PubmedArticle"][0]["MedlineCitation"]["Article"]["AuthorList"]
            ),
            22,
        )
        self.assertEqual(
            len(records["PubmedArticle"][0]["MedlineCitation"]["Article"]["GrantList"]),
            35,
        )
        self.assertEqual(
            len(
                records["PubmedArticle"][0]["MedlineCitation"]["Article"][
                    "PublicationTypeList"
                ]
            ),
            5,
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"][
                "PublicationTypeList"
            ][0],
            "Journal Article",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"][
                "PublicationTypeList"
            ][0].attributes["UI"],
            "D016428",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"][
                "PublicationTypeList"
            ][1],
            "Observational Study",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"][
                "PublicationTypeList"
            ][1].attributes["UI"],
            "D064888",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"][
                "PublicationTypeList"
            ][2],
            "Research Support, N.I.H., Extramural",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"][
                "PublicationTypeList"
            ][2].attributes["UI"],
            "D052061",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"][
                "PublicationTypeList"
            ][3],
            "Research Support, U.S. Gov't, Non-P.H.S.",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"][
                "PublicationTypeList"
            ][3].attributes["UI"],
            "D013486",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"][
                "PublicationTypeList"
            ][4],
            "Research Support, Non-U.S. Gov't",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"][
                "PublicationTypeList"
            ][4].attributes["UI"],
            "D013485",
        )
        self.assertEqual(
            len(
                records["PubmedArticle"][0]["MedlineCitation"]["Article"]["ArticleDate"]
            ),
            1,
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"]["ArticleDate"][
                0
            ].attributes["DateType"],
            "Electronic",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"]["ArticleDate"][0][
                "Year"
            ],
            "2016",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"]["ArticleDate"][0][
                "Month"
            ],
            "10",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["Article"]["ArticleDate"][0][
                "Day"
            ],
            "21",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["MedlineJournalInfo"][
                "Country"
            ],
            "England",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["MedlineJournalInfo"][
                "MedlineTA"
            ],
            "Gut",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["MedlineJournalInfo"][
                "NlmUniqueID"
            ],
            "2985108R",
        )
        self.assertEqual(
            records["PubmedArticle"][0]["MedlineCitation"]["MedlineJournalInfo"][
                "ISSNLinking"
            ],
            "0017-5749",
        )
        self.assertEqual(
            len(records["PubmedArticle"][0]["MedlineCitation"]["ChemicalList"]), 2
        )

    def test_pubmed_html_escaping(self):
        """Test parsing XML returned by EFetch, PubMed database with HTML tags and HTML escape characters."""
        # In PubMed display PMIDs in xml retrieval mode.
        # To create the XML file, use
        # >>> Bio.Entrez.efetch(db='pubmed', retmode='xml', id='28775130')
        with open("Entrez/pubmed5.xml", "rb") as stream:
            record = Entrez.read(stream, escape=True)
        self.assertEqual(len(record), 2)
        self.assertEqual(len(record["PubmedArticle"]), 1)
        self.assertEqual(len(record["PubmedBookArticle"]), 0)
        article = record["PubmedArticle"][0]
        self.assertEqual(len(article), 2)
        self.assertEqual(len(article["PubmedData"]), 3)
        self.assertEqual(len(article["PubmedData"]["ArticleIdList"]), 5)
        self.assertEqual(article["PubmedData"]["ArticleIdList"][0], "28775130")
        self.assertEqual(
            article["PubmedData"]["ArticleIdList"][0].attributes, {"IdType": "pubmed"}
        )
        self.assertEqual(article["PubmedData"]["ArticleIdList"][1], "oemed-2017-104431")
        self.assertEqual(
            article["PubmedData"]["ArticleIdList"][1].attributes, {"IdType": "pii"}
        )
        self.assertEqual(
            article["PubmedData"]["ArticleIdList"][2], "10.1136/oemed-2017-104431"
        )
        self.assertEqual(
            article["PubmedData"]["ArticleIdList"][2].attributes, {"IdType": "doi"}
        )
        self.assertEqual(article["PubmedData"]["ArticleIdList"][3], "PMC5771820")
        self.assertEqual(
            article["PubmedData"]["ArticleIdList"][3].attributes, {"IdType": "pmc"}
        )
        self.assertEqual(article["PubmedData"]["ArticleIdList"][4], "NIHMS932407")
        self.assertEqual(
            article["PubmedData"]["ArticleIdList"][4].attributes, {"IdType": "mid"}
        )
        self.assertEqual(article["PubmedData"]["PublicationStatus"], "ppublish")
        self.assertEqual(len(article["PubmedData"]["History"]), 7)
        self.assertEqual(len(article["PubmedData"]["History"][0]), 3)
        self.assertEqual(article["PubmedData"]["History"][0]["Year"], "2017")
        self.assertEqual(article["PubmedData"]["History"][0]["Month"], "03")
        self.assertEqual(article["PubmedData"]["History"][0]["Day"], "10")
        self.assertEqual(
            article["PubmedData"]["History"][0].attributes, {"PubStatus": "received"}
        )
        self.assertEqual(len(article["PubmedData"]["History"][1]), 3)
        self.assertEqual(article["PubmedData"]["History"][1]["Year"], "2017")
        self.assertEqual(article["PubmedData"]["History"][1]["Month"], "06")
        self.assertEqual(article["PubmedData"]["History"][1]["Day"], "13")
        self.assertEqual(
            article["PubmedData"]["History"][1].attributes, {"PubStatus": "revised"}
        )
        self.assertEqual(len(article["PubmedData"]["History"][2]), 3)
        self.assertEqual(article["PubmedData"]["History"][2]["Year"], "2017")
        self.assertEqual(article["PubmedData"]["History"][2]["Month"], "06")
        self.assertEqual(article["PubmedData"]["History"][2]["Day"], "22")
        self.assertEqual(
            article["PubmedData"]["History"][2].attributes, {"PubStatus": "accepted"}
        )
        self.assertEqual(len(article["PubmedData"]["History"][3]), 3)
        self.assertEqual(article["PubmedData"]["History"][3]["Year"], "2019")
        self.assertEqual(article["PubmedData"]["History"][3]["Month"], "02")
        self.assertEqual(article["PubmedData"]["History"][3]["Day"], "01")
        self.assertEqual(
            article["PubmedData"]["History"][3].attributes, {"PubStatus": "pmc-release"}
        )
        self.assertEqual(len(article["PubmedData"]["History"][4]), 5)
        self.assertEqual(article["PubmedData"]["History"][4]["Year"], "2017")
        self.assertEqual(article["PubmedData"]["History"][4]["Month"], "8")
        self.assertEqual(article["PubmedData"]["History"][4]["Day"], "5")
        self.assertEqual(article["PubmedData"]["History"][4]["Hour"], "6")
        self.assertEqual(article["PubmedData"]["History"][4]["Minute"], "0")
        self.assertEqual(
            article["PubmedData"]["History"][4].attributes, {"PubStatus": "pubmed"}
        )
        self.assertEqual(len(article["PubmedData"]["History"][5]), 5)
        self.assertEqual(article["PubmedData"]["History"][5]["Year"], "2017")
        self.assertEqual(article["PubmedData"]["History"][5]["Month"], "8")
        self.assertEqual(article["PubmedData"]["History"][5]["Day"], "5")
        self.assertEqual(article["PubmedData"]["History"][5]["Hour"], "6")
        self.assertEqual(article["PubmedData"]["History"][5]["Minute"], "0")
        self.assertEqual(
            article["PubmedData"]["History"][5].attributes, {"PubStatus": "medline"}
        )
        self.assertEqual(len(article["PubmedData"]["History"][6]), 5)
        self.assertEqual(article["PubmedData"]["History"][6]["Year"], "2017")
        self.assertEqual(article["PubmedData"]["History"][6]["Month"], "8")
        self.assertEqual(article["PubmedData"]["History"][6]["Day"], "5")
        self.assertEqual(article["PubmedData"]["History"][6]["Hour"], "6")
        self.assertEqual(article["PubmedData"]["History"][6]["Minute"], "0")
        self.assertEqual(
            article["PubmedData"]["History"][6].attributes, {"PubStatus": "entrez"}
        )
        self.assertEqual(len(article["MedlineCitation"]), 12)
        self.assertEqual(len(article["MedlineCitation"]["CitationSubset"]), 0)
        self.assertEqual(
            article["MedlineCitation"]["CoiStatement"],
            "Competing interests: None declared.",
        )
        self.assertEqual(len(article["MedlineCitation"]["CommentsCorrectionsList"]), 40)
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][0]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][0]["RefSource"],
            "J Toxicol Environ Health A. 2003 Jun 13;66(11):965-86",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][0]["PMID"], "12775511"
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][0].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][1]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][1]["RefSource"],
            "Ann Intern Med. 2015 May 5;162(9):641-50",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][1]["PMID"], "25798805"
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][1].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][2]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][2]["RefSource"],
            "Cancer Causes Control. 1999 Dec;10(6):583-95",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][2]["PMID"], "10616827"
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][2].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][3]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][3]["RefSource"],
            "Thyroid. 2010 Jul;20(7):755-61",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][3]["PMID"], "20578899"
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][3].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][4]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][4]["RefSource"],
            "Environ Health Perspect. 1999 Mar;107(3):205-11",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][4]["PMID"], "10064550"
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][4].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][5]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][5]["RefSource"],
            "J Clin Endocrinol Metab. 2006 Nov;91(11):4295-301",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][5]["PMID"], "16868053"
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][5].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][6]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][6]["RefSource"],
            "Endocrinology. 1998 Oct;139(10):4252-63",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][6]["PMID"], "9751507"
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][6].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][7]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][7]["RefSource"],
            "Eur J Endocrinol. 2016 Apr;174(4):409-14",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][7]["PMID"], "26863886"
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][7].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][8]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][8]["RefSource"],
            "Eur J Endocrinol. 2000 Nov;143(5):639-47",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][8]["PMID"], "11078988"
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][8].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][9]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][9]["RefSource"],
            "Environ Res. 2016 Nov;151:389-398",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][9]["PMID"], "27540871"
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][9].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][10]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][10]["RefSource"],
            "Am J Epidemiol. 2010 Jan 15;171(2):242-52",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][10]["PMID"],
            "19951937",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][10].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][11]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][11]["RefSource"],
            "Thyroid. 1998 Sep;8(9):827-56",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][11]["PMID"], "9777756"
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][11].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][12]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][12]["RefSource"],
            "Curr Opin Pharmacol. 2001 Dec;1(6):626-31",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][12]["PMID"],
            "11757819",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][12].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][13]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][13]["RefSource"],
            "Breast Cancer Res Treat. 2012 Jun;133(3):1169-77",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][13]["PMID"],
            "22434524",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][13].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][14]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][14]["RefSource"],
            "Int J Environ Res Public Health. 2011 Dec;8(12 ):4608-22",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][14]["PMID"],
            "22408592",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][14].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][15]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][15]["RefSource"],
            "Ann Oncol. 2014 Oct;25(10):2025-30",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][15]["PMID"],
            "25081899",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][15].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][16]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][16]["RefSource"],
            "Environ Health. 2006 Dec 06;5:32",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][16]["PMID"],
            "17147831",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][16].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][17]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][17]["RefSource"],
            "Environ Health Perspect. 1998 Aug;106(8):437-45",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][17]["PMID"], "9681970"
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][17].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][18]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][18]["RefSource"],
            "Arch Intern Med. 2000 Feb 28;160(4):526-34",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][18]["PMID"],
            "10695693",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][18].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][19]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][19]["RefSource"],
            "Endocrine. 2011 Jun;39(3):259-65",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][19]["PMID"],
            "21161440",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][19].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][20]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][20]["RefSource"],
            "Cancer Epidemiol Biomarkers Prev. 2008 Aug;17(8):1880-3",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][20]["PMID"],
            "18708375",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][20].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][21]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][21]["RefSource"],
            "Am J Epidemiol. 2010 Feb 15;171(4):455-64",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][21]["PMID"],
            "20061368",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][21].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][22]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][22]["RefSource"],
            "J Clin Endocrinol Metab. 2002 Feb;87(2):489-99",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][22]["PMID"],
            "11836274",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][22].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][23]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][23]["RefSource"],
            "J Toxicol Environ Health A. 2015 ;78(21-22):1338-47",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][23]["PMID"],
            "26555155",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][23].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][24]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][24]["RefSource"],
            "Toxicol Sci. 2002 Jun;67(2):207-18",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][24]["PMID"],
            "12011480",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][24].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][25]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][25]["RefSource"],
            "Natl Cancer Inst Carcinog Tech Rep Ser. 1978;21:1-184",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][25]["PMID"],
            "12844187",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][25].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][26]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][26]["RefSource"],
            "Environ Res. 2013 Nov;127:7-15",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][26]["PMID"],
            "24183346",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][26].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][27]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][27]["RefSource"],
            "JAMA. 2004 Jan 14;291(2):228-38",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][27]["PMID"],
            "14722150",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][27].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][28]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][28]["RefSource"],
            "J Expo Sci Environ Epidemiol. 2010 Sep;20(6):559-69",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][28]["PMID"],
            "19888312",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][28].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][29]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][29]["RefSource"],
            "Environ Health Perspect. 1996 Apr;104(4):362-9",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][29]["PMID"], "8732939"
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][29].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][30]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][30]["RefSource"],
            "Lancet. 2012 Mar 24;379(9821):1142-54",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][30]["PMID"],
            "22273398",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][30].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][31]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][31]["RefSource"],
            "JAMA. 1995 Mar 8;273(10):808-12",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][31]["PMID"], "7532241"
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][31].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][32]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][32]["RefSource"],
            "Sci Total Environ. 2002 Aug 5;295(1-3):207-15",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][32]["PMID"],
            "12186288",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][32].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][33]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][33]["RefSource"],
            "Eur J Endocrinol. 2006 May;154(5):599-611",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][33]["PMID"],
            "16645005",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][33].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][34]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][34]["RefSource"],
            "J Occup Environ Med. 2013 Oct;55(10):1171-8",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][34]["PMID"],
            "24064777",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][34].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][35]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][35]["RefSource"],
            "Thyroid. 2007 Sep;17(9):811-7",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][35]["PMID"],
            "17956155",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][35].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][36]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][36]["RefSource"],
            "Rev Environ Contam Toxicol. 1991;120:1-82",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][36]["PMID"], "1899728"
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][36].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][37]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][37]["RefSource"],
            "Environ Health Perspect. 1997 Oct;105(10):1126-30",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][37]["PMID"], "9349837"
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][37].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][38]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][38]["RefSource"],
            "J Biochem Mol Toxicol. 2005;19(3):175",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][38]["PMID"],
            "15977190",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][38].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(
            len(article["MedlineCitation"]["CommentsCorrectionsList"][39]), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][39]["RefSource"],
            "Immunogenetics. 2002 Jun;54(3):141-57",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][39]["PMID"],
            "12073143",
        )
        self.assertEqual(
            article["MedlineCitation"]["CommentsCorrectionsList"][39].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(article["MedlineCitation"]["DateRevised"]["Year"], "2018")
        self.assertEqual(article["MedlineCitation"]["DateRevised"]["Month"], "04")
        self.assertEqual(article["MedlineCitation"]["DateRevised"]["Day"], "25")
        self.assertEqual(len(article["MedlineCitation"]["DateRevised"].attributes), 0)
        self.assertEqual(len(article["MedlineCitation"]["GeneralNote"]), 0)
        self.assertEqual(len(article["MedlineCitation"]["KeywordList"]), 1)
        self.assertEqual(len(article["MedlineCitation"]["KeywordList"][0]), 5)
        self.assertEqual(article["MedlineCitation"]["KeywordList"][0][0], "agriculture")
        self.assertEqual(
            article["MedlineCitation"]["KeywordList"][0][0].attributes,
            {"MajorTopicYN": "N"},
        )
        self.assertEqual(
            article["MedlineCitation"]["KeywordList"][0][1], "hypothyroidism"
        )
        self.assertEqual(
            article["MedlineCitation"]["KeywordList"][0][1].attributes,
            {"MajorTopicYN": "N"},
        )
        self.assertEqual(article["MedlineCitation"]["KeywordList"][0][2], "pesticides")
        self.assertEqual(
            article["MedlineCitation"]["KeywordList"][0][2].attributes,
            {"MajorTopicYN": "N"},
        )
        self.assertEqual(
            article["MedlineCitation"]["KeywordList"][0][3], "thyroid disease"
        )
        self.assertEqual(
            article["MedlineCitation"]["KeywordList"][0][3].attributes,
            {"MajorTopicYN": "N"},
        )
        self.assertEqual(
            article["MedlineCitation"]["KeywordList"][0][4],
            "thyroid stimulating hormone",
        )
        self.assertEqual(
            article["MedlineCitation"]["KeywordList"][0][4].attributes,
            {"MajorTopicYN": "N"},
        )
        self.assertEqual(len(article["MedlineCitation"]["MedlineJournalInfo"]), 4)
        self.assertEqual(
            article["MedlineCitation"]["MedlineJournalInfo"]["MedlineTA"],
            "Occup Environ Med",
        )
        self.assertEqual(
            article["MedlineCitation"]["MedlineJournalInfo"]["Country"], "England"
        )
        self.assertEqual(
            article["MedlineCitation"]["MedlineJournalInfo"]["NlmUniqueID"], "9422759"
        )
        self.assertEqual(
            article["MedlineCitation"]["MedlineJournalInfo"]["ISSNLinking"], "1351-0711"
        )
        self.assertEqual(
            len(article["MedlineCitation"]["MedlineJournalInfo"].attributes), 0
        )
        self.assertEqual(len(article["MedlineCitation"]["OtherAbstract"]), 0)
        self.assertEqual(len(article["MedlineCitation"]["OtherID"]), 0)
        self.assertEqual(article["MedlineCitation"]["PMID"], "28775130")
        self.assertEqual(len(article["MedlineCitation"]["SpaceFlightMission"]), 0)
        self.assertEqual(len(article["MedlineCitation"]["Article"]["ArticleDate"]), 1)
        self.assertEqual(
            len(article["MedlineCitation"]["Article"]["ArticleDate"][0]), 3
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["ArticleDate"][0]["Month"], "08"
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["ArticleDate"][0]["Day"], "03"
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["ArticleDate"][0]["Year"], "2017"
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["ArticleDate"][0].attributes,
            {"DateType": "Electronic"},
        )
        self.assertEqual(len(article["MedlineCitation"]["Article"]["Pagination"]), 1)
        self.assertEqual(
            article["MedlineCitation"]["Article"]["Pagination"]["MedlinePgn"], "79-89"
        )
        self.assertEqual(
            len(article["MedlineCitation"]["Article"]["Pagination"].attributes), 0
        )
        self.assertEqual(len(article["MedlineCitation"]["Article"]["AuthorList"]), 12)
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][0]["LastName"], "Lerro"
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][0]["Initials"], "CC"
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][0]["Identifier"], []
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["AuthorList"][0][
                    "AffiliationInfo"
                ]
            ),
            1,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][0]["AffiliationInfo"][
                0
            ]["Affiliation"],
            "Division of Cancer Epidemiology and Genetics, National Cancer Institute, Rockville, Maryland, USA.",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][0]["AffiliationInfo"][
                0
            ]["Identifier"],
            [],
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["AuthorList"][0][
                    "AffiliationInfo"
                ][0].attributes
            ),
            0,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][0]["ForeName"],
            "Catherine C",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][0].attributes,
            {"ValidYN": "Y"},
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][1]["LastName"],
            "Beane Freeman",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][1]["Initials"], "LE"
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][1]["Identifier"], []
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["AuthorList"][1][
                    "AffiliationInfo"
                ]
            ),
            1,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][1]["AffiliationInfo"][
                0
            ]["Affiliation"],
            "Division of Cancer Epidemiology and Genetics, National Cancer Institute, Rockville, Maryland, USA.",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][1]["AffiliationInfo"][
                0
            ]["Identifier"],
            [],
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["AuthorList"][1][
                    "AffiliationInfo"
                ][0].attributes
            ),
            0,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][1]["ForeName"],
            "Laura E",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][1].attributes,
            {"ValidYN": "Y"},
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][2]["LastName"],
            "DellaValle",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][2]["Initials"], "CT"
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][2]["Identifier"], []
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["AuthorList"][2][
                    "AffiliationInfo"
                ]
            ),
            2,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][2]["AffiliationInfo"][
                0
            ]["Affiliation"],
            "Division of Cancer Epidemiology and Genetics, National Cancer Institute, Rockville, Maryland, USA.",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][2]["AffiliationInfo"][
                0
            ]["Identifier"],
            [],
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["AuthorList"][2][
                    "AffiliationInfo"
                ][0].attributes
            ),
            0,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][2]["AffiliationInfo"][
                1
            ]["Affiliation"],
            "Environmental Working Group, Washington, DC, USA.",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][2]["AffiliationInfo"][
                1
            ]["Identifier"],
            [],
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["AuthorList"][2][
                    "AffiliationInfo"
                ][1].attributes
            ),
            0,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][2]["ForeName"], "Curt T"
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][2].attributes,
            {"ValidYN": "Y"},
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][3]["LastName"],
            "Kibriya",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][3]["Initials"], "MG"
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][3]["Identifier"], []
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["AuthorList"][3][
                    "AffiliationInfo"
                ]
            ),
            1,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][3]["AffiliationInfo"][
                0
            ]["Affiliation"],
            "Department of Public Health Sciences, The University of Chicago, Chicago, Illinois, USA.",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][3]["AffiliationInfo"][
                0
            ]["Identifier"],
            [],
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["AuthorList"][3][
                    "AffiliationInfo"
                ][0].attributes
            ),
            0,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][3]["ForeName"],
            "Muhammad G",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][3].attributes,
            {"ValidYN": "Y"},
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][4]["LastName"],
            "Aschebrook-Kilfoy",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][4]["Initials"], "B"
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][4]["Identifier"], []
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["AuthorList"][4][
                    "AffiliationInfo"
                ]
            ),
            1,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][4]["AffiliationInfo"][
                0
            ]["Affiliation"],
            "Department of Public Health Sciences, The University of Chicago, Chicago, Illinois, USA.",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][4]["AffiliationInfo"][
                0
            ]["Identifier"],
            [],
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["AuthorList"][4][
                    "AffiliationInfo"
                ][0].attributes
            ),
            0,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][4]["ForeName"],
            "Briseis",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][4].attributes,
            {"ValidYN": "Y"},
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][5]["LastName"],
            "Jasmine",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][5]["Initials"], "F"
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][5]["Identifier"], []
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["AuthorList"][5][
                    "AffiliationInfo"
                ]
            ),
            1,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][5]["AffiliationInfo"][
                0
            ]["Affiliation"],
            "Department of Public Health Sciences, The University of Chicago, Chicago, Illinois, USA.",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][5]["AffiliationInfo"][
                0
            ]["Identifier"],
            [],
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["AuthorList"][5][
                    "AffiliationInfo"
                ][0].attributes
            ),
            0,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][5]["ForeName"],
            "Farzana",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][5].attributes,
            {"ValidYN": "Y"},
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][6]["LastName"],
            "Koutros",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][6]["Initials"], "S"
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][6]["Identifier"], []
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["AuthorList"][6][
                    "AffiliationInfo"
                ]
            ),
            1,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][6]["AffiliationInfo"][
                0
            ]["Affiliation"],
            "Division of Cancer Epidemiology and Genetics, National Cancer Institute, Rockville, Maryland, USA.",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][6]["AffiliationInfo"][
                0
            ]["Identifier"],
            [],
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["AuthorList"][6][
                    "AffiliationInfo"
                ][0].attributes
            ),
            0,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][6]["ForeName"], "Stella"
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][6].attributes,
            {"ValidYN": "Y"},
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][7]["LastName"], "Parks"
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][7]["Initials"], "CG"
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][7]["Identifier"], []
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["AuthorList"][7][
                    "AffiliationInfo"
                ]
            ),
            1,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][7]["AffiliationInfo"][
                0
            ]["Affiliation"],
            "National Institute of Environmental Health Sciences, Research Triangle Park, North Carolina, USA.",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][7]["AffiliationInfo"][
                0
            ]["Identifier"],
            [],
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["AuthorList"][7][
                    "AffiliationInfo"
                ][0].attributes
            ),
            0,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][7]["ForeName"],
            "Christine G",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][7].attributes,
            {"ValidYN": "Y"},
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][8]["LastName"],
            "Sandler",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][8]["Initials"], "DP"
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][8]["Identifier"], []
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["AuthorList"][8][
                    "AffiliationInfo"
                ]
            ),
            1,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][8]["AffiliationInfo"][
                0
            ]["Affiliation"],
            "National Institute of Environmental Health Sciences, Research Triangle Park, North Carolina, USA.",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][8]["AffiliationInfo"][
                0
            ]["Identifier"],
            [],
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["AuthorList"][8][
                    "AffiliationInfo"
                ][0].attributes
            ),
            0,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][8]["ForeName"], "Dale P"
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][8].attributes,
            {"ValidYN": "Y"},
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][9]["LastName"],
            "Alavanja",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][9]["Initials"], "MCR"
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][9]["Identifier"], []
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["AuthorList"][9][
                    "AffiliationInfo"
                ]
            ),
            2,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][9]["AffiliationInfo"][
                0
            ]["Affiliation"],
            "Division of Cancer Epidemiology and Genetics, National Cancer Institute, Rockville, Maryland, USA.",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][9]["AffiliationInfo"][
                0
            ]["Identifier"],
            [],
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["AuthorList"][9][
                    "AffiliationInfo"
                ][0].attributes
            ),
            0,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][9]["AffiliationInfo"][
                1
            ]["Affiliation"],
            "Department of Biology, Hood College, Frederick, Maryland, USA.",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][9]["AffiliationInfo"][
                1
            ]["Identifier"],
            [],
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["AuthorList"][9][
                    "AffiliationInfo"
                ][1].attributes
            ),
            0,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][9]["ForeName"],
            "Michael C R",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][9].attributes,
            {"ValidYN": "Y"},
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][10]["LastName"],
            "Hofmann",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][10]["Initials"], "JN"
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][10]["Identifier"], []
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["AuthorList"][10][
                    "AffiliationInfo"
                ]
            ),
            1,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][10]["AffiliationInfo"][
                0
            ]["Affiliation"],
            "Division of Cancer Epidemiology and Genetics, National Cancer Institute, Rockville, Maryland, USA.",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][10]["AffiliationInfo"][
                0
            ]["Identifier"],
            [],
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["AuthorList"][10][
                    "AffiliationInfo"
                ][0].attributes
            ),
            0,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][10]["ForeName"],
            "Jonathan N",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][10].attributes,
            {"ValidYN": "Y"},
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][11]["LastName"], "Ward"
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][11]["Initials"], "MH"
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][11]["Identifier"], []
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["AuthorList"][11][
                    "AffiliationInfo"
                ]
            ),
            1,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][11]["AffiliationInfo"][
                0
            ]["Affiliation"],
            "Division of Cancer Epidemiology and Genetics, National Cancer Institute, Rockville, Maryland, USA.",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][11]["AffiliationInfo"][
                0
            ]["Identifier"],
            [],
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["AuthorList"][11][
                    "AffiliationInfo"
                ][0].attributes
            ),
            0,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][11]["ForeName"],
            "Mary H",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["AuthorList"][11].attributes,
            {"ValidYN": "Y"},
        )
        self.assertEqual(len(article["MedlineCitation"]["Article"]["Language"]), 1)
        self.assertEqual(article["MedlineCitation"]["Article"]["Language"][0], "eng")
        self.assertEqual(
            len(article["MedlineCitation"]["Article"]["PublicationTypeList"]), 1
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["PublicationTypeList"][0],
            "Journal Article",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["PublicationTypeList"][0].attributes,
            {"UI": "D016428"},
        )
        self.assertEqual(len(article["MedlineCitation"]["Article"]["Journal"]), 4)
        self.assertEqual(
            article["MedlineCitation"]["Article"]["Journal"]["ISSN"], "1470-7926"
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["Journal"]["ISSN"].attributes,
            {"IssnType": "Electronic"},
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["Journal"]["ISOAbbreviation"],
            "Occup Environ Med",
        )
        self.assertEqual(
            len(article["MedlineCitation"]["Article"]["Journal"]["JournalIssue"]), 3
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["Journal"]["JournalIssue"]["Volume"],
            "75",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["Journal"]["JournalIssue"]["Issue"],
            "2",
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["Journal"]["JournalIssue"][
                    "PubDate"
                ]
            ),
            2,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["Journal"]["JournalIssue"]["PubDate"][
                "Month"
            ],
            "Feb",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["Journal"]["JournalIssue"]["PubDate"][
                "Year"
            ],
            "2018",
        )
        self.assertEqual(
            len(
                article["MedlineCitation"]["Article"]["Journal"]["JournalIssue"][
                    "PubDate"
                ].attributes
            ),
            0,
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["Journal"]["JournalIssue"].attributes,
            {"CitedMedium": "Internet"},
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["Journal"]["Title"],
            "Occupational and environmental medicine",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["Journal"]["ISSN"].attributes,
            {"IssnType": "Electronic"},
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["ArticleTitle"],
            "Occupational pesticide exposure and subclinical hypothyroidism among male pesticide applicators.",
        )
        self.assertEqual(len(article["MedlineCitation"]["Article"]["ELocationID"]), 1)
        self.assertEqual(
            article["MedlineCitation"]["Article"]["ELocationID"][0],
            "10.1136/oemed-2017-104431",
        )
        self.assertEqual(
            len(article["MedlineCitation"]["Article"]["ELocationID"][0].attributes), 2
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["ELocationID"][0].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["ELocationID"][0].attributes[
                "EIdType"
            ],
            "doi",
        )
        self.assertEqual(
            len(article["MedlineCitation"]["Article"]["Abstract"]["AbstractText"]), 4
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["Abstract"]["AbstractText"][0],
            "Animal studies suggest that exposure to pesticides may alter thyroid function; however, few epidemiologic studies have examined this association. We evaluated the relationship between individual pesticides and thyroid function in 679 men enrolled in a substudy of the Agricultural Health Study, a cohort of licensed pesticide applicators.",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["Abstract"]["AbstractText"][
                0
            ].attributes,
            {"NlmCategory": "OBJECTIVE", "Label": "OBJECTIVES"},
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["Abstract"]["AbstractText"][1],
            "Self-reported lifetime pesticide use was obtained at cohort enrolment (1993-1997). Intensity-weighted lifetime days were computed for 33 pesticides, which adjusts cumulative days of pesticide use for factors that modify exposure (eg, use of personal protective equipment). Thyroid-stimulating hormone (TSH), thyroxine (T4), triiodothyronine (T3) and antithyroid peroxidase (anti-TPO) autoantibodies were measured in serum collected in 2010-2013. We used multivariate logistic regression to estimate ORs and 95% CIs for subclinical hypothyroidism (TSH &gt;4.5 mIU/L) compared with normal TSH (0.4-<u>&lt;</u>4.5 mIU/L) and for anti-TPO positivity. We also examined pesticide associations with TSH, T4 and T3 in multivariate linear regression models.",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["Abstract"]["AbstractText"][
                1
            ].attributes,
            {"NlmCategory": "METHODS", "Label": "METHODS"},
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["Abstract"]["AbstractText"][2],
            "Higher exposure to the insecticide aldrin (third and fourth quartiles of intensity-weighted days vs no exposure) was positively associated with subclinical hypothyroidism (OR<sub>Q3</sub>=4.15, 95% CI 1.56 to 11.01, OR<sub>Q4</sub>=4.76, 95% CI 1.53 to 14.82, p<sub>trend</sub> &lt;0.01), higher TSH (p<sub>trend</sub>=0.01) and lower T4 (p<sub>trend</sub>=0.04). Higher exposure to the herbicide pendimethalin was associated with subclinical hypothyroidism (fourth quartile vs no exposure: OR<sub>Q4</sub>=2.78, 95% CI 1.30 to 5.95, p<sub>trend</sub>=0.02), higher TSH (p<sub>trend</sub>=0.04) and anti-TPO positivity (p<sub>trend</sub>=0.01). The fumigant methyl bromide was inversely associated with TSH (p<sub>trend</sub>=0.02) and positively associated with T4 (p<sub>trend</sub>=0.01).",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["Abstract"]["AbstractText"][
                2
            ].attributes,
            {"NlmCategory": "RESULTS", "Label": "RESULTS"},
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["Abstract"]["AbstractText"][3],
            "Our results suggest that long-term exposure to aldrin, pendimethalin and methyl bromide may alter thyroid function among male pesticide applicators.",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["Abstract"]["AbstractText"][
                3
            ].attributes,
            {"NlmCategory": "CONCLUSIONS", "Label": "CONCLUSIONS"},
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["Abstract"]["CopyrightInformation"],
            "\xa9 Article author(s) (or their employer(s) unless otherwise stated in the text of the article) 2018. All rights reserved. No commercial use is permitted unless otherwise expressly granted.",
        )
        self.assertEqual(len(article["MedlineCitation"]["Article"]["GrantList"]), 3)
        self.assertEqual(len(article["MedlineCitation"]["Article"]["GrantList"][0]), 4)
        self.assertEqual(
            article["MedlineCitation"]["Article"]["GrantList"][0]["Acronym"], "CP"
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["GrantList"][0]["Country"],
            "United States",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["GrantList"][0]["Agency"],
            "NCI NIH HHS",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["GrantList"][0]["GrantID"],
            "Z01 CP010119",
        )
        self.assertEqual(
            len(article["MedlineCitation"]["Article"]["GrantList"][0].attributes), 0
        )
        self.assertEqual(len(article["MedlineCitation"]["Article"]["GrantList"][1]), 4)
        self.assertEqual(
            article["MedlineCitation"]["Article"]["GrantList"][1]["Acronym"], "ES"
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["GrantList"][1]["Country"],
            "United States",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["GrantList"][1]["Agency"],
            "NIEHS NIH HHS",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["GrantList"][1]["GrantID"],
            "Z01 ES049030",
        )
        self.assertEqual(
            len(article["MedlineCitation"]["Article"]["GrantList"][1].attributes), 0
        )
        self.assertEqual(len(article["MedlineCitation"]["Article"]["GrantList"][2]), 4)
        self.assertEqual(
            article["MedlineCitation"]["Article"]["GrantList"][2]["Acronym"], "NULL"
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["GrantList"][2]["Country"],
            "United States",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["GrantList"][2]["Agency"],
            "Intramural NIH HHS",
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["GrantList"][2]["GrantID"],
            "Z99 CA999999",
        )
        self.assertEqual(
            len(article["MedlineCitation"]["Article"]["GrantList"][2].attributes), 0
        )
        self.assertEqual(
            article["MedlineCitation"]["Article"]["GrantList"].attributes,
            {"CompleteYN": "Y"},
        )

    def test_pubmed_html_mathml_tags(self):
        """Test parsing XML returned by EFetch, PubMed database, with both HTML and MathML tags."""
        # In PubMed display PMID 30108519 in xml retrieval mode, containing
        # both HTML and MathML tags in the abstract text.
        # To create the XML file, use
        # >>> Bio.Entrez.efetch(db="pubmed", id='30108519', rettype="null",
        #                       retmode="xml", parsed=True)
        with open("Entrez/pubmed6.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(len(record), 2)
        self.assertEqual(record["PubmedBookArticle"], [])
        self.assertEqual(len(record["PubmedArticle"]), 1)
        pubmed_article = record["PubmedArticle"][0]
        self.assertEqual(len(pubmed_article), 2)
        self.assertEqual(len(pubmed_article["PubmedData"]), 3)
        self.assertEqual(len(pubmed_article["PubmedData"]["ArticleIdList"]), 3)
        self.assertEqual(pubmed_article["PubmedData"]["ArticleIdList"][0], "30108519")
        self.assertEqual(
            pubmed_article["PubmedData"]["ArticleIdList"][0].attributes,
            {"IdType": "pubmed"},
        )
        self.assertEqual(
            pubmed_article["PubmedData"]["ArticleIdList"][1], "10.3389/fphys.2018.01034"
        )
        self.assertEqual(
            pubmed_article["PubmedData"]["ArticleIdList"][1].attributes,
            {"IdType": "doi"},
        )
        self.assertEqual(pubmed_article["PubmedData"]["ArticleIdList"][2], "PMC6079548")
        self.assertEqual(
            pubmed_article["PubmedData"]["ArticleIdList"][2].attributes,
            {"IdType": "pmc"},
        )
        self.assertEqual(pubmed_article["PubmedData"]["PublicationStatus"], "epublish")
        self.assertEqual(len(pubmed_article["PubmedData"]["History"]), 5)
        self.assertEqual(len(pubmed_article["PubmedData"]["History"][0]), 3)
        self.assertEqual(pubmed_article["PubmedData"]["History"][0]["Year"], "2018")
        self.assertEqual(pubmed_article["PubmedData"]["History"][0]["Month"], "05")
        self.assertEqual(pubmed_article["PubmedData"]["History"][0]["Day"], "22")
        self.assertEqual(
            pubmed_article["PubmedData"]["History"][0].attributes,
            {"PubStatus": "received"},
        )
        self.assertEqual(len(pubmed_article["PubmedData"]["History"][1]), 3)
        self.assertEqual(pubmed_article["PubmedData"]["History"][1]["Year"], "2018")
        self.assertEqual(pubmed_article["PubmedData"]["History"][1]["Month"], "07")
        self.assertEqual(pubmed_article["PubmedData"]["History"][1]["Day"], "11")
        self.assertEqual(
            pubmed_article["PubmedData"]["History"][1].attributes,
            {"PubStatus": "accepted"},
        )
        self.assertEqual(len(pubmed_article["PubmedData"]["History"][2]), 5)
        self.assertEqual(pubmed_article["PubmedData"]["History"][2]["Year"], "2018")
        self.assertEqual(pubmed_article["PubmedData"]["History"][2]["Month"], "8")
        self.assertEqual(pubmed_article["PubmedData"]["History"][2]["Day"], "16")
        self.assertEqual(pubmed_article["PubmedData"]["History"][2]["Hour"], "6")
        self.assertEqual(pubmed_article["PubmedData"]["History"][2]["Minute"], "0")
        self.assertEqual(
            pubmed_article["PubmedData"]["History"][2].attributes,
            {"PubStatus": "entrez"},
        )
        self.assertEqual(len(pubmed_article["PubmedData"]["History"][3]), 5)
        self.assertEqual(pubmed_article["PubmedData"]["History"][3]["Year"], "2018")
        self.assertEqual(pubmed_article["PubmedData"]["History"][3]["Month"], "8")
        self.assertEqual(pubmed_article["PubmedData"]["History"][3]["Day"], "16")
        self.assertEqual(pubmed_article["PubmedData"]["History"][3]["Hour"], "6")
        self.assertEqual(pubmed_article["PubmedData"]["History"][3]["Minute"], "0")
        self.assertEqual(
            pubmed_article["PubmedData"]["History"][3].attributes,
            {"PubStatus": "pubmed"},
        )
        self.assertEqual(len(pubmed_article["PubmedData"]["History"][4]), 5)
        self.assertEqual(pubmed_article["PubmedData"]["History"][4]["Year"], "2018")
        self.assertEqual(pubmed_article["PubmedData"]["History"][4]["Month"], "8")
        self.assertEqual(pubmed_article["PubmedData"]["History"][4]["Day"], "16")
        self.assertEqual(pubmed_article["PubmedData"]["History"][4]["Hour"], "6")
        self.assertEqual(pubmed_article["PubmedData"]["History"][4]["Minute"], "1")
        self.assertEqual(
            pubmed_article["PubmedData"]["History"][4].attributes,
            {"PubStatus": "medline"},
        )
        medline_citation = pubmed_article["MedlineCitation"]
        self.assertEqual(len(medline_citation), 11)
        self.assertEqual(medline_citation["GeneralNote"], [])
        self.assertEqual(len(medline_citation["KeywordList"]), 1)
        self.assertEqual(len(medline_citation["KeywordList"][0]), 8)
        self.assertEqual(medline_citation["KeywordList"][0][0], "Owles' point")
        self.assertEqual(
            medline_citation["KeywordList"][0][0].attributes, {"MajorTopicYN": "N"}
        )
        self.assertEqual(medline_citation["KeywordList"][0][1], "aerobic capacity")
        self.assertEqual(
            medline_citation["KeywordList"][0][1].attributes, {"MajorTopicYN": "N"}
        )
        self.assertEqual(medline_citation["KeywordList"][0][2], "aerobic threshold")
        self.assertEqual(
            medline_citation["KeywordList"][0][2].attributes, {"MajorTopicYN": "N"}
        )
        self.assertEqual(medline_citation["KeywordList"][0][3], "anaerobic threshold")
        self.assertEqual(
            medline_citation["KeywordList"][0][3].attributes, {"MajorTopicYN": "N"}
        )
        self.assertEqual(medline_citation["KeywordList"][0][4], "endurance assessment")
        self.assertEqual(
            medline_citation["KeywordList"][0][4].attributes, {"MajorTopicYN": "N"}
        )
        self.assertEqual(medline_citation["KeywordList"][0][5], "lactate threshold")
        self.assertEqual(
            medline_citation["KeywordList"][0][5].attributes, {"MajorTopicYN": "N"}
        )
        self.assertEqual(
            medline_citation["KeywordList"][0][6], "oxygen endurance performance limit"
        )
        self.assertEqual(
            medline_citation["KeywordList"][0][6].attributes, {"MajorTopicYN": "N"}
        )
        self.assertEqual(
            medline_citation["KeywordList"][0][7], "submaximal exercise testing"
        )
        self.assertEqual(
            medline_citation["KeywordList"][0][7].attributes, {"MajorTopicYN": "N"}
        )
        self.assertEqual(medline_citation["CitationSubset"], [])
        self.assertEqual(medline_citation["OtherAbstract"], [])
        self.assertEqual(medline_citation["OtherID"], [])
        self.assertEqual(medline_citation["SpaceFlightMission"], [])
        self.assertEqual(medline_citation["PMID"], "30108519")
        self.assertEqual(medline_citation["PMID"].attributes, {"Version": "1"})
        self.assertEqual(len(medline_citation["DateRevised"]), 3)
        self.assertEqual(medline_citation["DateRevised"]["Year"], "2018")
        self.assertEqual(medline_citation["DateRevised"]["Month"], "08")
        self.assertEqual(medline_citation["DateRevised"]["Day"], "17")
        self.assertEqual(medline_citation["DateRevised"].attributes, {})
        self.assertEqual(len(medline_citation["MedlineJournalInfo"]), 4)
        self.assertEqual(
            medline_citation["MedlineJournalInfo"]["Country"], "Switzerland"
        )
        self.assertEqual(
            medline_citation["MedlineJournalInfo"]["MedlineTA"], "Front Physiol"
        )
        self.assertEqual(
            medline_citation["MedlineJournalInfo"]["NlmUniqueID"], "101549006"
        )
        self.assertEqual(
            medline_citation["MedlineJournalInfo"]["ISSNLinking"], "1664-042X"
        )
        self.assertEqual(medline_citation["MedlineJournalInfo"].attributes, {})
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"]), 53)
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][0]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][0]["RefSource"],
            "Stat Med. 2008 Feb 28;27(5):778-80",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][0]["PMID"], "17907247"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][0]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][0].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][1]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][1]["RefSource"],
            "Int J Sports Med. 2009 Jan;30(1):40-45",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][1]["PMID"], "19202577"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][1]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][1].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][2]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][2]["RefSource"],
            "Med Sci Sports Exerc. 1995 Jun;27(6):863-7",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][2]["PMID"], "7658947"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][2]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][2].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][3]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][3]["RefSource"],
            "Eur J Appl Physiol. 2010 Apr;108(6):1153-67",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][3]["PMID"], "20033207"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][3]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][3].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][4]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][4]["RefSource"],
            "Med Sci Sports Exerc. 1999 Apr;31(4):578-82",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][4]["PMID"], "10211855"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][4]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][4].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][5]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][5]["RefSource"],
            "Br J Sports Med. 1988 Jun;22(2):51-4",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][5]["PMID"], "3167501"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][5]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][5].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][6]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][6]["RefSource"],
            "Front Physiol. 2017 Jun 08;8:389",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][6]["PMID"], "28642717"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][6]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][6].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][7]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][7]["RefSource"],
            "Med Sci Sports Exerc. 1999 Sep;31(9):1342-5",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][7]["PMID"], "10487378"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][7]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][7].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][8]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][8]["RefSource"],
            "Med Sci Sports Exerc. 1998 Aug;30(8):1304-13",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][8]["PMID"], "9710874"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][8]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][8].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][9]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][9]["RefSource"],
            "Med Sci Sports. 1979 Winter;11(4):338-44",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][9]["PMID"], "530025"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][9]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][9].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][10]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][10]["RefSource"],
            "J Strength Cond Res. 2005 May;19(2):364-8",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][10]["PMID"], "15903376"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][10]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][10].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][11]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][11]["RefSource"],
            "Eur J Appl Physiol Occup Physiol. 1984;53(3):196-9",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][11]["PMID"], "6542852"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][11]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][11].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][12]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][12]["RefSource"],
            "Eur J Appl Physiol Occup Physiol. 1978 Oct 20;39(4):219-27",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][12]["PMID"], "710387"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][12]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][12].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][13]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][13]["RefSource"],
            "J Appl Physiol Respir Environ Exerc Physiol. 1980 Mar;48(3):523-7",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][13]["PMID"], "7372524"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][13]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][13].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][14]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][14]["RefSource"],
            "Int J Sports Med. 2015 Dec;36(14):1142-8",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][14]["PMID"], "26332904"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][14]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][14].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][15]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][15]["RefSource"],
            "J Physiol. 1930 Apr 14;69(2):214-37",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][15]["PMID"], "16994099"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][15]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][15].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][16]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][16]["RefSource"],
            "J Strength Cond Res. 2015 Oct;29(10):2794-801",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][16]["PMID"], "25844867"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][16]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][16].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][17]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][17]["RefSource"],
            "PLoS One. 2018 Mar 13;13(3):e0194313",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][17]["PMID"], "29534108"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][17]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][17].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][18]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][18]["RefSource"],
            "J Cardiopulm Rehabil Prev. 2012 Nov-Dec;32(6):327-50",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][18]["PMID"], "23103476"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][18]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][18].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][19]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][19]["RefSource"],
            "Exerc Sport Sci Rev. 1982;10:49-83",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][19]["PMID"], "6811284"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][19]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][19].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][20]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][20]["RefSource"],
            "Int J Sports Physiol Perform. 2010 Sep;5(3):276-91",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][20]["PMID"], "20861519"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][20]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][20].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][21]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][21]["RefSource"],
            "Eur J Appl Physiol Occup Physiol. 1990;60(4):249-53",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][21]["PMID"], "2357979"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][21]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][21].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][22]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][22]["RefSource"],
            "Med Sci Sports Exerc. 2004 Oct;36(10):1737-42",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][22]["PMID"], "15595295"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][22]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][22].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][23]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][23]["RefSource"],
            "Int J Sports Med. 2016 Jun;37(7):539-46",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][23]["PMID"], "27116348"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][23]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][23].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][24]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][24]["RefSource"],
            "Scand J Med Sci Sports. 2017 May;27(5):462-473",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][24]["PMID"], "28181710"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][24]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][24].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][25]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][25]["RefSource"],
            "Int J Sports Med. 1983 Nov;4(4):226-30",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][25]["PMID"], "6654546"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][25]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][25].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][26]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][26]["RefSource"],
            "J Appl Physiol (1985). 1988 Jun;64(6):2622-30",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][26]["PMID"], "3403447"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][26]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][26].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][27]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][27]["RefSource"],
            "Med Sci Sports Exerc. 2009 Jan;41(1):3-13",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][27]["PMID"], "19092709"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][27]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][27].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][28]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][28]["RefSource"],
            "Int J Sports Med. 2009 Sep;30(9):643-6",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][28]["PMID"], "19569005"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][28]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][28].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][29]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][29]["RefSource"],
            "Eur J Appl Physiol Occup Physiol. 1988;57(4):420-4",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][29]["PMID"], "3396556"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][29]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][29].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][30]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][30]["RefSource"],
            "J Physiol. 2004 Jul 1;558(Pt 1):5-30",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][30]["PMID"], "15131240"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][30]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][30].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][31]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][31]["RefSource"],
            "Int J Sports Med. 1990 Feb;11(1):26-32",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][31]["PMID"], "2318561"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][31]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][31].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][32]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][32]["RefSource"],
            "J Appl Physiol. 1973 Aug;35(2):236-43",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][32]["PMID"], "4723033"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][32]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][32].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][33]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][33]["RefSource"],
            "Int J Sports Med. 1987 Dec;8(6):401-6",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][33]["PMID"], "3429086"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][33]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][33].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][34]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][34]["RefSource"],
            "J Sci Med Sport. 2008 Jun;11(3):280-6",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][34]["PMID"], "17553745"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][34]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][34].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][35]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][35]["RefSource"],
            "J Appl Physiol Respir Environ Exerc Physiol. 1984 May;56(5):1260-4",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][35]["PMID"], "6725086"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][35]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][35].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][36]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][36]["RefSource"],
            "Int J Sports Med. 2008 Jun;29(6):475-9",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][36]["PMID"], "18302077"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][36]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][36].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][37]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][37]["RefSource"],
            "Med Sci Sports Exerc. 1985 Feb;17(1):22-34",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][37]["PMID"], "3884959"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][37]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][37].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][38]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][38]["RefSource"],
            "Sports Med. 2009;39(6):469-90",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][38]["PMID"], "19453206"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][38]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][38].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][39]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][39]["RefSource"],
            "Int J Sports Med. 2004 Aug;25(6):403-8",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][39]["PMID"], "15346226"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][39]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][39].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][40]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][40]["RefSource"],
            "J Sports Med Phys Fitness. 2004 Jun;44(2):132-40",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][40]["PMID"], "15470310"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][40]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][40].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][41]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][41]["RefSource"],
            "Int J Sports Med. 1985 Jun;6(3):117-30",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][41]["PMID"], "4030186"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][41]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][41].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][42]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][42]["RefSource"],
            "Int J Sports Med. 1999 Feb;20(2):122-7",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][42]["PMID"], "10190774"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][42]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][42].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][43]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][43]["RefSource"],
            "Int J Sports Med. 2006 May;27(5):368-72",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][43]["PMID"], "16729378"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][43]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][43].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][44]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][44]["RefSource"],
            "Int J Sports Med. 1985 Jun;6(3):109-16",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][44]["PMID"], "3897079"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][44]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][44].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][45]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][45]["RefSource"],
            "Pneumologie. 1990 Jan;44(1):2-13",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][45]["PMID"], "2408033"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][45]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][45].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][46]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][46]["RefSource"],
            "Eur J Appl Physiol. 2018 Apr;118(4):691-728",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][46]["PMID"], "29322250"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][46]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][46].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][47]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][47]["RefSource"],
            "J Appl Physiol Respir Environ Exerc Physiol. 1983 Oct;55(4):1178-86",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][47]["PMID"], "6629951"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][47]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][47].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][48]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][48]["RefSource"],
            "Sports Med. 2014 Nov;44 Suppl 2:S139-47",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][48]["PMID"], "25200666"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][48]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][48].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][49]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][49]["RefSource"],
            "Front Physiol. 2015 Oct 30;6:308",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][49]["PMID"], "26578980"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][49]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][49].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][50]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][50]["RefSource"],
            "Int J Sports Med. 2013 Mar;34(3):196-9",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][50]["PMID"], "22972242"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][50]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][50].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][51]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][51]["RefSource"],
            "Int J Sports Med. 1992 Oct;13(7):518-22",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][51]["PMID"], "1459746"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][51]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][51].attributes,
            {"RefType": "Cites"},
        )
        self.assertEqual(len(medline_citation["CommentsCorrectionsList"][52]), 2)
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][52]["RefSource"],
            "Med Sci Sports Exerc. 1993 May;25(5):620-7",
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][52]["PMID"], "8492691"
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][52]["PMID"].attributes,
            {"Version": "1"},
        )
        self.assertEqual(
            medline_citation["CommentsCorrectionsList"][52].attributes,
            {"RefType": "Cites"},
        )
        article = medline_citation["Article"]
        self.assertEqual(len(article["ELocationID"]), 1)
        self.assertEqual(article["ELocationID"][0], "10.3389/fphys.2018.01034")
        self.assertEqual(
            article["ELocationID"][0].attributes, {"EIdType": "doi", "ValidYN": "Y"}
        )
        self.assertEqual(len(article["ArticleDate"]), 1)
        self.assertEqual(len(article["ArticleDate"][0]), 3)
        self.assertEqual(article["ArticleDate"][0]["Year"], "2018")
        self.assertEqual(article["ArticleDate"][0]["Month"], "07")
        self.assertEqual(article["ArticleDate"][0]["Day"], "31")
        self.assertEqual(
            article["ArticleDate"][0].attributes, {"DateType": "Electronic"}
        )
        self.assertEqual(article["Language"], ["eng"])
        self.assertEqual(len(article["Journal"]), 4)
        self.assertEqual(article["Journal"]["ISSN"], "1664-042X")
        self.assertEqual(article["Journal"]["ISSN"].attributes, {"IssnType": "Print"})
        self.assertEqual(article["Journal"]["JournalIssue"]["Volume"], "9")
        self.assertEqual(article["Journal"]["JournalIssue"]["PubDate"]["Year"], "2018")
        self.assertEqual(article["Journal"]["JournalIssue"]["PubDate"].attributes, {})
        self.assertEqual(
            article["Journal"]["JournalIssue"].attributes, {"CitedMedium": "Print"}
        )
        self.assertEqual(article["Journal"]["Title"], "Frontiers in physiology")
        self.assertEqual(article["Journal"]["ISOAbbreviation"], "Front Physiol")
        self.assertEqual(article["Journal"].attributes, {})
        self.assertEqual(len(article["PublicationTypeList"]), 1)
        self.assertEqual(article["PublicationTypeList"][0], "Journal Article")
        self.assertEqual(
            article["PublicationTypeList"][0].attributes, {"UI": "D016428"}
        )
        self.assertEqual(
            article["ArticleTitle"],
            'A "<i>Blood Relationship"</i> Between the Overlooked Minimum Lactate Equivalent and Maximal Lactate Steady State in Trained Runners. Back to the Old Days?',
        )
        self.assertEqual(len(article["Pagination"]), 1)
        self.assertEqual(article["Pagination"]["MedlinePgn"], "1034")
        self.assertEqual(article["Pagination"].attributes, {})
        self.assertEqual(len(article["AuthorList"]), 2)
        self.assertEqual(len(article["AuthorList"][0]), 5)
        self.assertEqual(article["AuthorList"][0]["Identifier"], [])
        self.assertEqual(len(article["AuthorList"][0]["AffiliationInfo"]), 1)
        self.assertEqual(len(article["AuthorList"][0]["AffiliationInfo"][0]), 2)
        self.assertEqual(
            article["AuthorList"][0]["AffiliationInfo"][0]["Identifier"], []
        )
        self.assertEqual(
            article["AuthorList"][0]["AffiliationInfo"][0]["Affiliation"],
            "Studies, Research and Sports Medicine Center, Government of Navarre, Pamplona, Spain.",
        )
        self.assertEqual(article["AuthorList"][0]["AffiliationInfo"][0].attributes, {})
        self.assertEqual(article["AuthorList"][0]["LastName"], "Garcia-Tabar")
        self.assertEqual(article["AuthorList"][0]["ForeName"], "Ibai")
        self.assertEqual(article["AuthorList"][0]["Initials"], "I")
        self.assertEqual(article["AuthorList"][0].attributes, {"ValidYN": "Y"})
        self.assertEqual(len(article["AuthorList"][1]), 5)
        self.assertEqual(article["AuthorList"][1]["Identifier"], [])
        self.assertEqual(len(article["AuthorList"][1]["AffiliationInfo"]), 1)
        self.assertEqual(len(article["AuthorList"][1]["AffiliationInfo"][0]), 2)
        self.assertEqual(
            article["AuthorList"][1]["AffiliationInfo"][0]["Identifier"], []
        )
        self.assertEqual(
            article["AuthorList"][1]["AffiliationInfo"][0]["Affiliation"],
            "Studies, Research and Sports Medicine Center, Government of Navarre, Pamplona, Spain.",
        )
        self.assertEqual(article["AuthorList"][1]["AffiliationInfo"][0].attributes, {})
        self.assertEqual(article["AuthorList"][1]["LastName"], "Gorostiaga")
        self.assertEqual(article["AuthorList"][1]["ForeName"], "Esteban M")
        self.assertEqual(article["AuthorList"][1]["Initials"], "EM")
        self.assertEqual(article["AuthorList"][1].attributes, {"ValidYN": "Y"})
        self.assertEqual(len(article["Abstract"]), 1)
        self.assertEqual(
            article["Abstract"]["AbstractText"][0],
            """\
Maximal Lactate Steady State (MLSS) and Lactate Threshold (LT) are physiologically-related and fundamental concepts within the sports and exercise sciences. Literature supporting their relationship, however, is scarce. Among the recognized LTs, we were particularly interested in the disused "Minimum Lactate Equivalent" (LE<sub>min</sub>), first described in the early 1980s. We hypothesized that velocity at LT, conceptually comprehended as in the old days (LE<sub>min</sub>), could predict velocity at MLSS (<sub>V</sub>MLSS) more accurate than some other blood lactate-related thresholds (BL<sub>R</sub>Ts) routinely used nowadays by many sport science practitioners. Thirteen male endurance-trained [<sub>V</sub>MLSS 15.0 ± 1.1 km·h<sup>-1</sup>; maximal oxygen uptake ( <math xmlns="http://www.w3.org/1998/Math/MathML">
                        <msub>
                            <mrow>
                                <mover>
                                    <mrow>
                                        <mi>V</mi>
                                    </mrow>
                                    <mo>.</mo>
                                </mover>
                                <mi>O</mi>
                            </mrow>
                            <mrow>
                                <mn>2</mn>
                                <mi>m</mi>
                                <mi>a</mi>
                                <mi>x</mi>
                            </mrow>
                        </msub>
                    </math> ) 67.6 ± 4.1 ml·kg<sup>-1</sup>·min<sup>-1</sup>] homogeneous (coefficient of variation: ≈7%) runners conducted 1) a submaximal discontinuous incremental running test to determine several BL<sub>R</sub>Ts followed by a maximal ramp incremental running test for <math xmlns="http://www.w3.org/1998/Math/MathML">
                        <msub>
                            <mrow>
                                <mover>
                                    <mrow>
                                        <mi>V</mi>
                                    </mrow>
                                    <mo>.</mo>
                                </mover>
                                <mi>O</mi>
                            </mrow>
                            <mrow>
                                <mn>2</mn>
                                <mi>m</mi>
                                <mi>a</mi>
                                <mi>x</mi>
                            </mrow>
                        </msub>
                        <mtext> </mtext>
                    </math> determination, and 2) several (4-5) constant velocity running tests to determine <sub>V</sub>MLSS with a precision of 0.20 km·h<sup>-1</sup>. Determined BL<sub>R</sub>Ts include LE<sub>min</sub> and LE<sub>min</sub>-related LE<sub>min</sub> plus 1 (LE<sub>min+1mM</sub>) and 1.5 mmol·L<sup>-1</sup> (LE<sub>min+1.5mM</sub>), along with well-established BL<sub>R</sub>Ts such as conventionally-calculated LT, D<sub>max</sub> and fixed blood lactate concentration thresholds. LE<sub>min</sub> did not differ from LT (<i>P</i> = 0.71; ES: 0.08) and was 27% lower than MLSS (<i>P</i> < 0.001; ES: 3.54). LE<sub>min+1mM</sub> was not different from MLSS (<i>P</i> = 0.47; ES: 0.09). LE<sub>min</sub> was the best predictor of <sub>V</sub>MLSS (<i>r</i> = 0.91; <i>P</i> < 0.001; SEE = 0.47 km·h<sup>-1</sup>), followed by LE<sub>min+1mM</sub> (<i>r</i> = 0.86; <i>P</i> < 0.001; SEE = 0.58 km·h<sup>-1</sup>) and LE<sub>min+1.5mM</sub> (<i>r</i> = 0.84; <i>P</i> < 0.001; SEE = 0.86 km·h<sup>-1</sup>). There was no statistical difference between MLSS and estimated MLSS using LE<sub>min</sub> prediction formula (<i>P</i> = 0.99; ES: 0.001). Mean bias and limits of agreement were 0.00 ± 0.45 km·h<sup>-1</sup> and ±0.89 km·h<sup>-1</sup>. Additionally, LE<sub>min</sub>, LE<sub>min+1mM</sub> and LE<sub>min+1.5mM</sub> were the best predictors of <math xmlns="http://www.w3.org/1998/Math/MathML">
                        <msub>
                            <mrow>
                                <mover>
                                    <mrow>
                                        <mi>V</mi>
                                    </mrow>
                                    <mo>.</mo>
                                </mover>
                                <mi>O</mi>
                            </mrow>
                            <mrow>
                                <mn>2</mn>
                                <mi>m</mi>
                                <mi>a</mi>
                                <mi>x</mi>
                            </mrow>
                        </msub>
                    </math> (<i>r</i> = 0.72-0.79; <i>P</i> < 0.001). These results support LE<sub>min</sub>, an objective submaximal overlooked and underused BL<sub>R</sub>T, to be one of the best single MLSS predictors in endurance trained runners. Our study advocates factors controlling LE<sub>min</sub> to be shared, at least partly, with those controlling MLSS.""",
        )

    def test_pubmed_mathml_tags(self):
        """Test parsing XML returned by EFetch, PubMed database, with extensive MathML tags."""
        # In PubMed display PMID 29963580 in xml retrieval mode, containing
        # extensive MathML tags in the abstract text.
        # To create the XML file, use
        # >>> Bio.Entrez.efetch(db="pubmed", id="29963580", retmode="xml")
        with open("Entrez/pubmed7.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(len(record), 2)
        self.assertEqual(record["PubmedBookArticle"], [])
        self.assertEqual(len(record["PubmedArticle"]), 1)
        pubmed_article = record["PubmedArticle"][0]
        self.assertEqual(len(pubmed_article), 2)
        self.assertEqual(len(pubmed_article["MedlineCitation"].attributes), 2)
        self.assertEqual(
            pubmed_article["MedlineCitation"].attributes["Status"], "PubMed-not-MEDLINE"
        )
        self.assertEqual(pubmed_article["MedlineCitation"].attributes["Owner"], "NLM")
        self.assertEqual(pubmed_article["MedlineCitation"]["PMID"], "29963580")
        self.assertEqual(
            pubmed_article["MedlineCitation"]["PMID"].attributes["Version"], "1"
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["DateRevised"].attributes, {}
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["DateRevised"]["Year"], "2018"
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["DateRevised"]["Month"], "11"
        )
        self.assertEqual(pubmed_article["MedlineCitation"]["DateRevised"]["Day"], "14")
        self.assertEqual(
            len(pubmed_article["MedlineCitation"]["Article"].attributes), 1
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"].attributes["PubModel"],
            "Print-Electronic",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["Journal"].attributes, {}
        )
        self.assertEqual(
            len(
                pubmed_article["MedlineCitation"]["Article"]["Journal"][
                    "ISSN"
                ].attributes
            ),
            1,
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["Journal"]["ISSN"].attributes[
                "IssnType"
            ],
            "Print",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["Journal"]["ISSN"], "2329-4302"
        )
        self.assertEqual(
            len(
                pubmed_article["MedlineCitation"]["Article"]["Journal"][
                    "JournalIssue"
                ].attributes
            ),
            1,
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["Journal"][
                "JournalIssue"
            ].attributes["CitedMedium"],
            "Print",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["Journal"]["JournalIssue"][
                "Volume"
            ],
            "5",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["Journal"]["JournalIssue"][
                "Issue"
            ],
            "2",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["Journal"]["JournalIssue"][
                "PubDate"
            ]["Year"],
            "2018",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["Journal"]["JournalIssue"][
                "PubDate"
            ]["Month"],
            "Apr",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["Journal"]["Title"],
            "Journal of medical imaging (Bellingham, Wash.)",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["Journal"]["ISOAbbreviation"],
            "J Med Imaging (Bellingham)",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["ArticleTitle"],
            "Development of a pulmonary imaging biomarker pipeline for phenotyping of chronic lung disease.",
        )
        self.assertEqual(
            len(pubmed_article["MedlineCitation"]["Article"]["Pagination"]), 1
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["Pagination"]["MedlinePgn"],
            "026002",
        )
        self.assertEqual(
            len(pubmed_article["MedlineCitation"]["Article"]["ELocationID"]), 1
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["ELocationID"][0].attributes[
                "EIdType"
            ],
            "doi",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["ELocationID"][0].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["ELocationID"][0],
            "10.1117/1.JMI.5.2.026002",
        )
        self.assertEqual(
            len(pubmed_article["MedlineCitation"]["Article"]["Abstract"]), 1
        )
        self.assertEqual(
            len(
                pubmed_article["MedlineCitation"]["Article"]["Abstract"]["AbstractText"]
            ),
            1,
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["Abstract"]["AbstractText"][0],
            """\
We designed and generated pulmonary imaging biomarker pipelines to facilitate high-throughput research and point-of-care use in patients with chronic lung disease. Image processing modules and algorithm pipelines were embedded within a graphical user interface (based on the .NET framework) for pulmonary magnetic resonance imaging (MRI) and x-ray computed-tomography (CT) datasets. The software pipelines were generated using C++ and included: (1) inhaled <math xmlns="http://www.w3.org/1998/Math/MathML">
                        <mrow>
                            <mmultiscripts>
                                <mrow>
                                    <mi>He</mi>
                                </mrow>
                                <mprescripts></mprescripts>
                                <none></none>
                                <mrow>
                                    <mn>3</mn>
                                </mrow>
                            </mmultiscripts>
                            <mo>/</mo>
                            <mmultiscripts>
                                <mrow>
                                    <mi>Xe</mi>
                                </mrow>
                                <mprescripts></mprescripts>
                                <none></none>
                                <mrow>
                                    <mn>129</mn>
                                </mrow>
                            </mmultiscripts>
                            <mtext> </mtext>
                            <mi>MRI</mi>
                        </mrow>
                    </math> ventilation and apparent diffusion coefficients, (2) CT-MRI coregistration for lobar and segmental ventilation and perfusion measurements, (3) ultrashort echo-time <math xmlns="http://www.w3.org/1998/Math/MathML">
                        <mrow>
                            <mmultiscripts>
                                <mrow>
                                    <mi>H</mi>
                                </mrow>
                                <mprescripts></mprescripts>
                                <none></none>
                                <mrow>
                                    <mn>1</mn>
                                </mrow>
                            </mmultiscripts>
                            <mtext> </mtext>
                            <mi>MRI</mi>
                        </mrow>
                    </math> proton density measurements, (4) free-breathing Fourier-decomposition <math xmlns="http://www.w3.org/1998/Math/MathML">
                        <mrow>
                            <mmultiscripts>
                                <mrow>
                                    <mi>H</mi>
                                </mrow>
                                <mprescripts></mprescripts>
                                <none></none>
                                <mrow>
                                    <mn>1</mn>
                                </mrow>
                            </mmultiscripts>
                            <mtext> </mtext>
                            <mi>MRI</mi>
                        </mrow>
                    </math> ventilation/perfusion and free-breathing <math xmlns="http://www.w3.org/1998/Math/MathML">
                        <mrow>
                            <mmultiscripts>
                                <mrow>
                                    <mi>H</mi>
                                </mrow>
                                <mprescripts></mprescripts>
                                <none></none>
                                <mrow>
                                    <mn>1</mn>
                                </mrow>
                            </mmultiscripts>
                            <mtext> </mtext>
                            <mi>MRI</mi>
                        </mrow>
                    </math> specific ventilation, (5)\u00a0multivolume CT and MRI parametric response maps, and (6)\u00a0MRI and CT texture analysis and radiomics. The image analysis framework was implemented on a desktop workstation/tablet to generate biomarkers of regional lung structure and function related to ventilation, perfusion, lung tissue texture, and integrity as well as multiparametric measures of gas trapping and airspace enlargement. All biomarkers were generated within 10 min with measurement reproducibility consistent with clinical and research requirements. The resultant pulmonary imaging biomarker pipeline provides real-time and automated lung imaging measurements for point-of-care and high-throughput research.""",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"].attributes[
                "CompleteYN"
            ],
            "Y",
        )
        self.assertEqual(
            len(pubmed_article["MedlineCitation"]["Article"]["AuthorList"]), 9
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][0].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][0]["LastName"],
            "Guo",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][0]["ForeName"],
            "Fumin",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][0]["Initials"],
            "F",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][0][
                "AffiliationInfo"
            ][0]["Affiliation"],
            "University of Western Ontario, Robarts Research Institute, London, Ontario, Canada.",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][0][
                "AffiliationInfo"
            ][1]["Affiliation"],
            "University of Western Ontario, Graduate Program in Biomedical Engineering, London, Ontario, Canada.",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][0][
                "AffiliationInfo"
            ][2]["Affiliation"],
            "University of Toronto, Sunnybrook Research Institute, Toronto, Canada.",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][1].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][1]["LastName"],
            "Capaldi",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][1]["ForeName"],
            "Dante",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][1]["Initials"],
            "D",
        )
        self.assertEqual(
            len(
                pubmed_article["MedlineCitation"]["Article"]["AuthorList"][1][
                    "Identifier"
                ]
            ),
            1,
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][1]["Identifier"][
                0
            ].attributes["Source"],
            "ORCID",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][1]["Identifier"][
                0
            ],
            "https://orcid.org/0000-0002-4590-7461",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][1][
                "AffiliationInfo"
            ][0]["Affiliation"],
            "University of Western Ontario, Robarts Research Institute, London, Ontario, Canada.",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][1][
                "AffiliationInfo"
            ][1]["Affiliation"],
            "University of Western Ontario, Department of Medical Biophysics, London, Ontario, Canada.",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][2].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][2]["LastName"],
            "Kirby",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][2]["ForeName"],
            "Miranda",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][2]["Initials"],
            "M",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][2][
                "AffiliationInfo"
            ][0]["Affiliation"],
            "University of British Columbia, St. Paul's Hospital, Centre for Heart Lung Innovation, Vancouver, Canada.",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][3].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][3]["LastName"],
            "Sheikh",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][3]["ForeName"],
            "Khadija",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][3]["Initials"],
            "K",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][3][
                "AffiliationInfo"
            ][0]["Affiliation"],
            "University of Western Ontario, Robarts Research Institute, London, Ontario, Canada.",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][4].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][4]["LastName"],
            "Svenningsen",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][4]["ForeName"],
            "Sarah",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][4]["Initials"],
            "S",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][4][
                "AffiliationInfo"
            ][0]["Affiliation"],
            "University of Western Ontario, Robarts Research Institute, London, Ontario, Canada.",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][5].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][5]["LastName"],
            "McCormack",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][5]["ForeName"],
            "David G",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][5]["Initials"],
            "DG",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][5][
                "AffiliationInfo"
            ][0]["Affiliation"],
            "University of Western Ontario, Division of Respirology, Department of Medicine, London, Ontario, Canada.",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][6].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][6]["LastName"],
            "Fenster",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][6]["ForeName"],
            "Aaron",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][6]["Initials"],
            "A",
        )
        self.assertEqual(
            len(
                pubmed_article["MedlineCitation"]["Article"]["AuthorList"][6][
                    "Identifier"
                ]
            ),
            1,
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][6]["Identifier"][
                0
            ].attributes["Source"],
            "ORCID",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][6]["Identifier"][
                0
            ],
            "https://orcid.org/0000-0003-3525-2788",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][6][
                "AffiliationInfo"
            ][0]["Affiliation"],
            "University of Western Ontario, Robarts Research Institute, London, Ontario, Canada.",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][6][
                "AffiliationInfo"
            ][1]["Affiliation"],
            "University of Western Ontario, Graduate Program in Biomedical Engineering, London, Ontario, Canada.",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][6][
                "AffiliationInfo"
            ][2]["Affiliation"],
            "University of Western Ontario, Department of Medical Biophysics, London, Ontario, Canada.",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][7].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][7]["LastName"],
            "Parraga",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][7]["ForeName"],
            "Grace",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][7]["Initials"],
            "G",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][7][
                "AffiliationInfo"
            ][0]["Affiliation"],
            "University of Western Ontario, Robarts Research Institute, London, Ontario, Canada.",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][7][
                "AffiliationInfo"
            ][1]["Affiliation"],
            "University of Western Ontario, Graduate Program in Biomedical Engineering, London, Ontario, Canada.",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][7][
                "AffiliationInfo"
            ][2]["Affiliation"],
            "University of Western Ontario, Department of Medical Biophysics, London, Ontario, Canada.",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][8].attributes[
                "ValidYN"
            ],
            "Y",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["AuthorList"][8][
                "CollectiveName"
            ],
            "Canadian Respiratory Research Network",
        )
        self.assertEqual(
            len(pubmed_article["MedlineCitation"]["Article"]["Language"]), 1
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["Language"][0], "eng"
        )
        self.assertEqual(
            len(pubmed_article["MedlineCitation"]["Article"]["PublicationTypeList"]), 1
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["PublicationTypeList"][
                0
            ].attributes["UI"],
            "D016428",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["PublicationTypeList"][0],
            "Journal Article",
        )
        self.assertEqual(
            len(pubmed_article["MedlineCitation"]["Article"]["ArticleDate"]), 1
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["ArticleDate"][0].attributes[
                "DateType"
            ],
            "Electronic",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["ArticleDate"][0]["Year"],
            "2018",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["ArticleDate"][0]["Month"],
            "06",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["Article"]["ArticleDate"][0]["Day"], "28"
        )
        self.assertEqual(
            len(pubmed_article["MedlineCitation"]["MedlineJournalInfo"]), 4
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["MedlineJournalInfo"]["Country"],
            "United States",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["MedlineJournalInfo"]["MedlineTA"],
            "J Med Imaging (Bellingham)",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["MedlineJournalInfo"]["NlmUniqueID"],
            "101643461",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["MedlineJournalInfo"]["ISSNLinking"],
            "2329-4302",
        )
        self.assertEqual(len(pubmed_article["MedlineCitation"]["KeywordList"]), 1)
        self.assertEqual(
            pubmed_article["MedlineCitation"]["KeywordList"][0].attributes["Owner"],
            "NOTNLM",
        )
        self.assertEqual(len(pubmed_article["MedlineCitation"]["KeywordList"][0]), 5)
        self.assertEqual(
            pubmed_article["MedlineCitation"]["KeywordList"][0][0].attributes[
                "MajorTopicYN"
            ],
            "N",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["KeywordList"][0][0], "asthma"
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["KeywordList"][0][1].attributes[
                "MajorTopicYN"
            ],
            "N",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["KeywordList"][0][1],
            "chronic obstructive lung disease",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["KeywordList"][0][2].attributes[
                "MajorTopicYN"
            ],
            "N",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["KeywordList"][0][2],
            "image processing, biomarkers",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["KeywordList"][0][3].attributes[
                "MajorTopicYN"
            ],
            "N",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["KeywordList"][0][3],
            "magnetic resonance imaging",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["KeywordList"][0][4].attributes[
                "MajorTopicYN"
            ],
            "N",
        )
        self.assertEqual(
            pubmed_article["MedlineCitation"]["KeywordList"][0][4],
            "thoracic computed tomography",
        )
        self.assertEqual(
            pubmed_article["PubmedData"]["History"][0].attributes["PubStatus"],
            "received",
        )
        self.assertEqual(pubmed_article["PubmedData"]["History"][0]["Year"], "2017")
        self.assertEqual(pubmed_article["PubmedData"]["History"][0]["Month"], "12")
        self.assertEqual(pubmed_article["PubmedData"]["History"][0]["Day"], "12")
        self.assertEqual(
            pubmed_article["PubmedData"]["History"][1].attributes["PubStatus"],
            "accepted",
        )
        self.assertEqual(pubmed_article["PubmedData"]["History"][1]["Year"], "2018")
        self.assertEqual(pubmed_article["PubmedData"]["History"][1]["Month"], "06")
        self.assertEqual(pubmed_article["PubmedData"]["History"][1]["Day"], "14")
        self.assertEqual(
            pubmed_article["PubmedData"]["History"][2].attributes["PubStatus"],
            "pmc-release",
        )
        self.assertEqual(pubmed_article["PubmedData"]["History"][2]["Year"], "2019")
        self.assertEqual(pubmed_article["PubmedData"]["History"][2]["Month"], "06")
        self.assertEqual(pubmed_article["PubmedData"]["History"][2]["Day"], "28")
        self.assertEqual(
            pubmed_article["PubmedData"]["History"][3].attributes["PubStatus"], "entrez"
        )
        self.assertEqual(pubmed_article["PubmedData"]["History"][3]["Year"], "2018")
        self.assertEqual(pubmed_article["PubmedData"]["History"][3]["Month"], "7")
        self.assertEqual(pubmed_article["PubmedData"]["History"][3]["Day"], "3")
        self.assertEqual(pubmed_article["PubmedData"]["History"][3]["Hour"], "6")
        self.assertEqual(pubmed_article["PubmedData"]["History"][3]["Minute"], "0")
        self.assertEqual(
            pubmed_article["PubmedData"]["History"][4].attributes["PubStatus"], "pubmed"
        )
        self.assertEqual(pubmed_article["PubmedData"]["History"][4]["Year"], "2018")
        self.assertEqual(pubmed_article["PubmedData"]["History"][4]["Month"], "7")
        self.assertEqual(pubmed_article["PubmedData"]["History"][4]["Day"], "3")
        self.assertEqual(pubmed_article["PubmedData"]["History"][4]["Hour"], "6")
        self.assertEqual(pubmed_article["PubmedData"]["History"][4]["Minute"], "0")
        self.assertEqual(
            pubmed_article["PubmedData"]["History"][5].attributes["PubStatus"],
            "medline",
        )
        self.assertEqual(pubmed_article["PubmedData"]["History"][5]["Year"], "2018")
        self.assertEqual(pubmed_article["PubmedData"]["History"][5]["Month"], "7")
        self.assertEqual(pubmed_article["PubmedData"]["History"][5]["Day"], "3")
        self.assertEqual(pubmed_article["PubmedData"]["History"][5]["Hour"], "6")
        self.assertEqual(pubmed_article["PubmedData"]["History"][5]["Minute"], "1")
        self.assertEqual(pubmed_article["PubmedData"]["PublicationStatus"], "ppublish")
        self.assertEqual(len(pubmed_article["PubmedData"]["ArticleIdList"]), 4)
        self.assertEqual(
            pubmed_article["PubmedData"]["ArticleIdList"][0].attributes["IdType"],
            "pubmed",
        )
        self.assertEqual(pubmed_article["PubmedData"]["ArticleIdList"][0], "29963580")
        self.assertEqual(
            pubmed_article["PubmedData"]["ArticleIdList"][1].attributes["IdType"], "doi"
        )
        self.assertEqual(
            pubmed_article["PubmedData"]["ArticleIdList"][1], "10.1117/1.JMI.5.2.026002"
        )
        self.assertEqual(
            pubmed_article["PubmedData"]["ArticleIdList"][2].attributes["IdType"], "pii"
        )
        self.assertEqual(pubmed_article["PubmedData"]["ArticleIdList"][2], "17360RR")
        self.assertEqual(
            pubmed_article["PubmedData"]["ArticleIdList"][3].attributes["IdType"], "pmc"
        )
        self.assertEqual(pubmed_article["PubmedData"]["ArticleIdList"][3], "PMC6022861")
        self.assertEqual(len(pubmed_article["PubmedData"]["ReferenceList"]), 1)
        self.assertEqual(len(pubmed_article["PubmedData"]["ReferenceList"][0]), 2)
        self.assertEqual(
            len(pubmed_article["PubmedData"]["ReferenceList"][0]["ReferenceList"]), 0
        )
        references = pubmed_article["PubmedData"]["ReferenceList"][0]["Reference"]
        self.assertEqual(len(references), 49)
        self.assertEqual(references[0]["Citation"], "Radiology. 2015 Jan;274(1):250-9")
        self.assertEqual(len(references[0]["ArticleIdList"]), 1)
        self.assertEqual(references[0]["ArticleIdList"][0], "25144646")
        self.assertEqual(
            references[0]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[1]["Citation"], "Nature. 1994 Jul 21;370(6486):199-201"
        )
        self.assertEqual(len(references[1]["ArticleIdList"]), 1)
        self.assertEqual(references[1]["ArticleIdList"][0], "8028666")
        self.assertEqual(
            references[1]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[2]["Citation"], "Magn Reson Med. 2009 Sep;62(3):656-64"
        )
        self.assertEqual(len(references[2]["ArticleIdList"]), 1)
        self.assertEqual(references[2]["ArticleIdList"][0], "19585597")
        self.assertEqual(
            references[2]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(references[3]["Citation"], "Radiology. 2016 Feb;278(2):563-77")
        self.assertEqual(len(references[3]["ArticleIdList"]), 1)
        self.assertEqual(references[3]["ArticleIdList"][0], "26579733")
        self.assertEqual(
            references[3]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(references[4]["Citation"], "Radiology. 1991 Jun;179(3):777-81")
        self.assertEqual(len(references[4]["ArticleIdList"]), 1)
        self.assertEqual(references[4]["ArticleIdList"][0], "2027991")
        self.assertEqual(
            references[4]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(references[5]["Citation"], "Radiology. 2010 Jul;256(1):280-9")
        self.assertEqual(len(references[5]["ArticleIdList"]), 1)
        self.assertEqual(references[5]["ArticleIdList"][0], "20574101")
        self.assertEqual(
            references[5]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[6]["Citation"], "Phys Med Biol. 2001 May;46(5):R67-99"
        )
        self.assertEqual(len(references[6]["ArticleIdList"]), 1)
        self.assertEqual(references[6]["ArticleIdList"][0], "11384074")
        self.assertEqual(
            references[6]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[7]["Citation"], "IEEE Trans Med Imaging. 2011 Nov;30(11):1901-20"
        )
        self.assertEqual(len(references[7]["ArticleIdList"]), 1)
        self.assertEqual(references[7]["ArticleIdList"][0], "21632295")
        self.assertEqual(
            references[7]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[8]["Citation"], "Eur J Cancer. 2012 Mar;48(4):441-6"
        )
        self.assertEqual(len(references[8]["ArticleIdList"]), 1)
        self.assertEqual(references[8]["ArticleIdList"][0], "22257792")
        self.assertEqual(
            references[8]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[9]["Citation"], "Med Phys. 2017 May;44(5):1718-1733"
        )
        self.assertEqual(len(references[9]["ArticleIdList"]), 1)
        self.assertEqual(references[9]["ArticleIdList"][0], "28206676")
        self.assertEqual(
            references[9]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(references[10]["Citation"], "COPD. 2014 Apr;11(2):125-32")
        self.assertEqual(len(references[10]["ArticleIdList"]), 1)
        self.assertEqual(references[10]["ArticleIdList"][0], "22433011")
        self.assertEqual(
            references[10]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[11]["Citation"],
            "Am J Respir Crit Care Med. 2015 Nov 15;192(10):1215-22",
        )
        self.assertEqual(len(references[11]["ArticleIdList"]), 1)
        self.assertEqual(references[11]["ArticleIdList"][0], "26186608")
        self.assertEqual(
            references[11]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[12]["Citation"], "N Engl J Med. 2016 May 12;374(19):1811-21"
        )
        self.assertEqual(len(references[12]["ArticleIdList"]), 1)
        self.assertEqual(references[12]["ArticleIdList"][0], "27168432")
        self.assertEqual(
            references[12]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[13]["Citation"], "Am J Epidemiol. 2002 Nov 1;156(9):871-81"
        )
        self.assertEqual(len(references[13]["ArticleIdList"]), 1)
        self.assertEqual(references[13]["ArticleIdList"][0], "12397006")
        self.assertEqual(
            references[13]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(references[14]["Citation"], "BMC Cancer. 2014 Dec 11;14:934")
        self.assertEqual(len(references[14]["ArticleIdList"]), 1)
        self.assertEqual(references[14]["ArticleIdList"][0], "25496482")
        self.assertEqual(
            references[14]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[15]["Citation"], "Acad Radiol. 2015 Mar;22(3):320-9"
        )
        self.assertEqual(len(references[15]["ArticleIdList"]), 1)
        self.assertEqual(references[15]["ArticleIdList"][0], "25491735")
        self.assertEqual(
            references[15]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(references[16]["Citation"], "Chest. 1999 Dec;116(6):1750-61")
        self.assertEqual(len(references[16]["ArticleIdList"]), 1)
        self.assertEqual(references[16]["ArticleIdList"][0], "10593802")
        self.assertEqual(
            references[16]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[17]["Citation"], "Acad Radiol. 2012 Feb;19(2):141-52"
        )
        self.assertEqual(len(references[17]["ArticleIdList"]), 1)
        self.assertEqual(references[17]["ArticleIdList"][0], "22104288")
        self.assertEqual(
            references[17]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(references[18]["Citation"], "Med Phys. 2014 Mar;41(3):033502")
        self.assertEqual(len(references[18]["ArticleIdList"]), 1)
        self.assertEqual(references[18]["ArticleIdList"][0], "24593744")
        self.assertEqual(
            references[18]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[19]["Citation"], "Med Phys. 2008 Oct;35(10):4695-707"
        )
        self.assertEqual(len(references[19]["ArticleIdList"]), 1)
        self.assertEqual(references[19]["ArticleIdList"][0], "18975715")
        self.assertEqual(
            references[19]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(references[20]["Citation"], "Thorax. 2017 May;72(5):475-477")
        self.assertEqual(len(references[20]["ArticleIdList"]), 1)
        self.assertEqual(references[20]["ArticleIdList"][0], "28258250")
        self.assertEqual(
            references[20]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(references[21]["Citation"], "Nat Med. 1996 Nov;2(11):1236-9")
        self.assertEqual(len(references[21]["ArticleIdList"]), 1)
        self.assertEqual(references[21]["ArticleIdList"][0], "8898751")
        self.assertEqual(
            references[21]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[22]["Citation"], "J Magn Reson Imaging. 2015 May;41(5):1465-74"
        )
        self.assertEqual(len(references[22]["ArticleIdList"]), 1)
        self.assertEqual(references[22]["ArticleIdList"][0], "24965907")
        self.assertEqual(
            references[22]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[23]["Citation"], "Acad Radiol. 2008 Jun;15(6):776-85"
        )
        self.assertEqual(len(references[23]["ArticleIdList"]), 1)
        self.assertEqual(references[23]["ArticleIdList"][0], "18486013")
        self.assertEqual(
            references[23]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[24]["Citation"], "Magn Reson Med. 2000 Aug;44(2):174-9"
        )
        self.assertEqual(len(references[24]["ArticleIdList"]), 1)
        self.assertEqual(references[24]["ArticleIdList"][0], "10918314")
        self.assertEqual(
            references[24]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[25]["Citation"],
            "Am J Respir Crit Care Med. 2014 Jul 15;190(2):135-44",
        )
        self.assertEqual(len(references[25]["ArticleIdList"]), 1)
        self.assertEqual(references[25]["ArticleIdList"][0], "24873985")
        self.assertEqual(
            references[25]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[26]["Citation"], "Med Phys. 2016 Jun;43(6):2911-2926"
        )
        self.assertEqual(len(references[26]["ArticleIdList"]), 1)
        self.assertEqual(references[26]["ArticleIdList"][0], "27277040")
        self.assertEqual(
            references[26]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(references[27]["Citation"], "Nat Med. 2009 May;15(5):572-6")
        self.assertEqual(len(references[27]["ArticleIdList"]), 1)
        self.assertEqual(references[27]["ArticleIdList"][0], "19377487")
        self.assertEqual(
            references[27]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[28]["Citation"], "Eur J Radiol. 2014 Nov;83(11):2093-101"
        )
        self.assertEqual(len(references[28]["ArticleIdList"]), 1)
        self.assertEqual(references[28]["ArticleIdList"][0], "25176287")
        self.assertEqual(
            references[28]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[29]["Citation"], "Radiology. 2004 Sep;232(3):739-48"
        )
        self.assertEqual(len(references[29]["ArticleIdList"]), 1)
        self.assertEqual(references[29]["ArticleIdList"][0], "15333795")
        self.assertEqual(
            references[29]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[30]["Citation"], "Med Image Anal. 2015 Jul;23(1):43-55"
        )
        self.assertEqual(len(references[30]["ArticleIdList"]), 1)
        self.assertEqual(references[30]["ArticleIdList"][0], "25958028")
        self.assertEqual(
            references[30]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[31]["Citation"], "Radiology. 2015 Oct;277(1):192-205"
        )
        self.assertEqual(len(references[31]["ArticleIdList"]), 1)
        self.assertEqual(references[31]["ArticleIdList"][0], "25961632")
        self.assertEqual(
            references[31]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[32]["Citation"], "Med Image Anal. 2012 Oct;16(7):1423-35"
        )
        self.assertEqual(len(references[32]["ArticleIdList"]), 1)
        self.assertEqual(references[32]["ArticleIdList"][0], "22722056")
        self.assertEqual(
            references[32]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[33]["Citation"], "Radiology. 2016 May;279(2):597-608"
        )
        self.assertEqual(len(references[33]["ArticleIdList"]), 1)
        self.assertEqual(references[33]["ArticleIdList"][0], "26744928")
        self.assertEqual(
            references[33]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[34]["Citation"],
            "J Allergy Clin Immunol. 2003 Jun;111(6):1205-11",
        )
        self.assertEqual(len(references[34]["ArticleIdList"]), 1)
        self.assertEqual(references[34]["ArticleIdList"][0], "12789218")
        self.assertEqual(
            references[34]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[35]["Citation"], "J Magn Reson Imaging. 2016 Mar;43(3):544-57"
        )
        self.assertEqual(len(references[35]["ArticleIdList"]), 1)
        self.assertEqual(references[35]["ArticleIdList"][0], "26199216")
        self.assertEqual(
            references[35]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[36]["Citation"],
            "Am J Respir Crit Care Med. 2016 Oct 1;194(7):794-806",
        )
        self.assertEqual(len(references[36]["ArticleIdList"]), 1)
        self.assertEqual(references[36]["ArticleIdList"][0], "27482984")
        self.assertEqual(
            references[36]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(references[37]["Citation"], "Radiology. 1996 Nov;201(2):564-8")
        self.assertEqual(len(references[37]["ArticleIdList"]), 1)
        self.assertEqual(references[37]["ArticleIdList"][0], "8888259")
        self.assertEqual(
            references[37]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(references[38]["Citation"], "Thorax. 2014 May;69(5):491-4")
        self.assertEqual(len(references[38]["ArticleIdList"]), 1)
        self.assertEqual(references[38]["ArticleIdList"][0], "24029743")
        self.assertEqual(
            references[38]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[39]["Citation"], "J Magn Reson Imaging. 2017 Apr;45(4):1204-1215"
        )
        self.assertEqual(len(references[39]["ArticleIdList"]), 1)
        self.assertEqual(references[39]["ArticleIdList"][0], "27731948")
        self.assertEqual(
            references[39]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[40]["Citation"], "J Appl Physiol (1985). 2009 Oct;107(4):1258-65"
        )
        self.assertEqual(len(references[40]["ArticleIdList"]), 1)
        self.assertEqual(references[40]["ArticleIdList"][0], "19661452")
        self.assertEqual(
            references[40]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[41]["Citation"], "Acad Radiol. 2016 Feb;23(2):176-85"
        )
        self.assertEqual(len(references[41]["ArticleIdList"]), 1)
        self.assertEqual(references[41]["ArticleIdList"][0], "26601971")
        self.assertEqual(
            references[41]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[42]["Citation"], "Radiology. 2018 May;287(2):693-704"
        )
        self.assertEqual(len(references[42]["ArticleIdList"]), 1)
        self.assertEqual(references[42]["ArticleIdList"][0], "29470939")
        self.assertEqual(
            references[42]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[43]["Citation"], "Eur Respir J. 2016 Aug;48(2):370-9"
        )
        self.assertEqual(len(references[43]["ArticleIdList"]), 1)
        self.assertEqual(references[43]["ArticleIdList"][0], "27174885")
        self.assertEqual(
            references[43]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[44]["Citation"], "Radiology. 2011 Oct;261(1):283-92"
        )
        self.assertEqual(len(references[44]["ArticleIdList"]), 1)
        self.assertEqual(references[44]["ArticleIdList"][0], "21813741")
        self.assertEqual(
            references[44]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[45]["Citation"],
            "Am J Respir Crit Care Med. 2014 Mar 15;189(6):650-7",
        )
        self.assertEqual(len(references[45]["ArticleIdList"]), 1)
        self.assertEqual(references[45]["ArticleIdList"][0], "24401150")
        self.assertEqual(
            references[45]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[46]["Citation"],
            "Am J Respir Crit Care Med. 2012 Feb 15;185(4):356-62",
        )
        self.assertEqual(len(references[46]["ArticleIdList"]), 1)
        self.assertEqual(references[46]["ArticleIdList"][0], "22095547")
        self.assertEqual(
            references[46]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(references[47]["Citation"], "COPD. 2010 Feb;7(1):32-43")
        self.assertEqual(len(references[47]["ArticleIdList"]), 1)
        self.assertEqual(references[47]["ArticleIdList"][0], "20214461")
        self.assertEqual(
            references[47]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )
        self.assertEqual(
            references[48]["Citation"], "Eur Respir J. 2008 Apr;31(4):869-73"
        )
        self.assertEqual(len(references[48]["ArticleIdList"]), 1)
        self.assertEqual(references[48]["ArticleIdList"][0], "18216052")
        self.assertEqual(
            references[48]["ArticleIdList"][0].attributes["IdType"], "pubmed"
        )

    def test_pmc(self):
        """Test parsing XML returned by EFetch from PubMed Central."""
        # To create the XML file, use
        # >>> Bio.Entrez.efetch(db='pmc', id="8435807")
        with open("Entrez/efetch_pmc.xml", "rb") as stream:
            records = Entrez.parse(stream)
            records = list(records)
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(len(record), 2)
        self.assertEqual(len(record["front"]), 9)
        self.assertEqual(len(record["front"]["journal-meta"]), 10)
        self.assertEqual(len(record["front"]["journal-meta"]["journal-id"]), 4)
        self.assertEqual(
            record["front"]["journal-meta"]["journal-id"][0], "ERJ Open Res"
        )
        self.assertEqual(
            record["front"]["journal-meta"]["journal-id"][0].attributes,
            {"journal-id-type": "nlm-ta"},
        )
        self.assertEqual(
            record["front"]["journal-meta"]["journal-id"][1], "ERJ Open Res"
        )
        self.assertEqual(
            record["front"]["journal-meta"]["journal-id"][1].attributes,
            {"journal-id-type": "iso-abbrev"},
        )
        self.assertEqual(record["front"]["journal-meta"]["journal-id"][2], "ERJOR")
        self.assertEqual(
            record["front"]["journal-meta"]["journal-id"][2].attributes,
            {"journal-id-type": "publisher-id"},
        )
        self.assertEqual(record["front"]["journal-meta"]["journal-id"][3], "erjor")
        self.assertEqual(
            record["front"]["journal-meta"]["journal-id"][3].attributes,
            {"journal-id-type": "hwp"},
        )
        self.assertEqual(len(record["front"]["journal-meta"]["journal-title-group"]), 1)
        journal_title_group = record["front"]["journal-meta"]["journal-title-group"][0]
        self.assertEqual(len(journal_title_group), 4)
        self.assertEqual(journal_title_group["journal-title"], ["ERJ Open Research"])
        self.assertEqual(journal_title_group["journal-subtitle"], [])
        self.assertEqual(journal_title_group["abbrev-journal-title"], [])
        self.assertEqual(journal_title_group["trans-title-group"], [])
        self.assertEqual(len(record["front"]["journal-meta"]["issn"]), 1)
        self.assertEqual(record["front"]["journal-meta"]["issn"][0], "2312-0541")
        self.assertEqual(
            record["front"]["journal-meta"]["issn"][0].attributes, {"pub-type": "epub"}
        )
        self.assertEqual(len(record["front"]["journal-meta"]["publisher"]), 1)
        self.assertEqual(len(record["front"]["journal-meta"]["publisher"][0]), 1)
        self.assertEqual(
            record["front"]["journal-meta"]["publisher"][0][0],
            "European Respiratory Society",
        )
        self.assertEqual(
            record["front"]["journal-meta"]["publisher"][0][0].tag, "publisher-name"
        )
        self.assertEqual(record["front"]["journal-meta"]["contrib-group"], [])
        self.assertEqual(record["front"]["journal-meta"]["notes"], [])
        self.assertEqual(record["front"]["journal-meta"]["aff"], [])
        self.assertEqual(record["front"]["journal-meta"]["aff-alternatives"], [])
        self.assertEqual(record["front"]["journal-meta"]["self-uri"], [])
        self.assertEqual(record["front"]["journal-meta"]["isbn"], [])
        self.assertEqual(len(record["front"]["article-meta"]), 34)
        self.assertEqual(record["front"]["article-meta"]["abstract"], [])
        self.assertEqual(record["front"]["article-meta"]["funding-group"], [])
        self.assertEqual(record["front"]["article-meta"]["aff"], [])
        self.assertEqual(record["front"]["article-meta"]["issue-title"], [])
        self.assertEqual(len(record["front"]["article-meta"]["pub-date"]), 3)
        self.assertEqual(record["front"]["article-meta"]["pub-date"][0], ["7", "2021"])
        self.assertEqual(
            record["front"]["article-meta"]["pub-date"][0].attributes,
            {"pub-type": "collection"},
        )
        self.assertEqual(
            record["front"]["article-meta"]["pub-date"][1], ["13", "9", "2021"]
        )
        self.assertEqual(
            record["front"]["article-meta"]["pub-date"][1].attributes,
            {"pub-type": "epub"},
        )
        self.assertEqual(
            record["front"]["article-meta"]["pub-date"][2], ["13", "9", "2021"]
        )
        self.assertEqual(
            record["front"]["article-meta"]["pub-date"][2].attributes,
            {"pub-type": "pmc-release"},
        )
        self.assertEqual(record["front"]["article-meta"]["conference"], [])
        self.assertEqual(record["front"]["article-meta"]["supplementary-material"], [])
        self.assertEqual(len(record["front"]["article-meta"]["related-article"]), 1)
        self.assertEqual(record["front"]["article-meta"]["related-article"][0], "")
        self.assertEqual(
            record["front"]["article-meta"]["related-article"][0].attributes,
            {
                "related-article-type": "corrected-article",
                "id": "d31e52",
                "ext-link-type": "doi",
                "http://www.w3.org/1999/xlink href": "10.1183/23120541.00193-2021",
            },
        )
        self.assertEqual(record["front"]["article-meta"]["kwd-group"], [])
        self.assertEqual(record["front"]["article-meta"]["contrib-group"], [])
        self.assertEqual(record["front"]["article-meta"]["issue-sponsor"], [])
        self.assertEqual(record["front"]["article-meta"]["self-uri"], [])
        self.assertEqual(record["front"]["article-meta"]["product"], [])
        self.assertEqual(record["front"]["article-meta"]["issue"], ["3"])
        self.assertEqual(record["front"]["article-meta"]["ext-link"], [])
        self.assertEqual(record["front"]["article-meta"]["support-group"], [])
        self.assertEqual(len(record["front"]["article-meta"]["article-id"]), 4)
        self.assertEqual(record["front"]["article-meta"]["article-id"][0], "34527728")
        self.assertEqual(
            record["front"]["article-meta"]["article-id"][0].attributes,
            {"pub-id-type": "pmid"},
        )
        self.assertEqual(record["front"]["article-meta"]["article-id"][1], "8435807")
        self.assertEqual(
            record["front"]["article-meta"]["article-id"][1].attributes,
            {"pub-id-type": "pmc"},
        )
        self.assertEqual(
            record["front"]["article-meta"]["article-id"][2],
            "10.1183/23120541.50193-2021",
        )
        self.assertEqual(
            record["front"]["article-meta"]["article-id"][2].attributes,
            {"pub-id-type": "doi"},
        )
        self.assertEqual(record["front"]["article-meta"]["article-id"][3], "50193-2021")
        self.assertEqual(
            record["front"]["article-meta"]["article-id"][3].attributes,
            {"pub-id-type": "publisher-id"},
        )
        self.assertEqual(record["front"]["article-meta"]["issue-title-group"], [])
        self.assertEqual(record["front"]["article-meta"]["x"], [])
        self.assertEqual(record["front"]["article-meta"]["uri"], [])
        self.assertEqual(record["front"]["article-meta"]["email"], [])
        self.assertEqual(record["front"]["article-meta"]["volume-id"], [])
        self.assertEqual(record["front"]["article-meta"]["issue-id"], [])
        self.assertEqual(record["front"]["article-meta"]["trans-abstract"], [])
        self.assertEqual(record["front"]["article-meta"]["volume-issue-group"], [])
        self.assertEqual(record["front"]["article-meta"]["related-object"], [])
        self.assertEqual(record["front"]["article-meta"]["isbn"], [])
        self.assertEqual(record["front"]["article-meta"]["volume"], ["7"])
        self.assertEqual(record["front"]["article-meta"]["aff-alternatives"], [])
        self.assertEqual(
            record["front"]["article-meta"]["article-version"], "Version of Record"
        )
        self.assertEqual(
            len(record["front"]["article-meta"]["article-version"].attributes), 3
        )
        self.assertEqual(
            record["front"]["article-meta"]["article-version"].attributes["vocab"],
            "JAV",
        )
        self.assertEqual(
            record["front"]["article-meta"]["article-version"].attributes[
                "vocab-identifier"
            ],
            "http://www.niso.org/publications/rp/RP-8-2008.pdf",
        )
        self.assertEqual(
            record["front"]["article-meta"]["article-version"].attributes[
                "article-version-type"
            ],
            "VoR",
        )
        self.assertEqual(len(record["front"]["article-meta"]["article-categories"]), 3)
        self.assertEqual(
            record["front"]["article-meta"]["article-categories"]["series-text"], []
        )
        self.assertEqual(
            len(record["front"]["article-meta"]["article-categories"]["subj-group"]), 1
        )
        self.assertEqual(
            len(record["front"]["article-meta"]["article-categories"]["subj-group"][0]),
            3,
        )
        self.assertEqual(
            record["front"]["article-meta"]["article-categories"]["subj-group"][0][
                "subject"
            ],
            ["Author Correction"],
        )
        self.assertEqual(
            record["front"]["article-meta"]["article-categories"]["subj-group"][0][
                "subj-group"
            ],
            [],
        )
        self.assertEqual(
            record["front"]["article-meta"]["article-categories"]["subj-group"][0][
                "compound-subject"
            ],
            [],
        )
        self.assertEqual(
            record["front"]["article-meta"]["article-categories"]["subj-group"][
                0
            ].attributes,
            {"subj-group-type": "heading"},
        )
        self.assertEqual(len(record["front"]["article-meta"]["title-group"]), 4)
        self.assertEqual(
            record["front"]["article-meta"]["title-group"]["trans-title-group"], []
        )
        self.assertEqual(
            record["front"]["article-meta"]["title-group"]["alt-title"], []
        )
        self.assertEqual(record["front"]["article-meta"]["title-group"]["subtitle"], [])
        self.assertEqual(
            record["front"]["article-meta"]["title-group"]["article-title"],
            '“Lung diffusing capacity for nitric oxide measured by two commercial devices: a randomised crossover comparison in healthy adults”. Thomas Radtke, Quintin de Groot, Sarah R. Haile, Marion Maggi, Connie C.W. Hsia and Holger Dressel. <italic toggle="yes">ERJ Open Res</italic> 2021; 7: 00193-2021.',
        )
        self.assertEqual(record["front"]["article-meta"]["elocation-id"], "50193-2021")
        self.assertEqual(len(record["front"]["article-meta"]["permissions"]), 5)
        self.assertEqual(
            record["front"]["article-meta"]["permissions"]["copyright-year"], ["2021"]
        )
        self.assertEqual(
            record["front"]["article-meta"]["permissions"]["copyright-holder"], []
        )
        self.assertEqual(
            len(record["front"]["article-meta"]["permissions"]["license"]), 1
        )
        self.assertEqual(
            len(record["front"]["article-meta"]["permissions"]["license"][0]), 2
        )
        self.assertEqual(
            record["front"]["article-meta"]["permissions"]["license"][0][0],
            "https://creativecommons.org/licenses/by-nc/4.0/",
        )
        self.assertEqual(
            record["front"]["article-meta"]["permissions"]["license"][0][0].attributes,
            {"specific-use": "textmining", "content-type": "ccbynclicense"},
        )
        self.assertEqual(
            record["front"]["article-meta"]["permissions"]["license"][0][1],
            'This version is distributed under the terms of the Creative Commons Attribution Non-Commercial Licence 4.0. For commercial reproduction rights and permissions contact <ext-link ext-link-type="uri" http://www.w3.org/1999/xlink href="mailto:permissions@ersnet.org">permissions@ersnet.org</ext-link>',
        )
        self.assertEqual(
            record["front"]["article-meta"]["permissions"]["copyright-statement"],
            ["Copyright ©The authors 2021"],
        )
        self.assertEqual(
            record["front"]["article-meta"]["permissions"]["ali:free_to_read"], []
        )
        self.assertEqual(record["front"]["glossary"], [])
        self.assertEqual(record["front"]["fn-group"], [])
        self.assertEqual(record["front"]["notes"], [])
        self.assertEqual(record["front"]["bio"], [])
        self.assertEqual(record["front"]["list"], [])
        self.assertEqual(record["front"]["def-list"], [])
        self.assertEqual(record["front"]["ack"], [])
        self.assertEqual(len(record["body"]), 37)

        self.assertEqual(record["body"]["table-wrap-group"], [])
        self.assertEqual(record["body"]["disp-formula"], [])
        self.assertEqual(record["body"]["answer-set"], [])
        self.assertEqual(record["body"]["graphic"], [])
        self.assertEqual(record["body"]["statement"], [])
        self.assertEqual(record["body"]["fig-group"], [])
        self.assertEqual(record["body"]["verse-group"], [])
        self.assertEqual(record["body"]["supplementary-material"], [])
        self.assertEqual(record["body"]["related-article"], [])
        self.assertEqual(record["body"]["code"], [])
        self.assertEqual(record["body"]["question"], [])
        self.assertEqual(record["body"]["preformat"], [])
        self.assertEqual(record["body"]["tex-math"], [])
        self.assertEqual(record["body"]["mml:math"], [])
        self.assertEqual(record["body"]["speech"], [])
        self.assertEqual(record["body"]["block-alternatives"], [])
        self.assertEqual(record["body"]["explanation"], [])
        self.assertEqual(record["body"]["array"], [])
        self.assertEqual(record["body"]["question-wrap-group"], [])
        self.assertEqual(record["body"]["alternatives"], [])
        self.assertEqual(record["body"]["media"], [])
        self.assertEqual(record["body"]["x"], [])
        self.assertEqual(record["body"]["sec"], [])
        self.assertEqual(record["body"]["address"], [])
        self.assertEqual(record["body"]["disp-quote"], [])
        self.assertEqual(record["body"]["table-wrap"], [])
        self.assertEqual(record["body"]["ack"], [])
        self.assertEqual(record["body"]["chem-struct-wrap"], [])
        self.assertEqual(record["body"]["related-object"], [])
        self.assertEqual(record["body"]["list"], [])
        self.assertEqual(record["body"]["def-list"], [])
        self.assertEqual(
            record["body"]["p"],
            [
                "This article was originally published with an error in table 2. The upper 95% confidence limit of the per cent difference in the primary end-point (diffusing capacity of the lung for nitric oxide) was incorrectly given as 15.1% and has now been corrected to −15.1% in the published article.\n"
            ],
        )
        self.assertEqual(record["body"]["fig"], [])
        self.assertEqual(record["body"]["answer"], [])
        self.assertEqual(record["body"]["boxed-text"], [])
        self.assertEqual(record["body"]["disp-formula-group"], [])
        self.assertEqual(record["body"]["question-wrap"], [])

    def test_omim(self):
        """Test parsing XML returned by EFetch, OMIM database."""
        # In OMIM show the full record for MIM number 601100 as XML
        # To create the XML file, use
        # >>> Bio.Entrez.efetch(db="omim", id="601100", retmode='xml',
        #                       rettype='full')
        with open("Entrez/ncbi_mim.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(len(record), 1)
        self.assertEqual(record[0]["Mim-entry_mimNumber"], "601100")
        self.assertEqual(record[0]["Mim-entry_mimType"], "1")
        self.assertEqual(record[0]["Mim-entry_mimType"].attributes["value"], "star")
        self.assertEqual(
            record[0]["Mim-entry_title"],
            "STRESS 70 PROTEIN CHAPERONE, MICROSOME-ASSOCIATED, 60-KD; STCH",
        )
        self.assertEqual(
            record[0]["Mim-entry_copyright"],
            "Copyright (c) 1966-2008 Johns Hopkins University",
        )
        self.assertEqual(record[0]["Mim-entry_symbol"], "STCH")
        self.assertEqual(record[0]["Mim-entry_locus"], "21q11.1")
        self.assertEqual(len(record[0]["Mim-entry_text"]), 2)
        self.assertEqual(record[0]["Mim-entry_text"][0]["Mim-text_label"], "TEXT")
        self.assertEqual(
            record[0]["Mim-entry_text"][0]["Mim-text_text"],
            "The stress-70 chaperone family consists of proteins that bind to denatured or incorrectly folded polypeptides and play a major role in the processing of cytosolic and secretory proteins. {2:Otterson et al. (1994)} cloned a human cDNA encoding a predicted 471-amino acid protein (60 kD) which they designated STCH. {1:Brodsky et al. (1995)} stated that the protein sequence is very similar to that of HSP70 ({140550}) and BiP ({138120}). As with other members of the family, the STCH protein contains an ATPase domain at the amino terminus whose activity was shown to be independent of peptide stimulation. The protein was found to be microsome-associated and constitutively expressed in all cell types examined.",
        )
        self.assertEqual(len(record[0]["Mim-entry_text"][0]["Mim-text_neighbors"]), 1)
        self.assertEqual(
            record[0]["Mim-entry_text"][0]["Mim-text_neighbors"]["Mim-link"][
                "Mim-link_num"
            ],
            "30",
        )
        self.assertEqual(
            record[0]["Mim-entry_text"][0]["Mim-text_neighbors"]["Mim-link"][
                "Mim-link_uids"
            ],
            "8131751,9358068,10675567,9488737,8757872,11048651,2559088,10982831,2105497,16572726,9083109,17181539,14508011,15028727,10651811,9108392,11599566,2661019,11836248,7594475,12406544,8536694,12389629,10430932,9177027,9837933,8522346,2928112,12834280,8702658",
        )
        self.assertEqual(
            record[0]["Mim-entry_text"][0]["Mim-text_neighbors"]["Mim-link"][
                "Mim-link_numRelevant"
            ],
            "0",
        )
        self.assertEqual(record[0]["Mim-entry_text"][1]["Mim-text_label"], "TEXT")
        self.assertEqual(
            record[0]["Mim-entry_text"][1]["Mim-text_text"],
            "{1:Brodsky et al. (1995)} mapped the STCH gene to chromosome 21q11.1 with a high-resolution somatic cell hybrid panel for chromosome 21 and by fluorescence in situ hybridization with a YAC containing the gene. By interspecific backcross analysis, {3:Reeves et al. (1998)} mapped the mouse Stch gene to chromosome 16.",
        )
        self.assertEqual(len(record[0]["Mim-entry_text"][1]["Mim-text_neighbors"]), 1)
        self.assertEqual(
            record[0]["Mim-entry_text"][1]["Mim-text_neighbors"]["Mim-link"][
                "Mim-link_num"
            ],
            "30",
        )
        self.assertEqual(
            record[0]["Mim-entry_text"][1]["Mim-text_neighbors"]["Mim-link"][
                "Mim-link_uids"
            ],
            "1354597,8244375,8597637,8838809,9143508,1427875,7806216,9852683,7835904,11060461,10083745,7789175,7806232,7513297,8020937,12014109,1769649,2045096,9747039,8034329,8088815,1783375,8275716,8020959,7956352,8020952,10198174,7655454,8750197,11272792",
        )
        self.assertEqual(
            record[0]["Mim-entry_text"][1]["Mim-text_neighbors"]["Mim-link"][
                "Mim-link_numRelevant"
            ],
            "0",
        )
        self.assertEqual(record[0]["Mim-entry_hasSummary"], "")
        self.assertEqual(record[0]["Mim-entry_hasSummary"].attributes["value"], "false")
        self.assertEqual(record[0]["Mim-entry_hasSynopsis"], "")
        self.assertEqual(
            record[0]["Mim-entry_hasSynopsis"].attributes["value"], "false"
        )
        self.assertEqual(len(record[0]["Mim-entry_editHistory"]), 6)
        self.assertEqual(
            record[0]["Mim-entry_editHistory"][0]["Mim-edit-item_author"], "terry"
        )
        self.assertEqual(
            record[0]["Mim-entry_editHistory"][0]["Mim-edit-item_modDate"]["Mim-date"][
                "Mim-date_year"
            ],
            "1999",
        )
        self.assertEqual(
            record[0]["Mim-entry_editHistory"][0]["Mim-edit-item_modDate"]["Mim-date"][
                "Mim-date_month"
            ],
            "3",
        )
        self.assertEqual(
            record[0]["Mim-entry_editHistory"][0]["Mim-edit-item_modDate"]["Mim-date"][
                "Mim-date_day"
            ],
            "9",
        )
        self.assertEqual(
            record[0]["Mim-entry_editHistory"][1]["Mim-edit-item_author"], "carol"
        )
        self.assertEqual(
            record[0]["Mim-entry_editHistory"][1]["Mim-edit-item_modDate"]["Mim-date"][
                "Mim-date_year"
            ],
            "1999",
        )
        self.assertEqual(
            record[0]["Mim-entry_editHistory"][1]["Mim-edit-item_modDate"]["Mim-date"][
                "Mim-date_month"
            ],
            "3",
        )
        self.assertEqual(
            record[0]["Mim-entry_editHistory"][1]["Mim-edit-item_modDate"]["Mim-date"][
                "Mim-date_day"
            ],
            "7",
        )
        self.assertEqual(
            record[0]["Mim-entry_editHistory"][2]["Mim-edit-item_author"], "carol"
        )
        self.assertEqual(
            record[0]["Mim-entry_editHistory"][2]["Mim-edit-item_modDate"]["Mim-date"][
                "Mim-date_year"
            ],
            "1998",
        )
        self.assertEqual(
            record[0]["Mim-entry_editHistory"][2]["Mim-edit-item_modDate"]["Mim-date"][
                "Mim-date_month"
            ],
            "7",
        )
        self.assertEqual(
            record[0]["Mim-entry_editHistory"][2]["Mim-edit-item_modDate"]["Mim-date"][
                "Mim-date_day"
            ],
            "8",
        )
        self.assertEqual(
            record[0]["Mim-entry_editHistory"][3]["Mim-edit-item_author"], "terry"
        )
        self.assertEqual(
            record[0]["Mim-entry_editHistory"][3]["Mim-edit-item_modDate"]["Mim-date"][
                "Mim-date_year"
            ],
            "1996",
        )
        self.assertEqual(
            record[0]["Mim-entry_editHistory"][3]["Mim-edit-item_modDate"]["Mim-date"][
                "Mim-date_month"
            ],
            "5",
        )
        self.assertEqual(
            record[0]["Mim-entry_editHistory"][3]["Mim-edit-item_modDate"]["Mim-date"][
                "Mim-date_day"
            ],
            "24",
        )
        self.assertEqual(
            record[0]["Mim-entry_editHistory"][4]["Mim-edit-item_author"], "mark"
        )
        self.assertEqual(
            record[0]["Mim-entry_editHistory"][4]["Mim-edit-item_modDate"]["Mim-date"][
                "Mim-date_year"
            ],
            "1996",
        )
        self.assertEqual(
            record[0]["Mim-entry_editHistory"][4]["Mim-edit-item_modDate"]["Mim-date"][
                "Mim-date_month"
            ],
            "3",
        )
        self.assertEqual(
            record[0]["Mim-entry_editHistory"][4]["Mim-edit-item_modDate"]["Mim-date"][
                "Mim-date_day"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["Mim-entry_editHistory"][5]["Mim-edit-item_author"], "mark"
        )
        self.assertEqual(
            record[0]["Mim-entry_editHistory"][5]["Mim-edit-item_modDate"]["Mim-date"][
                "Mim-date_year"
            ],
            "1996",
        )
        self.assertEqual(
            record[0]["Mim-entry_editHistory"][5]["Mim-edit-item_modDate"]["Mim-date"][
                "Mim-date_month"
            ],
            "3",
        )
        self.assertEqual(
            record[0]["Mim-entry_editHistory"][5]["Mim-edit-item_modDate"]["Mim-date"][
                "Mim-date_day"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["Mim-entry_creationDate"]["Mim-edit-item"][
                "Mim-edit-item_author"
            ],
            "Alan F. Scott",
        )
        self.assertEqual(
            record[0]["Mim-entry_creationDate"]["Mim-edit-item"][
                "Mim-edit-item_modDate"
            ]["Mim-date"]["Mim-date_year"],
            "1996",
        )
        self.assertEqual(
            record[0]["Mim-entry_creationDate"]["Mim-edit-item"][
                "Mim-edit-item_modDate"
            ]["Mim-date"]["Mim-date_month"],
            "3",
        )
        self.assertEqual(
            record[0]["Mim-entry_creationDate"]["Mim-edit-item"][
                "Mim-edit-item_modDate"
            ]["Mim-date"]["Mim-date_day"],
            "1",
        )
        self.assertEqual(len(record[0]["Mim-entry_references"]), 3)
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_number"], "1"
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_origNumber"], "1"
        )
        self.assertEqual(record[0]["Mim-entry_references"][0]["Mim-reference_type"], "")
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_type"].attributes[
                "value"
            ],
            "citation",
        )
        self.assertEqual(
            len(record[0]["Mim-entry_references"][0]["Mim-reference_authors"]), 6
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_authors"][0][
                "Mim-author_name"
            ],
            "Brodsky, G.",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_authors"][0][
                "Mim-author_index"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_authors"][1][
                "Mim-author_name"
            ],
            "Otterson, G. A.",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_authors"][1][
                "Mim-author_index"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_authors"][2][
                "Mim-author_name"
            ],
            "Parry, B. B.",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_authors"][2][
                "Mim-author_index"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_authors"][3][
                "Mim-author_name"
            ],
            "Hart, I.",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_authors"][3][
                "Mim-author_index"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_authors"][4][
                "Mim-author_name"
            ],
            "Patterson, D.",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_authors"][4][
                "Mim-author_index"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_authors"][5][
                "Mim-author_name"
            ],
            "Kaye, F. J.",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_authors"][5][
                "Mim-author_index"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_primaryAuthor"],
            "Brodsky",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_otherAuthors"], "et al."
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_citationTitle"],
            "Localization of STCH to human chromosome 21q11.1.",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_citationType"], "0"
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_volume"], "30"
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_journal"], "Genomics"
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_pubDate"]["Mim-date"][
                "Mim-date_year"
            ],
            "1995",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_pubDate"]["Mim-date"][
                "Mim-date_month"
            ],
            "0",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_pubDate"]["Mim-date"][
                "Mim-date_day"
            ],
            "0",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_pages"][0][
                "Mim-page_from"
            ],
            "627",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_pages"][0][
                "Mim-page_to"
            ],
            "628",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_pubmedUID"], "8825657"
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_ambiguous"], ""
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_ambiguous"].attributes[
                "value"
            ],
            "false",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_noLink"], ""
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][0]["Mim-reference_noLink"].attributes[
                "value"
            ],
            "false",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_number"], "2"
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_origNumber"], "2"
        )
        self.assertEqual(record[0]["Mim-entry_references"][1]["Mim-reference_type"], "")
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_type"].attributes[
                "value"
            ],
            "citation",
        )
        self.assertEqual(
            len(record[0]["Mim-entry_references"][1]["Mim-reference_authors"]), 6
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_authors"][0][
                "Mim-author_name"
            ],
            "Otterson, G. A.",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_authors"][0][
                "Mim-author_index"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_authors"][1][
                "Mim-author_name"
            ],
            "Flynn, G. C.",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_authors"][1][
                "Mim-author_index"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_authors"][2][
                "Mim-author_name"
            ],
            "Kratzke, R. A.",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_authors"][2][
                "Mim-author_index"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_authors"][3][
                "Mim-author_name"
            ],
            "Coxon, A.",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_authors"][3][
                "Mim-author_index"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_authors"][4][
                "Mim-author_name"
            ],
            "Johnston, P. G.",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_authors"][4][
                "Mim-author_index"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_authors"][5][
                "Mim-author_name"
            ],
            "Kaye, F. J.",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_authors"][5][
                "Mim-author_index"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_primaryAuthor"],
            "Otterson",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_otherAuthors"], "et al."
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_citationTitle"],
            "Stch encodes the 'ATPase core' of a microsomal stress70 protein.",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_citationType"], "0"
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_volume"], "13"
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_journal"], "EMBO J."
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_pubDate"]["Mim-date"][
                "Mim-date_year"
            ],
            "1994",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_pubDate"]["Mim-date"][
                "Mim-date_month"
            ],
            "0",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_pubDate"]["Mim-date"][
                "Mim-date_day"
            ],
            "0",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_pages"][0][
                "Mim-page_from"
            ],
            "1216",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_pages"][0][
                "Mim-page_to"
            ],
            "1225",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_pubmedUID"], "8131751"
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_ambiguous"], ""
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_ambiguous"].attributes[
                "value"
            ],
            "false",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_noLink"], ""
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][1]["Mim-reference_noLink"].attributes[
                "value"
            ],
            "false",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_number"], "3"
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_origNumber"], "3"
        )
        self.assertEqual(record[0]["Mim-entry_references"][2]["Mim-reference_type"], "")
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_type"].attributes[
                "value"
            ],
            "citation",
        )
        self.assertEqual(
            len(record[0]["Mim-entry_references"][2]["Mim-reference_authors"]), 4
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_authors"][0][
                "Mim-author_name"
            ],
            "Reeves, R. H.",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_authors"][0][
                "Mim-author_index"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_authors"][1][
                "Mim-author_name"
            ],
            "Rue, E.",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_authors"][1][
                "Mim-author_index"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_authors"][2][
                "Mim-author_name"
            ],
            "Yu, J.",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_authors"][2][
                "Mim-author_index"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_authors"][3][
                "Mim-author_name"
            ],
            "Kao, F.-T.",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_authors"][3][
                "Mim-author_index"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_primaryAuthor"],
            "Reeves",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_otherAuthors"], "et al."
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_citationTitle"],
            "Stch maps to mouse chromosome 16, extending the conserved synteny with human chromosome 21.",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_citationType"], "0"
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_volume"], "49"
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_journal"], "Genomics"
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_pubDate"]["Mim-date"][
                "Mim-date_year"
            ],
            "1998",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_pubDate"]["Mim-date"][
                "Mim-date_month"
            ],
            "0",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_pubDate"]["Mim-date"][
                "Mim-date_day"
            ],
            "0",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_pages"][0][
                "Mim-page_from"
            ],
            "156",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_pages"][0][
                "Mim-page_to"
            ],
            "157",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_pubmedUID"], "9570963"
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_ambiguous"], ""
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_ambiguous"].attributes[
                "value"
            ],
            "false",
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_noLink"], ""
        )
        self.assertEqual(
            record[0]["Mim-entry_references"][2]["Mim-reference_noLink"].attributes[
                "value"
            ],
            "false",
        )
        self.assertEqual(
            record[0]["Mim-entry_attribution"][0]["Mim-edit-item_author"],
            "Carol A. Bocchini - updated",
        )
        self.assertEqual(
            record[0]["Mim-entry_attribution"][0]["Mim-edit-item_modDate"]["Mim-date"][
                "Mim-date_year"
            ],
            "1999",
        )
        self.assertEqual(
            record[0]["Mim-entry_attribution"][0]["Mim-edit-item_modDate"]["Mim-date"][
                "Mim-date_month"
            ],
            "3",
        )
        self.assertEqual(
            record[0]["Mim-entry_attribution"][0]["Mim-edit-item_modDate"]["Mim-date"][
                "Mim-date_day"
            ],
            "7",
        )
        self.assertEqual(record[0]["Mim-entry_numGeneMaps"], "1")
        self.assertEqual(len(record[0]["Mim-entry_medlineLinks"]), 1)
        self.assertEqual(
            record[0]["Mim-entry_medlineLinks"]["Mim-link"]["Mim-link_num"], "3"
        )
        self.assertEqual(
            record[0]["Mim-entry_medlineLinks"]["Mim-link"]["Mim-link_uids"],
            "8825657,8131751,9570963",
        )
        self.assertEqual(
            record[0]["Mim-entry_medlineLinks"]["Mim-link"]["Mim-link_numRelevant"], "0"
        )
        self.assertEqual(len(record[0]["Mim-entry_proteinLinks"]), 1)
        self.assertEqual(
            record[0]["Mim-entry_proteinLinks"]["Mim-link"]["Mim-link_num"], "7"
        )
        self.assertEqual(
            record[0]["Mim-entry_proteinLinks"]["Mim-link"]["Mim-link_uids"],
            "148747550,67461586,48928056,30089677,2352621,1351125,460148",
        )
        self.assertEqual(
            record[0]["Mim-entry_proteinLinks"]["Mim-link"]["Mim-link_numRelevant"], "0"
        )
        self.assertEqual(len(record[0]["Mim-entry_nucleotideLinks"]), 1)
        self.assertEqual(
            record[0]["Mim-entry_nucleotideLinks"]["Mim-link"]["Mim-link_num"], "5"
        )
        self.assertEqual(
            record[0]["Mim-entry_nucleotideLinks"]["Mim-link"]["Mim-link_uids"],
            "148747549,55741785,48928055,2352620,460147",
        )
        self.assertEqual(
            record[0]["Mim-entry_nucleotideLinks"]["Mim-link"]["Mim-link_numRelevant"],
            "0",
        )

    def test_taxonomy(self):
        """Test parsing XML returned by EFetch, Taxonomy database."""
        # Access the Taxonomy database using efetch.
        # To create the XML file, use
        # >>> Bio.Entrez.efetch(db="taxonomy", id="9685", retmode="xml")
        with open("Entrez/taxonomy.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(len(record), 1)
        self.assertEqual(record[0]["TaxId"], "9685")
        self.assertEqual(record[0]["ScientificName"], "Felis catus")
        self.assertEqual(record[0]["OtherNames"]["GenbankCommonName"], "domestic cat")
        self.assertEqual(
            record[0]["OtherNames"]["Synonym"][0], "Felis silvestris catus"
        )
        self.assertEqual(record[0]["OtherNames"]["Synonym"][1], "Felis domesticus")
        self.assertEqual(record[0]["OtherNames"]["CommonName"][0], "cat")
        self.assertEqual(record[0]["OtherNames"]["CommonName"][1], "cats")
        self.assertEqual(record[0]["OtherNames"]["Includes"][0], "Korat cats")
        self.assertEqual(record[0]["ParentTaxId"], "9682")
        self.assertEqual(record[0]["Rank"], "species")
        self.assertEqual(record[0]["Division"], "Mammals")
        self.assertEqual(record[0]["GeneticCode"]["GCId"], "1")
        self.assertEqual(record[0]["GeneticCode"]["GCName"], "Standard")
        self.assertEqual(record[0]["MitoGeneticCode"]["MGCId"], "2")
        self.assertEqual(
            record[0]["MitoGeneticCode"]["MGCName"], "Vertebrate Mitochondrial"
        )
        self.assertEqual(
            record[0]["Lineage"],
            "cellular organisms; Eukaryota; Fungi/Metazoa group; Metazoa; Eumetazoa; Bilateria; Coelomata; Deuterostomia; Chordata; Craniata; Vertebrata; Gnathostomata; Teleostomi; Euteleostomi; Sarcopterygii; Tetrapoda; Amniota; Mammalia; Theria; Eutheria; Laurasiatheria; Carnivora; Feliformia; Felidae; Felinae; Felis",
        )

        self.assertEqual(record[0]["LineageEx"][0]["TaxId"], "131567")
        self.assertEqual(
            record[0]["LineageEx"][0]["ScientificName"], "cellular organisms"
        )
        self.assertEqual(record[0]["LineageEx"][0]["Rank"], "no rank")
        self.assertEqual(record[0]["LineageEx"][1]["TaxId"], "2759")
        self.assertEqual(record[0]["LineageEx"][1]["ScientificName"], "Eukaryota")
        self.assertEqual(record[0]["LineageEx"][1]["Rank"], "superkingdom")
        self.assertEqual(record[0]["LineageEx"][2]["TaxId"], "33154")
        self.assertEqual(
            record[0]["LineageEx"][2]["ScientificName"], "Fungi/Metazoa group"
        )
        self.assertEqual(record[0]["LineageEx"][2]["Rank"], "no rank")
        self.assertEqual(record[0]["LineageEx"][3]["TaxId"], "33208")
        self.assertEqual(record[0]["LineageEx"][3]["ScientificName"], "Metazoa")
        self.assertEqual(record[0]["LineageEx"][3]["Rank"], "kingdom")
        self.assertEqual(record[0]["LineageEx"][4]["TaxId"], "6072")
        self.assertEqual(record[0]["LineageEx"][4]["ScientificName"], "Eumetazoa")
        self.assertEqual(record[0]["LineageEx"][4]["Rank"], "no rank")
        self.assertEqual(record[0]["LineageEx"][5]["TaxId"], "33213")
        self.assertEqual(record[0]["LineageEx"][5]["ScientificName"], "Bilateria")
        self.assertEqual(record[0]["LineageEx"][5]["Rank"], "no rank")
        self.assertEqual(record[0]["LineageEx"][6]["TaxId"], "33316")
        self.assertEqual(record[0]["LineageEx"][6]["ScientificName"], "Coelomata")
        self.assertEqual(record[0]["LineageEx"][6]["Rank"], "no rank")
        self.assertEqual(record[0]["LineageEx"][7]["TaxId"], "33511")
        self.assertEqual(record[0]["LineageEx"][7]["ScientificName"], "Deuterostomia")
        self.assertEqual(record[0]["LineageEx"][7]["Rank"], "no rank")
        self.assertEqual(record[0]["LineageEx"][8]["TaxId"], "7711")
        self.assertEqual(record[0]["LineageEx"][8]["ScientificName"], "Chordata")
        self.assertEqual(record[0]["LineageEx"][8]["Rank"], "phylum")
        self.assertEqual(record[0]["LineageEx"][9]["TaxId"], "89593")
        self.assertEqual(record[0]["LineageEx"][9]["ScientificName"], "Craniata")
        self.assertEqual(record[0]["LineageEx"][9]["Rank"], "subphylum")
        self.assertEqual(record[0]["LineageEx"][10]["TaxId"], "7742")
        self.assertEqual(record[0]["LineageEx"][10]["ScientificName"], "Vertebrata")
        self.assertEqual(record[0]["LineageEx"][10]["Rank"], "no rank")
        self.assertEqual(record[0]["LineageEx"][11]["TaxId"], "7776")
        self.assertEqual(record[0]["LineageEx"][11]["ScientificName"], "Gnathostomata")
        self.assertEqual(record[0]["LineageEx"][11]["Rank"], "superclass")
        self.assertEqual(record[0]["LineageEx"][12]["TaxId"], "117570")
        self.assertEqual(record[0]["LineageEx"][12]["ScientificName"], "Teleostomi")
        self.assertEqual(record[0]["LineageEx"][12]["Rank"], "no rank")
        self.assertEqual(record[0]["LineageEx"][13]["TaxId"], "117571")
        self.assertEqual(record[0]["LineageEx"][13]["ScientificName"], "Euteleostomi")
        self.assertEqual(record[0]["LineageEx"][13]["Rank"], "no rank")
        self.assertEqual(record[0]["LineageEx"][14]["TaxId"], "8287")
        self.assertEqual(record[0]["LineageEx"][14]["ScientificName"], "Sarcopterygii")
        self.assertEqual(record[0]["LineageEx"][14]["Rank"], "no rank")
        self.assertEqual(record[0]["LineageEx"][15]["TaxId"], "32523")
        self.assertEqual(record[0]["LineageEx"][15]["ScientificName"], "Tetrapoda")
        self.assertEqual(record[0]["LineageEx"][15]["Rank"], "no rank")
        self.assertEqual(record[0]["LineageEx"][16]["TaxId"], "32524")
        self.assertEqual(record[0]["LineageEx"][16]["ScientificName"], "Amniota")
        self.assertEqual(record[0]["LineageEx"][16]["Rank"], "no rank")
        self.assertEqual(record[0]["LineageEx"][17]["TaxId"], "40674")
        self.assertEqual(record[0]["LineageEx"][17]["ScientificName"], "Mammalia")
        self.assertEqual(record[0]["LineageEx"][17]["Rank"], "class")
        self.assertEqual(record[0]["LineageEx"][18]["TaxId"], "32525")
        self.assertEqual(record[0]["LineageEx"][18]["ScientificName"], "Theria")
        self.assertEqual(record[0]["LineageEx"][18]["Rank"], "no rank")
        self.assertEqual(record[0]["LineageEx"][19]["TaxId"], "9347")
        self.assertEqual(record[0]["LineageEx"][19]["ScientificName"], "Eutheria")
        self.assertEqual(record[0]["LineageEx"][19]["Rank"], "no rank")
        self.assertEqual(record[0]["LineageEx"][20]["TaxId"], "314145")
        self.assertEqual(record[0]["LineageEx"][20]["ScientificName"], "Laurasiatheria")
        self.assertEqual(record[0]["LineageEx"][20]["Rank"], "superorder")
        self.assertEqual(record[0]["LineageEx"][21]["TaxId"], "33554")
        self.assertEqual(record[0]["LineageEx"][21]["ScientificName"], "Carnivora")
        self.assertEqual(record[0]["LineageEx"][21]["Rank"], "order")
        self.assertEqual(record[0]["LineageEx"][22]["TaxId"], "379583")
        self.assertEqual(record[0]["LineageEx"][22]["ScientificName"], "Feliformia")
        self.assertEqual(record[0]["LineageEx"][22]["Rank"], "suborder")
        self.assertEqual(record[0]["LineageEx"][23]["TaxId"], "9681")
        self.assertEqual(record[0]["LineageEx"][23]["ScientificName"], "Felidae")
        self.assertEqual(record[0]["LineageEx"][23]["Rank"], "family")
        self.assertEqual(record[0]["LineageEx"][24]["TaxId"], "338152")
        self.assertEqual(record[0]["LineageEx"][24]["ScientificName"], "Felinae")
        self.assertEqual(record[0]["LineageEx"][24]["Rank"], "subfamily")
        self.assertEqual(record[0]["LineageEx"][25]["TaxId"], "9682")
        self.assertEqual(record[0]["LineageEx"][25]["ScientificName"], "Felis")
        self.assertEqual(record[0]["LineageEx"][25]["Rank"], "genus")
        self.assertEqual(record[0]["CreateDate"], "1995/02/27")
        self.assertEqual(record[0]["UpdateDate"], "2007/09/04")
        self.assertEqual(record[0]["PubDate"], "1993/07/26")

    def test_nucleotide1(self):
        """Test parsing XML returned by EFetch, Nucleotide database (first test)."""
        # Access the nucleotide database using efetch.
        # To create the XML file, use
        # >>> Bio.Entrez.efetch(db='nucleotide', id=5, retmode='xml')
        with open("Entrez/nucleotide1.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record[0]["GBSeq_locus"], "X60065")
        self.assertEqual(record[0]["GBSeq_length"], "1136")
        self.assertEqual(record[0]["GBSeq_strandedness"], "single")
        self.assertEqual(record[0]["GBSeq_moltype"], "mRNA")
        self.assertEqual(record[0]["GBSeq_topology"], "linear")
        self.assertEqual(record[0]["GBSeq_division"], "MAM")
        self.assertEqual(record[0]["GBSeq_update-date"], "14-NOV-2006")
        self.assertEqual(record[0]["GBSeq_create-date"], "05-MAY-1992")
        self.assertEqual(
            record[0]["GBSeq_definition"],
            "B.bovis beta-2-gpI mRNA for beta-2-glycoprotein I",
        )
        self.assertEqual(record[0]["GBSeq_primary-accession"], "X60065")
        self.assertEqual(record[0]["GBSeq_accession-version"], "X60065.1")
        self.assertEqual(record[0]["GBSeq_other-seqids"][0], "emb|X60065.1|")
        self.assertEqual(record[0]["GBSeq_other-seqids"][1], "gi|5")
        self.assertEqual(record[0]["GBSeq_keywords"][0], "beta-2 glycoprotein I")
        self.assertEqual(record[0]["GBSeq_source"], "Bos taurus (cattle)")
        self.assertEqual(record[0]["GBSeq_organism"], "Bos taurus")
        self.assertEqual(
            record[0]["GBSeq_taxonomy"],
            "Eukaryota; Metazoa; Chordata; Craniata; Vertebrata; Euteleostomi; Mammalia; Eutheria; Laurasiatheria; Cetartiodactyla; Ruminantia; Pecora; Bovidae; Bovinae; Bos",
        )
        self.assertEqual(record[0]["GBSeq_references"][0]["GBReference_reference"], "1")
        self.assertEqual(
            record[0]["GBSeq_references"][0]["GBReference_authors"][0], "Bendixen,E."
        )
        self.assertEqual(
            record[0]["GBSeq_references"][0]["GBReference_authors"][1], "Halkier,T."
        )
        self.assertEqual(
            record[0]["GBSeq_references"][0]["GBReference_authors"][2], "Magnusson,S."
        )
        self.assertEqual(
            record[0]["GBSeq_references"][0]["GBReference_authors"][3],
            "Sottrup-Jensen,L.",
        )
        self.assertEqual(
            record[0]["GBSeq_references"][0]["GBReference_authors"][4], "Kristensen,T."
        )
        self.assertEqual(
            record[0]["GBSeq_references"][0]["GBReference_title"],
            "Complete primary structure of bovine beta 2-glycoprotein I: localization of the disulfide bridges",
        )
        self.assertEqual(
            record[0]["GBSeq_references"][0]["GBReference_journal"],
            "Biochemistry 31 (14), 3611-3617 (1992)",
        )
        self.assertEqual(
            record[0]["GBSeq_references"][0]["GBReference_pubmed"], "1567819"
        )
        self.assertEqual(record[0]["GBSeq_references"][1]["GBReference_reference"], "2")
        self.assertEqual(
            record[0]["GBSeq_references"][1]["GBReference_position"], "1..1136"
        )
        self.assertEqual(
            record[0]["GBSeq_references"][1]["GBReference_authors"][0], "Kristensen,T."
        )
        self.assertEqual(
            record[0]["GBSeq_references"][1]["GBReference_title"], "Direct Submission"
        )
        self.assertEqual(
            record[0]["GBSeq_references"][1]["GBReference_journal"],
            "Submitted (11-JUN-1991) T. Kristensen, Dept of Mol Biology, University of Aarhus, C F Mollers Alle 130, DK-8000 Aarhus C, DENMARK",
        )
        self.assertEqual(len(record[0]["GBSeq_feature-table"]), 7)
        self.assertEqual(record[0]["GBSeq_feature-table"][0]["GBFeature_key"], "source")
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_location"], "1..1136"
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_intervals"][0][
                "GBInterval_from"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_intervals"][0][
                "GBInterval_to"
            ],
            "1136",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_intervals"][0][
                "GBInterval_accession"
            ],
            "X60065.1",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_quals"][0][
                "GBQualifier_name"
            ],
            "organism",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_quals"][0][
                "GBQualifier_value"
            ],
            "Bos taurus",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_quals"][1][
                "GBQualifier_name"
            ],
            "mol_type",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_quals"][1][
                "GBQualifier_value"
            ],
            "mRNA",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_quals"][2][
                "GBQualifier_name"
            ],
            "db_xref",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_quals"][2][
                "GBQualifier_value"
            ],
            "taxon:9913",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_quals"][3][
                "GBQualifier_name"
            ],
            "clone",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_quals"][3][
                "GBQualifier_value"
            ],
            "pBB2I",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_quals"][4][
                "GBQualifier_name"
            ],
            "tissue_type",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_quals"][4][
                "GBQualifier_value"
            ],
            "liver",
        )
        self.assertEqual(record[0]["GBSeq_feature-table"][1]["GBFeature_key"], "gene")
        self.assertEqual(
            record[0]["GBSeq_feature-table"][1]["GBFeature_location"], "<1..1136"
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][1]["GBFeature_intervals"][0][
                "GBInterval_from"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][1]["GBFeature_intervals"][0][
                "GBInterval_to"
            ],
            "1136",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][1]["GBFeature_intervals"][0][
                "GBInterval_accession"
            ],
            "X60065.1",
        )
        self.assertEqual(record[0]["GBSeq_feature-table"][1]["GBFeature_partial5"], "")
        self.assertEqual(
            record[0]["GBSeq_feature-table"][1]["GBFeature_partial5"].attributes[
                "value"
            ],
            "true",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][1]["GBFeature_quals"][0][
                "GBQualifier_name"
            ],
            "gene",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][1]["GBFeature_quals"][0][
                "GBQualifier_value"
            ],
            "beta-2-gpI",
        )
        self.assertEqual(record[0]["GBSeq_feature-table"][2]["GBFeature_key"], "CDS")
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_location"], "<1..1029"
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_intervals"][0][
                "GBInterval_from"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_intervals"][0][
                "GBInterval_to"
            ],
            "1029",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_intervals"][0][
                "GBInterval_accession"
            ],
            "X60065.1",
        )
        self.assertEqual(record[0]["GBSeq_feature-table"][2]["GBFeature_partial5"], "")
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_partial5"].attributes[
                "value"
            ],
            "true",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_quals"][0][
                "GBQualifier_name"
            ],
            "gene",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_quals"][0][
                "GBQualifier_value"
            ],
            "beta-2-gpI",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_quals"][1][
                "GBQualifier_name"
            ],
            "codon_start",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_quals"][1][
                "GBQualifier_value"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_quals"][2][
                "GBQualifier_name"
            ],
            "transl_table",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_quals"][2][
                "GBQualifier_value"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_quals"][3][
                "GBQualifier_name"
            ],
            "product",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_quals"][3][
                "GBQualifier_value"
            ],
            "beta-2-glycoprotein I",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_quals"][4][
                "GBQualifier_name"
            ],
            "protein_id",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_quals"][4][
                "GBQualifier_value"
            ],
            "CAA42669.1",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_quals"][5][
                "GBQualifier_name"
            ],
            "db_xref",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_quals"][5][
                "GBQualifier_value"
            ],
            "GI:6",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_quals"][6][
                "GBQualifier_name"
            ],
            "db_xref",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_quals"][6][
                "GBQualifier_value"
            ],
            "GOA:P17690",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_quals"][7][
                "GBQualifier_name"
            ],
            "db_xref",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_quals"][7][
                "GBQualifier_value"
            ],
            "UniProtKB/Swiss-Prot:P17690",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_quals"][8][
                "GBQualifier_name"
            ],
            "translation",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_quals"][8][
                "GBQualifier_value"
            ],
            "PALVLLLGFLCHVAIAGRTCPKPDELPFSTVVPLKRTYEPGEQIVFSCQPGYVSRGGIRRFTCPLTGLWPINTLKCMPRVCPFAGILENGTVRYTTFEYPNTISFSCHTGFYLKGASSAKCTEEGKWSPDLPVCAPITCPPPPIPKFASLSVYKPLAGNNSFYGSKAVFKCLPHHAMFGNDTVTCTEHGNWTQLPECREVRCPFPSRPDNGFVNHPANPVLYYKDTATFGCHETYSLDGPEEVECSKFGNWSAQPSCKASCKLSIKRATVIYEGERVAIQNKFKNGMLHGQKVSFFCKHKEKKCSYTEDAQCIDGTIEIPKCFKEHSSLAFWKTDASDVKPC",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][3]["GBFeature_key"], "sig_peptide"
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][3]["GBFeature_location"], "<1..48"
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][3]["GBFeature_intervals"][0][
                "GBInterval_from"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][3]["GBFeature_intervals"][0][
                "GBInterval_to"
            ],
            "48",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][3]["GBFeature_intervals"][0][
                "GBInterval_accession"
            ],
            "X60065.1",
        )
        self.assertEqual(record[0]["GBSeq_feature-table"][3]["GBFeature_partial5"], "")
        self.assertEqual(
            record[0]["GBSeq_feature-table"][3]["GBFeature_partial5"].attributes[
                "value"
            ],
            "true",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][3]["GBFeature_quals"][0][
                "GBQualifier_name"
            ],
            "gene",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][3]["GBFeature_quals"][0][
                "GBQualifier_value"
            ],
            "beta-2-gpI",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][4]["GBFeature_key"], "mat_peptide"
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][4]["GBFeature_location"], "49..1026"
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][4]["GBFeature_intervals"][0][
                "GBInterval_from"
            ],
            "49",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][4]["GBFeature_intervals"][0][
                "GBInterval_to"
            ],
            "1026",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][4]["GBFeature_intervals"][0][
                "GBInterval_accession"
            ],
            "X60065.1",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][4]["GBFeature_quals"][0][
                "GBQualifier_name"
            ],
            "gene",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][4]["GBFeature_quals"][0][
                "GBQualifier_value"
            ],
            "beta-2-gpI",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][4]["GBFeature_quals"][1][
                "GBQualifier_name"
            ],
            "product",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][4]["GBFeature_quals"][1][
                "GBQualifier_value"
            ],
            "beta-2-glycoprotein I",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][5]["GBFeature_key"], "polyA_signal"
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][5]["GBFeature_location"], "1101..1106"
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][5]["GBFeature_intervals"][0][
                "GBInterval_from"
            ],
            "1101",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][5]["GBFeature_intervals"][0][
                "GBInterval_to"
            ],
            "1106",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][5]["GBFeature_intervals"][0][
                "GBInterval_accession"
            ],
            "X60065.1",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][5]["GBFeature_quals"][0][
                "GBQualifier_name"
            ],
            "gene",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][5]["GBFeature_quals"][0][
                "GBQualifier_value"
            ],
            "beta-2-gpI",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][6]["GBFeature_key"], "polyA_site"
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][6]["GBFeature_location"], "1130"
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][6]["GBFeature_intervals"][0][
                "GBInterval_point"
            ],
            "1130",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][6]["GBFeature_intervals"][0][
                "GBInterval_accession"
            ],
            "X60065.1",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][6]["GBFeature_quals"][0][
                "GBQualifier_name"
            ],
            "gene",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][6]["GBFeature_quals"][0][
                "GBQualifier_value"
            ],
            "beta-2-gpI",
        )
        self.assertEqual(
            record[0]["GBSeq_sequence"],
            "ccagcgctcgtcttgctgttggggtttctctgccacgttgctatcgcaggacgaacctgccccaagccagatgagctaccgttttccacggtggttccactgaaacggacctatgagcccggggagcagatagtcttctcctgccagccgggctacgtgtcccggggagggatccggcggtttacatgcccgctcacaggactctggcccatcaacacgctgaaatgcatgcccagagtatgtccttttgctgggatcttagaaaacggaacggtacgctatacaacgtttgagtatcccaacaccatcagcttttcttgccacacggggttttatctgaaaggagctagttctgcaaaatgcactgaggaagggaagtggagcccagaccttcctgtctgtgcccctataacctgccctccaccacccatacccaagtttgcaagtctcagcgtttacaagccgttggctgggaacaactccttctatggcagcaaggcagtctttaagtgcttgccacaccacgcgatgtttggaaatgacaccgttacctgcacggaacatgggaactggacgcagttgccagaatgcagggaagtaagatgcccattcccatcaagaccagacaatgggtttgtgaaccatcctgcaaatccagtgctctactataaggacaccgccacctttggctgccatgaaacgtattccttggatggaccggaagaagtagaatgcagcaaattcggaaactggtctgcacagccaagctgtaaagcatcttgtaagttatctattaaaagagctactgtgatatatgaaggagagagagtagctatccagaacaaatttaagaatggaatgctgcatggccaaaaggtttctttcttctgcaagcataaggaaaagaagtgcagctacacagaagatgctcagtgcatagacggcaccatcgagattcccaaatgcttcaaggagcacagttctttagctttctggaaaacggatgcatctgacgtaaaaccatgctaagctggttttcacactgaaaattaaatgtcatgcttatatgtgtctgtctgagaatctgatggaaacggaaaaataaagagactgaatttaccgtgtcaagaaaaaaa",
        )

    def test_nucleotide2(self):
        """Test parsing XML returned by EFetch, Nucleotide database (second test)."""
        # Access the nucleotide database using efetch.
        # To create the XML file, use
        # >>> Bio.Entrez.efetch(db='nucleotide', id=5,
        #                       rettype='fasta', complexity=0, retmode='xml')
        with open("Entrez/nucleotide2.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record[0]["TSeq_seqtype"], "")
        self.assertEqual(record[0]["TSeq_seqtype"].attributes["value"], "nucleotide")
        self.assertEqual(record[0]["TSeq_gi"], "5")
        self.assertEqual(record[0]["TSeq_accver"], "X60065.1")
        self.assertEqual(record[0]["TSeq_taxid"], "9913")
        self.assertEqual(record[0]["TSeq_orgname"], "Bos taurus")
        self.assertEqual(
            record[0]["TSeq_defline"],
            "B.bovis beta-2-gpI mRNA for beta-2-glycoprotein I",
        )
        self.assertEqual(record[0]["TSeq_length"], "1136")
        self.assertEqual(
            record[0]["TSeq_sequence"],
            "CCAGCGCTCGTCTTGCTGTTGGGGTTTCTCTGCCACGTTGCTATCGCAGGACGAACCTGCCCCAAGCCAGATGAGCTACCGTTTTCCACGGTGGTTCCACTGAAACGGACCTATGAGCCCGGGGAGCAGATAGTCTTCTCCTGCCAGCCGGGCTACGTGTCCCGGGGAGGGATCCGGCGGTTTACATGCCCGCTCACAGGACTCTGGCCCATCAACACGCTGAAATGCATGCCCAGAGTATGTCCTTTTGCTGGGATCTTAGAAAACGGAACGGTACGCTATACAACGTTTGAGTATCCCAACACCATCAGCTTTTCTTGCCACACGGGGTTTTATCTGAAAGGAGCTAGTTCTGCAAAATGCACTGAGGAAGGGAAGTGGAGCCCAGACCTTCCTGTCTGTGCCCCTATAACCTGCCCTCCACCACCCATACCCAAGTTTGCAAGTCTCAGCGTTTACAAGCCGTTGGCTGGGAACAACTCCTTCTATGGCAGCAAGGCAGTCTTTAAGTGCTTGCCACACCACGCGATGTTTGGAAATGACACCGTTACCTGCACGGAACATGGGAACTGGACGCAGTTGCCAGAATGCAGGGAAGTAAGATGCCCATTCCCATCAAGACCAGACAATGGGTTTGTGAACCATCCTGCAAATCCAGTGCTCTACTATAAGGACACCGCCACCTTTGGCTGCCATGAAACGTATTCCTTGGATGGACCGGAAGAAGTAGAATGCAGCAAATTCGGAAACTGGTCTGCACAGCCAAGCTGTAAAGCATCTTGTAAGTTATCTATTAAAAGAGCTACTGTGATATATGAAGGAGAGAGAGTAGCTATCCAGAACAAATTTAAGAATGGAATGCTGCATGGCCAAAAGGTTTCTTTCTTCTGCAAGCATAAGGAAAAGAAGTGCAGCTACACAGAAGATGCTCAGTGCATAGACGGCACCATCGAGATTCCCAAATGCTTCAAGGAGCACAGTTCTTTAGCTTTCTGGAAAACGGATGCATCTGACGTAAAACCATGCTAAGCTGGTTTTCACACTGAAAATTAAATGTCATGCTTATATGTGTCTGTCTGAGAATCTGATGGAAACGGAAAAATAAAGAGACTGAATTTACCGTGTCAAGAAAAAAA",
        )
        self.assertEqual(record[1]["TSeq_seqtype"], "")
        self.assertEqual(record[1]["TSeq_seqtype"].attributes["value"], "protein")
        self.assertEqual(record[1]["TSeq_gi"], "6")
        self.assertEqual(record[1]["TSeq_accver"], "CAA42669.1")
        self.assertEqual(record[1]["TSeq_taxid"], "9913")
        self.assertEqual(record[1]["TSeq_orgname"], "Bos taurus")
        self.assertEqual(
            record[1]["TSeq_defline"], "beta-2-glycoprotein I [Bos taurus]"
        )
        self.assertEqual(record[1]["TSeq_length"], "342")
        self.assertEqual(
            record[1]["TSeq_sequence"],
            "PALVLLLGFLCHVAIAGRTCPKPDELPFSTVVPLKRTYEPGEQIVFSCQPGYVSRGGIRRFTCPLTGLWPINTLKCMPRVCPFAGILENGTVRYTTFEYPNTISFSCHTGFYLKGASSAKCTEEGKWSPDLPVCAPITCPPPPIPKFASLSVYKPLAGNNSFYGSKAVFKCLPHHAMFGNDTVTCTEHGNWTQLPECREVRCPFPSRPDNGFVNHPANPVLYYKDTATFGCHETYSLDGPEEVECSKFGNWSAQPSCKASCKLSIKRATVIYEGERVAIQNKFKNGMLHGQKVSFFCKHKEKKCSYTEDAQCIDGTIEIPKCFKEHSSLAFWKTDASDVKPC",
        )

    def test_protein(self):
        """Test parsing XML returned by EFetch, Protein database."""
        # Access the protein database using efetch.
        # To create the XML file, use
        # >>> Bio.Entrez.efetch(db='protein', id=8, rettype='gp', retmode='xml')
        with open("Entrez/protein.xml", "rb") as stream:
            record = Entrez.read(stream)
        self.assertEqual(record[0]["GBSeq_locus"], "CAA35997")
        self.assertEqual(record[0]["GBSeq_length"], "100")
        self.assertEqual(record[0]["GBSeq_moltype"], "AA")
        self.assertEqual(record[0]["GBSeq_topology"], "linear")
        self.assertEqual(record[0]["GBSeq_division"], "MAM")
        self.assertEqual(record[0]["GBSeq_update-date"], "12-SEP-1993")
        self.assertEqual(record[0]["GBSeq_create-date"], "03-APR-1990")
        self.assertEqual(
            record[0]["GBSeq_definition"], "unnamed protein product [Bos taurus]"
        )
        self.assertEqual(record[0]["GBSeq_primary-accession"], "CAA35997")
        self.assertEqual(record[0]["GBSeq_accession-version"], "CAA35997.1")
        self.assertEqual(record[0]["GBSeq_other-seqids"][0], "emb|CAA35997.1|")
        self.assertEqual(record[0]["GBSeq_other-seqids"][1], "gi|8")
        self.assertEqual(record[0]["GBSeq_source"], "Bos taurus (cattle)")
        self.assertEqual(record[0]["GBSeq_organism"], "Bos taurus")
        self.assertEqual(
            record[0]["GBSeq_taxonomy"],
            "Eukaryota; Metazoa; Chordata; Craniata; Vertebrata; Euteleostomi; Mammalia; Eutheria; Laurasiatheria; Cetartiodactyla; Ruminantia; Pecora; Bovidae; Bovinae; Bos",
        )
        self.assertEqual(record[0]["GBSeq_references"][0]["GBReference_reference"], "1")
        self.assertEqual(
            record[0]["GBSeq_references"][0]["GBReference_position"], "1..100"
        )
        self.assertEqual(
            record[0]["GBSeq_references"][0]["GBReference_authors"][0], "Kiefer,M.C."
        )
        self.assertEqual(
            record[0]["GBSeq_references"][0]["GBReference_authors"][1], "Saphire,A.C.S."
        )
        self.assertEqual(
            record[0]["GBSeq_references"][0]["GBReference_authors"][2], "Bauer,D.M."
        )
        self.assertEqual(
            record[0]["GBSeq_references"][0]["GBReference_authors"][3], "Barr,P.J."
        )
        self.assertEqual(
            record[0]["GBSeq_references"][0]["GBReference_journal"], "Unpublished"
        )
        self.assertEqual(record[0]["GBSeq_references"][1]["GBReference_reference"], "2")
        self.assertEqual(
            record[0]["GBSeq_references"][1]["GBReference_position"], "1..100"
        )
        self.assertEqual(
            record[0]["GBSeq_references"][1]["GBReference_authors"][0], "Kiefer,M.C."
        )
        self.assertEqual(
            record[0]["GBSeq_references"][1]["GBReference_title"], "Direct Submission"
        )
        self.assertEqual(
            record[0]["GBSeq_references"][1]["GBReference_journal"],
            "Submitted (30-JAN-1990) Kiefer M.C., Chiron Corporation, 4560 Hortom St, Emeryville CA 94608-2916, U S A",
        )
        self.assertEqual(
            record[0]["GBSeq_comment"],
            "See <X15699> for Human sequence.~Data kindly reviewed (08-MAY-1990) by Kiefer M.C.",
        )
        self.assertEqual(record[0]["GBSeq_source-db"], "embl accession X51700.1")
        self.assertEqual(record[0]["GBSeq_feature-table"][0]["GBFeature_key"], "source")
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_location"], "1..100"
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_intervals"][0][
                "GBInterval_from"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_intervals"][0][
                "GBInterval_to"
            ],
            "100",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_intervals"][0][
                "GBInterval_accession"
            ],
            "CAA35997.1",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_quals"][0][
                "GBQualifier_name"
            ],
            "organism",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_quals"][0][
                "GBQualifier_value"
            ],
            "Bos taurus",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_quals"][1][
                "GBQualifier_name"
            ],
            "db_xref",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_quals"][1][
                "GBQualifier_value"
            ],
            "taxon:9913",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_quals"][2][
                "GBQualifier_name"
            ],
            "clone",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_quals"][2][
                "GBQualifier_value"
            ],
            "bBGP-3",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_quals"][3][
                "GBQualifier_name"
            ],
            "tissue_type",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_quals"][3][
                "GBQualifier_value"
            ],
            "bone matrix",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_quals"][4][
                "GBQualifier_name"
            ],
            "clone_lib",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][0]["GBFeature_quals"][4][
                "GBQualifier_value"
            ],
            "Zap-bb",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][1]["GBFeature_key"], "Protein"
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][1]["GBFeature_location"], "1..100"
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][1]["GBFeature_intervals"][0][
                "GBInterval_from"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][1]["GBFeature_intervals"][0][
                "GBInterval_to"
            ],
            "100",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][1]["GBFeature_intervals"][0][
                "GBInterval_accession"
            ],
            "CAA35997.1",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][1]["GBFeature_quals"][0][
                "GBQualifier_name"
            ],
            "name",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][1]["GBFeature_quals"][0][
                "GBQualifier_value"
            ],
            "unnamed protein product",
        )
        self.assertEqual(record[0]["GBSeq_feature-table"][2]["GBFeature_key"], "Region")
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_location"], "33..97"
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_intervals"][0][
                "GBInterval_from"
            ],
            "33",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_intervals"][0][
                "GBInterval_to"
            ],
            "97",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_intervals"][0][
                "GBInterval_accession"
            ],
            "CAA35997.1",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_quals"][0][
                "GBQualifier_name"
            ],
            "region_name",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_quals"][0][
                "GBQualifier_value"
            ],
            "Gla",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_quals"][1][
                "GBQualifier_name"
            ],
            "note",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_quals"][1][
                "GBQualifier_value"
            ],
            "Vitamin K-dependent carboxylation/gamma-carboxyglutamic (GLA) domain. This domain is responsible for the high-affinity binding of calcium ions. This domain contains post-translational modifications of many glutamate residues by Vitamin K-dependent...; cl02449",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_quals"][2][
                "GBQualifier_name"
            ],
            "db_xref",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][2]["GBFeature_quals"][2][
                "GBQualifier_value"
            ],
            "CDD:92835",
        )
        self.assertEqual(record[0]["GBSeq_feature-table"][3]["GBFeature_key"], "CDS")
        self.assertEqual(
            record[0]["GBSeq_feature-table"][3]["GBFeature_location"], "1..100"
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][3]["GBFeature_intervals"][0][
                "GBInterval_from"
            ],
            "1",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][3]["GBFeature_intervals"][0][
                "GBInterval_to"
            ],
            "100",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][3]["GBFeature_intervals"][0][
                "GBInterval_accession"
            ],
            "CAA35997.1",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][3]["GBFeature_quals"][0][
                "GBQualifier_name"
            ],
            "coded_by",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][3]["GBFeature_quals"][0][
                "GBQualifier_value"
            ],
            "X51700.1:28..330",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][3]["GBFeature_quals"][1][
                "GBQualifier_name"
            ],
            "note",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][3]["GBFeature_quals"][1][
                "GBQualifier_value"
            ],
            "bone Gla precursor (100 AA)",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][3]["GBFeature_quals"][2][
                "GBQualifier_name"
            ],
            "db_xref",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][3]["GBFeature_quals"][2][
                "GBQualifier_value"
            ],
            "GOA:P02820",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][3]["GBFeature_quals"][3][
                "GBQualifier_name"
            ],
            "db_xref",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][3]["GBFeature_quals"][3][
                "GBQualifier_value"
            ],
            "InterPro:IPR000294",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][3]["GBFeature_quals"][4][
                "GBQualifier_name"
            ],
            "db_xref",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][3]["GBFeature_quals"][4][
                "GBQualifier_value"
            ],
            "InterPro:IPR002384",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][3]["GBFeature_quals"][5][
                "GBQualifier_name"
            ],
            "db_xref",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][3]["GBFeature_quals"][5][
                "GBQualifier_value"
            ],
            "PDB:1Q3M",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][3]["GBFeature_quals"][6][
                "GBQualifier_name"
            ],
            "db_xref",
        )
        self.assertEqual(
            record[0]["GBSeq_feature-table"][3]["GBFeature_quals"][6][
                "GBQualifier_value"
            ],
            "UniProtKB/Swiss-Prot:P02820",
        )
        self.assertEqual(
            record[0]["GBSeq_sequence"],
            "mrtpmllallalatlclagradakpgdaesgkgaafvskqegsevvkrlrryldhwlgapapypdplepkrevcelnpdcdeladhigfqeayrrfygpv",
        )

    def test_efetch_schemas(self):
        """Test parsing XML using Schemas."""
        # To create the XML file,use
        # >>> Bio.Entrez.efetch("protein", id="783730874", rettype="ipg", retmode="xml")
        with open("Entrez/efetch_schemas.xml", "rb") as stream:
            records = Entrez.read(stream)
        self.assertEqual(len(records), 1)
        record = records["IPGReport"]
        self.assertEqual(len(record.attributes), 2)
        self.assertEqual(record.attributes["product_acc"], "KJV04014.1")
        self.assertEqual(record.attributes["ipg"], "79092155")
        self.assertEqual(len(record), 3)
        self.assertEqual(record["Product"], "")
        self.assertEqual(record["Product"].attributes["kingdom"], "Bacteria")
        self.assertEqual(record["Product"].attributes["slen"], "513")
        self.assertEqual(
            record["Product"].attributes["name"],
            "methylmalonate-semialdehyde dehydrogenase (CoA acylating)",
        )
        self.assertEqual(record["Product"].attributes["org"], "Rhodococcus sp. PML026")
        self.assertEqual(record["Product"].attributes["kingdom_taxid"], "2")
        self.assertEqual(record["Product"].attributes["accver"], "WP_045840896.1")
        self.assertEqual(record["Product"].attributes["taxid"], "1356405")
        self.assertEqual(len(record["ProteinList"]), 2)
        protein = record["ProteinList"][0]
        self.assertEqual(protein.tag, "Protein")
        self.assertEqual(protein.attributes["accver"], "KJV04014.1")
        self.assertEqual(protein.attributes["kingdom"], "Bacteria")
        self.assertEqual(protein.attributes["kingdom_taxid"], "2")
        self.assertEqual(
            protein.attributes["name"],
            "methylmalonic acid semialdehyde dehydrogenase mmsa",
        )
        self.assertEqual(protein.attributes["org"], "Rhodococcus sp. PML026")
        self.assertEqual(protein.attributes["priority"], "0")
        self.assertEqual(protein.attributes["source"], "INSDC")
        self.assertEqual(protein.attributes["taxid"], "1356405")
        self.assertEqual(len(protein), 1)
        self.assertEqual(protein["CDSList"].tag, "CDSList")
        self.assertEqual(protein["CDSList"].attributes, {})
        self.assertEqual(len(protein["CDSList"]), 2)
        self.assertEqual(protein["CDSList"][0], "")
        self.assertEqual(protein["CDSList"][0].attributes["kingdom"], "Bacteria")
        self.assertEqual(
            protein["CDSList"][0].attributes["assembly"], "GCA_000963615.1"
        )
        self.assertEqual(protein["CDSList"][0].attributes["start"], "264437")
        self.assertEqual(protein["CDSList"][0].attributes["stop"], "265978")
        self.assertEqual(protein["CDSList"][0].attributes["taxid"], "1356405")
        self.assertEqual(protein["CDSList"][0].attributes["strain"], "PML026")
        self.assertEqual(
            protein["CDSList"][0].attributes["org"], "Rhodococcus sp. PML026"
        )
        self.assertEqual(protein["CDSList"][0].attributes["kingdom_taxid"], "2")
        self.assertEqual(protein["CDSList"][0].attributes["accver"], "JZIS01000004.1")
        self.assertEqual(protein["CDSList"][0].attributes["strand"], "-")
        self.assertEqual(protein["CDSList"][1], "")
        self.assertEqual(protein["CDSList"][1].attributes["kingdom"], "Bacteria")
        self.assertEqual(
            protein["CDSList"][1].attributes["assembly"], "GCA_000963615.1"
        )
        self.assertEqual(protein["CDSList"][1].attributes["start"], "264437")
        self.assertEqual(protein["CDSList"][1].attributes["stop"], "265978")
        self.assertEqual(protein["CDSList"][1].attributes["taxid"], "1356405")
        self.assertEqual(protein["CDSList"][1].attributes["strain"], "PML026")
        self.assertEqual(
            protein["CDSList"][1].attributes["org"], "Rhodococcus sp. PML026"
        )
        self.assertEqual(protein["CDSList"][1].attributes["kingdom_taxid"], "2")
        self.assertEqual(protein["CDSList"][1].attributes["accver"], "KQ031368.1")
        self.assertEqual(protein["CDSList"][1].attributes["strand"], "-")
        protein = record["ProteinList"][1]
        self.assertEqual(protein.attributes["accver"], "WP_045840896.1")
        self.assertEqual(protein.attributes["source"], "RefSeq")
        self.assertEqual(
            protein.attributes["name"],
            "methylmalonate-semialdehyde dehydrogenase (CoA acylating)",
        )
        self.assertEqual(protein.attributes["taxid"], "1356405")
        self.assertEqual(protein.attributes["org"], "Rhodococcus sp. PML026")
        self.assertEqual(protein.attributes["kingdom_taxid"], "2")
        self.assertEqual(protein.attributes["kingdom"], "Bacteria")
        self.assertEqual(protein.attributes["priority"], "1")
        self.assertEqual(len(protein), 1)
        self.assertEqual(protein["CDSList"].tag, "CDSList")
        self.assertEqual(protein["CDSList"].attributes, {})
        self.assertEqual(len(protein["CDSList"]), 1)
        self.assertEqual(
            protein["CDSList"][0].attributes["assembly"], "GCF_000963615.1"
        )
        self.assertEqual(protein["CDSList"][0].attributes["start"], "264437")
        self.assertEqual(protein["CDSList"][0].attributes["stop"], "265978")
        self.assertEqual(protein["CDSList"][0].attributes["taxid"], "1356405")
        self.assertEqual(protein["CDSList"][0].attributes["strain"], "PML026")
        self.assertEqual(
            protein["CDSList"][0].attributes["org"], "Rhodococcus sp. PML026"
        )
        self.assertEqual(protein["CDSList"][0].attributes["kingdom_taxid"], "2")
        self.assertEqual(protein["CDSList"][0].attributes["accver"], "NZ_KQ031368.1")
        self.assertEqual(protein["CDSList"][0].attributes["strand"], "-")
        self.assertEqual(record["Statistics"], "")
        self.assertEqual(record["Statistics"].attributes["assmb_count"], "2")
        self.assertEqual(record["Statistics"].attributes["nuc_count"], "3")
        self.assertEqual(record["Statistics"].attributes["prot_count"], "2")

    def test_genbank(self):
        """Test error handling when presented with GenBank non-XML data."""
        # Access the nucleotide database using efetch, but return the data
        # in GenBank format.
        # To create the GenBank file, use
        # >>> Bio.Entrez.efetch(db='nucleotide', id='NT_019265', rettype='gb')
        from Bio.Entrez import Parser

        with open("GenBank/NT_019265.gb", "rb") as stream:
            self.assertRaises(Parser.NotXMLError, Entrez.read, stream)
        with open("GenBank/NT_019265.gb", "rb") as stream:
            iterator = Entrez.parse(stream)
            self.assertRaises(Parser.NotXMLError, next, iterator)

    def test_fasta(self):
        """Test error handling when presented with Fasta non-XML data."""
        from Bio.Entrez import Parser

        with open("Fasta/wisteria.nu", "rb") as stream:
            self.assertRaises(Parser.NotXMLError, Entrez.read, stream)
        with open("Fasta/wisteria.nu", "rb") as stream:
            iterator = Entrez.parse(stream)
            self.assertRaises(Parser.NotXMLError, next, iterator)

    def test_pubmed_html(self):
        """Test error handling when presented with HTML (so XML-like) data."""
        # To create the HTML file, use
        # >>> Bio.Entrez.efetch(db="pubmed", id="19304878")
        from Bio.Entrez import Parser

        with open("Entrez/pubmed3.html", "rb") as stream:
            self.assertRaises(Parser.NotXMLError, Entrez.read, stream)
        # Test if the error is also raised with Entrez.parse
        with open("Entrez/pubmed3.html", "rb") as stream:
            records = Entrez.parse(stream)
            self.assertRaises(Parser.NotXMLError, next, records)

    def test_xml_without_declaration(self):
        """Test error handling for a missing XML declaration."""
        # To create the XML file, use
        # >>> Bio.Entrez.efetch(db="journals",id="2830,6011,7473",retmode='xml')
        from Bio.Entrez import Parser

        with open("Entrez/journals.xml", "rb") as stream:
            self.assertRaises(Parser.NotXMLError, Entrez.read, stream)
        # Test if the error is also raised with Entrez.parse
        with open("Entrez/journals.xml", "rb") as stream:
            records = Entrez.parse(stream)
            self.assertRaises(Parser.NotXMLError, next, records)

    def test_xml_without_definition(self):
        """Test error handling for a missing DTD or XML Schema."""
        # To create the XML file, use
        # >>> Bio.Entrez.efetch(db="biosample", id="3502652", rettype="xml")
        with open("Entrez/biosample.xml", "rb") as stream:
            self.assertRaises(ValueError, Entrez.read, stream)
        # Test if the error is also raised with Entrez.parse
        with open("Entrez/biosample.xml", "rb") as stream:
            records = Entrez.parse(stream)
            self.assertRaises(ValueError, next, records)

    def test_truncated_xml(self):
        """Test error handling for a truncated XML declaration."""
        from io import BytesIO

        from Bio.Entrez.Parser import CorruptedXMLError

        truncated_xml = b"""<?xml version="1.0"?>
        <!DOCTYPE GBSet PUBLIC "-//NCBI//NCBI GBSeq/EN" "http://www.ncbi.nlm.nih.gov/dtd/NCBI_GBSeq.dtd">
        <GBSet><GBSeq><GBSeq_locus>
        """
        stream = BytesIO()
        stream.write(truncated_xml)
        stream.seek(0)
        records = Entrez.parse(stream)
        self.assertRaises(CorruptedXMLError, next, records)


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=2)
    unittest.main(testRunner=runner)
