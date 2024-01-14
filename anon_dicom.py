import argparse
from dicomanonymizer import *
from dicomanonymizer import dicomfields,anonymizer
import dicomanonymizer as d

def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('input', help='Path to the input dicom file or input directory which contains dicom files')
    parser.add_argument('output', help='Path to the output dicom file or output directory which will contains dicom files')
    parser.add_argument('--id', action='store', help='Patient ID/Name')
    parser.add_argument('--keepPrivateTags', action='store_true', dest='keepPrivateTags', help='If used, then private tags won\'t be deleted')
    args = parser.parse_args()

    """
        To anonymise:
        - Name      (0x0010, 0x0010) - Replace
        - ID        (0x0010, 0x0020) - Replace
        - Birthdate (0x0010, 0x0030)
        - Referrer  (0x0008, 0x0090)
        - Address   (0x0010, 0x1040)
        - Weight    (0x0010, 0x1030)
        - St. Date  (0x0008, 0x0020)
        - St. Time  (0x0008, 0x0030)
        - Inst. Add.(0x0008, 0x0081)
    """

    input_dicom_path = args.input
    output_dicom_path = args.output

    extraAnonymizationRules = {}

    tags_to_remove = [
        (0x0010, 0x0030),
        (0x0008, 0x0090),
        (0x0010, 0x1040),
        (0x0010, 0x1030),
        (0x0008, 0x0020),
        (0x0008, 0x0030),
        (0x0008, 0x0081),
    ]

    # ALL_TAGS variable is defined on file dicomfields.py
    # the 'keep' method is already defined into the dicom-anonymizer
    # It will overrides the default behaviour

    # First we keep all the tags
    for i in d.ALL_TAGS:
        extraAnonymizationRules[i] = keep

    # Then we delete some of the relevant tags
    for i in tags_to_remove:
        extraAnonymizationRules[i] = delete

    # Finally we anon the name and ID
    if args.id:
        extraAnonymizationRules[(0x0010, 0x0010)] = args.id
        extraAnonymizationRules[(0x0010, 0x0020)] = args.id

    # Launch the anonymization
    d.anonymize(input_dicom_path, output_dicom_path, extraAnonymizationRules, True)

if __name__ == "__main__":
    main()