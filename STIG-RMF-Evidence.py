import xml.etree.ElementTree as ET
import argparse
from collections import defaultdict
import json
from os import path

parser = argparse.ArgumentParser(description='Python script to parse STIG XML and list NIST 800-53 Rev. 4 evidence.')
#  STIG XML file: https://public.cyber.mil/stigs/downloads/
parser.add_argument('-f', '--file', metavar='FILE_PATH', help='Path to STIG XML file to be parsed.')
#  CCI File: https://dl.dod.cyber.mil/wp-content/uploads/stigs/zip/u_cci_list.zip
parser.add_argument('-c', '--cci', metavar='FILE_PATH', help='Path to CCI XML file to be parsed.')
#  Output File name
parser.add_argument('-o', '--output', metavar='File_Name', help='Output Filename.', default="output")
args = parser.parse_args()


# TODO If files exist, run, else pull down into python folder
# TODO Make final output file readable in the browser (JSON, XML format?)
# TODO Need to provide the Check Text from STIG to VID so need to open the STIG at all for evidence collection


def retrieve_vids():
    """

    :return: [Dictionary] STIG VIDs with CCI numbers.
    """
    tree = ET.parse(args.file)
    root = tree.getroot()
    # Set List and Dict for storing
    CCIDs = []
    VIDtoCCI = {}

    # Loop through finding all VIDs and associated CCIs
    for vid in root.findall('{http://checklists.nist.gov/xccdf/1.1}Group'):
        VID = vid.get('id').encode('utf-8')
        for child in vid:
            for cci in child.findall('{http://checklists.nist.gov/xccdf/1.1}ident'):
                CCI = cci.text
                CCIDs.append(CCI) # Append all CCIs for current VID to list.
            VIDtoCCI.update({VID: CCIDs}) # Update dict with all VIDs and children.
            CCIDs = []
    return VIDtoCCI



def cci_to_evidence():
    """

    :return: [Dictionary] CCI numbers with NIST 800-53 Rev. 4 Controls for Evidence
    """
    tree = ET.parse(args.cci)
    root = tree.getroot()

    RMF_Evidence = []
    CCI_to_RMF = {}

    for cci in root.findall('{http://iase.disa.mil/cci}cci_items'):
        for item in cci.findall('{http://iase.disa.mil/cci}cci_item'):
            CCI = item.get('id')
            for references in item.findall('{http://iase.disa.mil/cci}references'):
                for reference in references:
                    if reference.get('version') == '4':
                        RMF_Evidence.append(reference.get('index'))
            CCI_to_RMF.update({CCI: RMF_Evidence})
            RMF_Evidence = []
    return CCI_to_RMF


def vid_with_evidence():
    """

    :return: [Dictionary] VID number with all NIST 800-53 Rev. 4 Evidence controls
    """
    vid_cci = retrieve_vids()  # Format {VID: [CCI, CCI]}
    cci_evidence = cci_to_evidence()  # Format {CCI: [Evidence, Evidence]}
    results = defaultdict(list)  # Format {VID: [Evidence, Evidence]}

    for vid, ccis in vid_cci.items():
        for cci in ccis:
            if cci_evidence.get(cci, None):
                results[vid].extend(cci_evidence[cci])
    return results


def results_format():
    """

    :return: [XML] XML Document with VID as parent and all Evidence controls as children
    """
    results = vid_with_evidence()
    top = ET.Element('Root')
    for vid, evidence in results.items():
        parent = ET.SubElement(top, "V-ID", text=vid)
        for evi in evidence:
            ET.SubElement(parent, "Evidence", text=evi)
        mydata = ET.tostring(top)
    file = open(str(args.output) + ".xml", "w")
    file.write(mydata)


results_format()
