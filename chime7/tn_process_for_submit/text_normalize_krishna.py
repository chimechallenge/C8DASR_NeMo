"""
normalize text for final submission
"""

import re
import json
import argparse
import glob
import os
import jiwer
from jiwer.transforms import RemoveKaldiNonWords
# from lhotse.recipes.chime6 import normalize_text_chime6

# jiwer_chime6_scoring = jiwer.Compose(
#     [
#         RemoveKaldiNonWords(),
#         jiwer.SubstituteRegexes({r"\"": " ", "^[ \t]+|[ \t]+$": "", r"\u2019": "'"}),
#         jiwer.RemoveEmptyStrings(),
#         jiwer.RemoveMultipleSpaces(),
#     ]
# )

jiwer_chime7_scoring = jiwer.Compose(
    [
        jiwer.SubstituteRegexes(
            {
                "(?:^|(?<= ))(hm|hmm|mhm|mmh|mmm)(?:(?= )|$)": "hmmm",
                "(?:^|(?<= ))(uhm|um|umm|umh|ummh)(?:(?= )|$)": "ummm",
                "(?:^|(?<= ))(uh|uhh)(?:(?= )|$)": "uhhh",
            }
        ),
        jiwer.RemoveEmptyStrings(),
        jiwer.RemoveMultipleSpaces(),
    ]
)

# def chime6_norm_scoring(txt):
#     return jiwer_chime6_scoring(normalize_text_chime6(txt, normalize="kaldi"))



# def chime7_norm_scoring(txt):
#     return jiwer_chime7_scoring(
#         jiwer_chime6_scoring(
#             normalize_text_chime6(txt, normalize="kaldi")
#         )  # noqa: E731
#     )  # noqa: E731

def read_manifest(manifest):
    data = []
    # try:
    #     f = open(manifest.get(), 'r', encoding='utf-8')
    # except:
    #     raise Exception(f"Manifest file could not be opened: {manifest}")
    # for line in f:
    #     item = json.loads(line)
    #     data.append(item)
    # f.close()
    with open(manifest, 'r') as f:
        for line in f:
            json_line = json.loads(line)  # parse json from line
            words = json_line['pred_text'] 
            del json_line['pred_text'], json_line['text'], json_line['audio_filepath']
            json_line['words'] = words
            data.append(json_line)
    return data

def write_manifest(output_path, target_manifest):
    with open(output_path, "w", encoding="utf-8") as outfile:
        for tgt in target_manifest:
            json.dump(tgt, outfile)
            outfile.write('\n')
            
def dump_json(output_path, target_manifest):
    with open(output_path, "w") as f:
        # f.write(json.dumps(entry, indent=4))
        json.dump(target_manifest, f, indent=4)
        # for entry in target_manifest:
        #     # Convert dictionary to JSON format with indent and write it to file
        #     f.write(json.dumps(entry, indent=4))
        #     # Write a newline character after each line
        #     f.write('\n')
            
def parse_args():
    parser = argparse.ArgumentParser(description='normalize text for final submission')
    parser.add_argument('--input_fp', type=str, required=True, help='input manifest file')
    args = parser.parse_args()
    return args

# def main(args):
def norm_text(input_fp, output_fp):
    manifest_items = read_manifest(input_fp)
    for item in manifest_items:
        # replace multiple spaces with single space
        item['words'] = re.sub(' +', ' ', item['words'])
        # replace '\u2047' with ''
        item['words'] = item['words'].replace('\u2047', '')
        # replace isolated aw with oh
        item['words'] = item['words'].replace(' aw ', ' oh ')
        
        item['words'] = jiwer_chime7_scoring(item['words'])
    # write manifest
    # write_manifest(output_fp, manifest_items)
    dump_json(output_fp, manifest_items)
    return manifest_items
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="nemo chime7 output folder to final submission format")
    parser.add_argument("--input_dir", type=str, required=True, help="Input file path")
    parser.add_argument("--sub_json_foldername", type=str, required=True, help="sub_json_foldername")
    args = parser.parse_args()
    
    # args = parse_args()
    # original_folder = "/disk_b/datasets/chime7_final_submission/final_submission_nemo_json/main/system1/dev"
    original_folder = args.input_dir
    # output_folder = "/disk_b/datasets/chime7_final_submission/final_submission_nemo_json_normalized"
    output_folder = original_folder.replace(f"{args.sub_json_foldername}", f"{args.sub_json_foldername}_normalized")
    # glob folder to get the file list
    file_list = glob.glob(original_folder + "/**/*.json", recursive=True)
    # loop all the files
    scenario_dict = {"chime6":[], "dipco":[], "mixer6":[]}
    for input_fp in file_list:
        # get basename from input_fp
        output_fp = input_fp.replace(original_folder, output_folder)
        up_folder = os.path.dirname(output_fp)
        os.makedirs(up_folder,  exist_ok=True)
        scenario = input_fp.split('/')[-2]
        print(f"Normalizing \n {input_fp} \n to \n {output_fp}")
        list_of_dicts = norm_text(input_fp, output_fp)
        
        if scenario in  scenario_dict:
            scenario_dict[scenario].extend(list_of_dicts)
        else:
            scenario_dict[scenario] = list_of_dicts
    track = original_folder.split('/')[-3]
    system = original_folder.split('/')[-2]
    split = original_folder.split('/')[-1]
    original_folder.split() 
    for scenario, list_of_dicts in scenario_dict.items():
        submit_folder = original_folder.replace(f"{args.sub_json_foldername}", f"{args.sub_json_foldername}_norm_for_submit") 
        base_dir = "/".join(submit_folder.split('/')[:-3]) 
        submit_category_folder = os.path.join(base_dir, f"{track}_{system}", split)
        os.makedirs(submit_category_folder,  exist_ok=True)
        submit_category_fullpath = os.path.join(base_dir, f"{track}_{system}", split, f"{scenario}.json")
        dump_json(submit_category_fullpath, list_of_dicts)