#%%
import json
import os
import sys
import pydicom
import re
import pandas as pd
import dicom2nifti
import shutil

def isDICOMType(filePath):
    """
    :returns True if input file is a DICOM File. False otherwise.
    """
    try:
        with open(filePath, 'rb') as tempFile:
            tempFile.seek(0x80, os.SEEK_SET)
            return tempFile.read(4) == b'DICM'
    except IOError:
        return False

def readDCMDir(input_path: str):
    """List all the dicom files in a dir

    Args:
        input_path (str): Path containing all the DICOM files
    """
     # Get input arguments
    input_folder = ''
    if os.path.isdir(input_path):
        input_folder = input_path

    # Generate list of input file if a folder has been set
    input_files_list = []

    if input_folder == '':
        input_files_list.append(input_path)
    else:
        files = os.listdir(input_folder)
        for fileName in files:
            if isDICOMType(input_folder + '/' + fileName):
                input_files_list.append(fileName)
    
    return input_files_list
                
def createImgsList(input_filenames: list):
    """Create a list of Seq, Ser, Img for a list of img filenames

    Args:
        input_filenames (list): files list from readDCMDir()

    Returns:
        imgs_list: [[Seq, Ser, Img], ...]
    """
    input_imgs_list = []

    for img in input_filenames:
        regex_se_im = re.search("Seq(\S+)\.Ser(\S+)\.Img(\S+).dcm$", img)
        Seq = regex_se_im.group(1)
        Ser = regex_se_im.group(2)
        Img = regex_se_im.group(3)
        input_imgs_list.append([Seq, Ser, Img])
    
    return input_imgs_list

def getPrefixLst(input_filenames: list):
    """Get the prefix 

    Args:
        input_filenames (list): _description_

    Returns:
        prefix (str): _description_
    """
    first_file = input_filenames[0]
    regex_prefix = re.search('(.*?)\.Seq\S+\.Ser\S+\.Img\S+.dcm$', first_file)
    return regex_prefix.group(1)

def sortDCMDir(imgs_list: list):
    """Create a dict of the sequence params from the list of files
    Sample output:
    {
        1.2 (Seq 1 Ser 2): {
            Imgs: 30
        }, 
        2.3 (Seq 2 Ser 3): {
            Imgs: 30
        }, ...
    }

    Args:
        imgs_list (array): _description_
    """

    dcm_df = pd.DataFrame(imgs_list)
    output_dict = {}

    for Seq in dcm_df[0].unique():
        # Create the dict of sequences
        # Key: Seq.Ser
        # Values: Only images (imgs) for now
        for Ser in dcm_df[dcm_df[0] == Seq][1].unique():
            arr_imgs = dcm_df[(dcm_df[0] == Seq) & (dcm_df[1] == Ser)][2]
            n_imgs = len(arr_imgs)
            temp_key = f"{Seq}.{Ser}"

            output_dict[temp_key] = {"Imgs": n_imgs}

    return output_dict

def formDCMFile(input_path: str, prefix: str, Seq: int, Ser: int, Img: int):
    # Form the path string from the various dcm params
    input_folder = ''
    if os.path.isdir(input_path):
        input_folder = input_path
    
    fileName = f"{prefix}.Seq{Seq}.Ser{Ser}.Img{Img}.dcm"
    return input_folder + '/' + fileName

def getDCMTags(input_file: str, tags: list): 
    # From one DCM file, get some of the tags and output to a dict
    dataset = pydicom.dcmread(input_file)
    output_dict = {}
    
    for tag in tags:
        tag_data = dataset.get(tag)
        if tag_data:
            tag_name = tag_data.name

            if tag == (0x0020, 0x0037):
                # Round off the patient position matrix
                # https://gist.github.com/agirault/60a72bdaea4a2126ecd08912137fe641
                matrix_pos = list(tag_data.value)
                tag_value = [round(x) for x in matrix_pos]
            elif tag == (0x0018, 0x0010):
                tag_value = 1
            else:
               tag_value = tag_data.value

            output_dict[tag_name] = tag_value
    
    return output_dict

keys_to_read = [
    (0x0008, 0x103E), # Series Description
    (0x0018, 0x0010), # Contrast Bolus Agent
    (0x0018, 0x0050), # Slice thickness
    (0x0018, 0x0088), # Slice gap
    (0x0018, 0x1310), # Matrix size
    (0x0020, 0x0037), # Image orientation/patient position
]

def createDCMInfo(input_path: str, keys_to_read: list):
    # Create a nested dict containing the image numbers, and data on various provided keys
    files_lst = readDCMDir(input_path)
    prefix = getPrefixLst(files_lst)
    imgs_lst = createImgsList(files_lst)
    dict_seqs = sortDCMDir(imgs_lst)

    for SeqSer, value_dict in dict_seqs.items():
        SeqSer_lst = str(SeqSer).split('.')
        temp_dcm = formDCMFile(input_path, prefix, SeqSer_lst[0], SeqSer_lst[1], 1)
        temp_tags_dict = getDCMTags(temp_dcm, keys_to_read)

        dict_seqs[SeqSer] = value_dict | temp_tags_dict
    
    return dict_seqs

