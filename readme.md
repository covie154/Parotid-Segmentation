# Parotid Tools

Readme for parotid segmentation helpers

Start with unanonymised DICOMs, and end up with aligned niis

Prerequisites (non-exhaustive):
- [dicom-anonymizer](https://github.com/KitwareMedical/dicom-anonymizer)
- [ITKElastix] (https://github.com/InsightSoftwareConsortium/ITKElastix/tree/main)
- [dicom2nifti] (https://github.com/icometrix/dicom2nifti)
- tqdm
- [Monai] (https://github.com/Project-MONAI/MONAILabel)

Files to use in order:
1. anon_all_dicoms.ps1
2. file_operations.ipynb
2. align_nii.ipynb
3. create_T1s.ipynb

## DICOM Anonymisation

Use dicom_anon.bat to anonymise one folder
e.g. `
dicom_anon.bat MR_231
`

Use anon_all_dicoms to anonymise all DICOMs in subfolders in the folder
`./anon_all_dicoms.ps1`

## Create NII from DICOM

Run the cells in file_operations.ipynb to create NIIs.
A JSON file is optionally created that details the sequence parameters, e.g. Matrix size, slice thickness, slice gap
Currently, it chooses axial T1 (T1_ax.nii), T2 (T2_ax.nii) and T1+c (T1c_ax.nii) sequences

# Align the sequences

The T2 and T1+c sequences are aligned to the T1 unenhanced sequence
Run the cells in align_nii.ipynb to align using ITKElastix

# Extract T1s for feeding into Monai

Run the cells in create_T1s.ipynb. This creates a folder of all the T1s which can be used in training the AI