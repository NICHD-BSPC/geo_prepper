import sys
import os
import argparse
import pandas as pd
import yaml
import subprocess
from pathlib import Path
import shutil

def parser():
    ap = argparse.ArgumentParser(
        description="""
            This script takes a sampletable and prepares files for GEO submission.

            - symlinks raw and processed files to local directory
            - calculates md5 sums
            - creates files that mimic sections of GEO metadata spreadsheet
        """,
        formatter_class = argparse.RawTextHelpFormatter
    )
    ap.add_argument(
        "-s",
        "--sampletable",
        help="Sampletable with sample names, technical replicates (if any) and path to fastq",
        default=""
    )
    ap.add_argument(
        "-c",
        "--config",
        help="Config yaml to define columns of interest in sampletable",
        default=""
    )
    ap.add_argument(
        "-o",
        "--output_dir",
        help="Output directory",
        default=None
    )
    ap.add_argument(
        "-g",
        "--grouping_col",
        help='Column name to group technical replicates. If specified, will override config.yaml specification',
        default=None
    )
    ap.add_argument(
        "-f",
        "--force",
        help='Overwrite output directory if it exists',
        action='store_true',
        default=False
    )

    args = ap.parse_args()
    if not args.output_dir or not args.sampletable or not args.config:
        print('Sample table, config and output directory are required parameters')
        ap.print_help()
        sys.exit(1)

    return args

# function to deduplicate a list
# NOTE: this maintains input order, so is different from set()
def unique_list(l):
    tmp = []
    for a in l:
        if a not in tmp:
            tmp += [a]
    return tmp

# function to check config for required tags
def check_config(c):
    required_tags = ['is_paired_end','file_cols','sample_col']
    if not all([t in c for t in required_tags]):
        print('Tags: ', ', '.join(required_tags), ' must be present in config file')
        sys.exit(1)

def run():
    args = parser()

    odir = Path(args.output_dir)
    force = args.force

    # read config yaml with column specifications
    try:
        c = yaml.load(open(args.config), Loader=yaml.FullLoader)
    except FileNotFoundError:
        print('Config file: ' + args.config + ' not found')
        sys.exit(1)
    # check config for required tags
    check_config(c)

    # check for output directory and create it
    if odir.exists():
        if not force:
            print('Output directory: \'' + str(odir) + '\' already exists! ' + \
                  'To overwrite please use \'-f/--force\' parameter.')
            sys.exit(1)
        else:
            shutil.rmtree(odir)
    os.mkdir(odir)

    # get columns dict
    columns = c['file_cols']

    # get paired end info from config
    is_paired_end = c['is_paired_end']

    # get column names to skip in output names
    if 'skip_column_suffix' in c:
        skip_column_name = c['skip_column_suffix']
    else:
        skip_column_name = None

    # get grouping variable
    if not args.grouping_col:
        try:
            gcol = c['grouping_col']
        except KeyError:
            # in the absence of 'grouping_col' specification, it defaults to c['sample_col']
            gcol = c['sample_col']
    else:
        gcol = args.grouping_col

    # start processing sampletable
    s = pd.read_csv(args.sampletable, sep='\t', header=0, comment='#')
    s = s.fillna('')

    # if paired end data, create paired-end section
    if is_paired_end:
        # and check for R1 and R2 tags in config
        if not all([key in columns.keys() for key in ['R1','R2']]):
            print('For paired-end experiments, R1 and R2 keys must be present ' +\
                  'in \'columns\' section of config file')
            sys.exit(1)
        paired_end = pd.DataFrame(columns=['R1', 'R2'])

    # check for presence of grouping_col in sampletable
    if gcol not in s.columns:
        print('Grouping column: ' + gcol + ' not found in sampletable')
        sys.exit(1)

    # get tech rep groups and counts
    groups = unique_list(s.loc[:, gcol].tolist())

    output_files = { key: [] for key in columns.keys() }
    md5hash = { key: [] for key in columns.keys() }
    sample_section = []

    # get metadata columns, if specified
    get_mdata = False
    try:
        metadata_cols = c['metadata_cols']
        # adding 1 to index since subset of sampletable has indexes reset
        metadata_idx = [(i + 1) for i in range(s.shape[1]) if s.columns[i] in metadata_cols]
        get_mdata = True
    except:
        metadata_cols = []

    for g in groups:
        print('group:', g)
        subset = s.loc[s.loc[:,gcol] == g,:].reset_index()

        samples = subset.loc[:, c['sample_col']].tolist()

        # dictionary to hold file lists
        fdict = {}

        for key in columns.keys():
            if columns[key] in subset.columns:
                fdict[key] = subset.loc[:, columns[key]].tolist()

        sample_group = []
        for i in range(subset.shape[0]):
            sample = samples[i]

            # dictionary to collect all files for a particular sample
            files = { key: fdict[key][i] for key in fdict.keys() if len(fdict[key]) > 0 }

            # dictionary for symlinked files
            dest_files = { key: [] for key in files.keys() }

            for key in files.keys():
                f = files[key]

                # skip if file is missing
                if not f:
                    continue
                elif not os.path.exists(f):
                    print('\tFile: ' + f + ' does not exist, skipping!')
                    continue

                print('\tsample:', samples[i], '\tfile:', f)

                # get file extension
                tok = os.path.basename(f).split('.')
                ext = '.'.join(tok[1:len(tok)])

                if key in ['R1','R2']:
                    file_prefix = str(odir / samples[i])
                else:
                    file_prefix = str(odir / g)

                # make destination file name
                if skip_column_name is not None and key in skip_column_name:
                    dest = file_prefix + '.' + ext
                else:
                    dest = file_prefix + '_' + key + '.' + ext

                # make symlink
                # NOTE: existing symlinks are overwritten
                src = f
                if os.path.exists(dest):
                    os.unlink(dest)
                print('\t1. Symlinking to:', dest)
                os.symlink(src, dest)

                # calculate md5 sum
                print('\t2. Calculating md5 sum')
                cmd = subprocess.run(['md5sum',dest], stdout=subprocess.PIPE)
                md5hash[ key ] += [ cmd.stdout.decode().split()[0] ]

                dest_files[ key ] = os.path.basename(dest)
                output_files[ key ] += [ dest_files[key] ]
                sample_group += [ dest_files[key] ]

            if is_paired_end:
                paired_end = paired_end.append({
                    'R1': dest_files['R1'],
                    'R2': dest_files['R2']},
                    ignore_index=True)

        # get metadata
        if get_mdata:
            metadata = []
            for m in range(len(metadata_cols)):
                metadata += [ subset.iloc[i, metadata_idx[m]] ]
            sample_group = metadata + sample_group

        sample_section += [sample_group]

    # write hashes to file
    hash_dict = { 'files': [], 'md5': [] }
    for key in md5hash.keys():
        hash_dict['files'] += output_files[key]
        hash_dict['md5'] += md5hash[key]
    hash_df = pd.DataFrame(hash_dict)
    hash_df.to_csv(odir / 'md5hash.tsv',
            sep='\t', index=False)

    # write paired end section to file
    if is_paired_end:
        paired_end.to_csv(
                odir / 'paired_end.tsv',
                sep='\t', index=False)

    # output sample section
    sample_section = pd.DataFrame(sample_section)
    sample_section.to_csv(odir / 'sample_section.tsv',
            sep='\t', index=False)


if __name__ == "__main__":
    run()