def noFSNoNeck(in_str: str):
    no_FS = not re.search('f\/s', in_str, re.IGNORECASE)
    no_neck = not re.search('neck', in_str, re.IGNORECASE)

    return no_neck and no_FS

def getAx(in_dict: dict):
    # Create a dict of the three axial sequences we need
    dict_keys = list(in_dict.keys())
    out_dict = {}
    # We want
    # 'T1_ax': "",
    # 'T2_ax': "",
    # 'T1c_ax': ""

    for seq, seq_data in in_dict.items():
        # Axial: Image orientation = [1, 0, 0, 0, 1, 0]
        desc = in_dict[seq]['Series Description']

        # First we filter out the non-MR sequences
        if 'Image Orientation (Patient)' not in seq_data.keys():
            # If it's not a cross-sectional sequence, remove it from the shortlist as well
            dict_keys.remove(seq)
            continue

        # Then we filter those with +c and axial
        if (seq_data['Image Orientation (Patient)'] == [1, 0, 0, 0, 1, 0]) and ('Contrast/Bolus Agent' in seq_data.keys()) and \
            re.search("[Tt]1", in_dict[seq]['Series Description']) and \
            (not re.search('neck', in_dict[seq]['Series Description'], re.IGNORECASE)):
            if 'T1c_ax' in out_dict:
                sub_desc = re.sub("\/", '', seq_data['Series Description'])
                out_dict[sub_desc] = seq
            else:
                out_dict['T1c_ax'] = seq

            # Remove it from further consideration cos there's both T1 pre and T1 post
            dict_keys.remove(seq)
                
    for seq in dict_keys:
         # First we get all the axial sequences
         if (in_dict[seq]['Image Orientation (Patient)'] == [1, 0, 0, 0, 1, 0]):
            desc = in_dict[seq]['Series Description']

            if (re.search("[Tt]1", desc) and noFSNoNeck(desc)):
                if 'T1_ax' in out_dict:
                    out_dict[desc] = seq
                else:
                    out_dict['T1_ax'] = seq
            if (re.search("[Tt]2", desc) and noFSNoNeck(desc)):
                if 'T2_ax' in out_dict:
                    out_dict[desc] = seq
                else:
                    out_dict['T2_ax'] = seq
    
    return out_dict

temp_dcm_dir = 'E:\\Parotid\\data_anon\\MR_021_anon'

def createTempFolder(path):
    try:  
        os.mkdir(path) 
    except OSError as error:  
        print(error)

def createJSON(dict_json, out_file_name):
    # Serializing json
    json_object = json.dumps(dict_json, indent=4)
    
    # Writing to sample.json
    with open(out_file_name, "w") as outfile:
        outfile.write(json_object)

def create_nii(in_path, out_path, out_json=""):
    # First check if out_path exists, if not create it
    if os.path.isdir(out_path):
        print(f"Copying files to {out_path}")
    else:
        os.mkdir(out_path)
        print(f"Output dir does not exist. Creating {out_path}...")

    # Instantiate the list of all sequences
    all_seqs = createDCMInfo(in_path, keys_to_read)

    if out_json:
        createJSON(all_seqs, out_path + '\\' + out_json)
    
    # Get a dict of the axial sequences
    ax_seqs = getAx(all_seqs)
    ax_seqs_list = list(ax_seqs.keys())
    print(f"Found the following sequences: {', '.join(ax_seqs_list)}")

    # Find the prefix
    prefix = getPrefixLst(readDCMDir(in_path))

    # Set up temp filder dir
    temp_folder_dir = in_path + "\\Temp"

    for seq, img_key in ax_seqs.items():
        # Create the "temp" folder to contain the imgs
        createTempFolder(temp_folder_dir)
        img_key_list = img_key.split('.')
        total_imgs = all_seqs[img_key]['Imgs']
        list_imgs = [formDCMFile(in_path, prefix, img_key_list[0], img_key_list[1], (x+1)) for x in range(total_imgs)]
        final_list_imgs = [formDCMFile(temp_folder_dir, prefix, img_key_list[0], img_key_list[1], (x+1)) for x in range(total_imgs)]
        
        # Copy everything to the temp dir
        for i in range(total_imgs):
            shutil.copyfile(list_imgs[i], final_list_imgs[i])
        
        print(f"Creating output for Seq {img_key_list[0]} Ser {img_key_list[1]} ({seq})... ", end=" ")
        # Create the nifti
        dicom2nifti.dicom_series_to_nifti(temp_folder_dir, out_path+'\\'+seq+".nii", reorient_nifti=True)
        # dicom2nifti.convert_directory(temp_folder_dir, out_path, compression=True, reorient=True)

        print("Done!")
        
        # Finally, delete temp folder
        shutil.rmtree(temp_folder_dir)


# %%
