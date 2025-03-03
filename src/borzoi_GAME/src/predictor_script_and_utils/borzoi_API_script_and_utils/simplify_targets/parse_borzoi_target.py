# parse_borzoi_target.py
import os
import sys
import pandas as pd

utils_dir = os.path.dirname(__file__)
borzoi_api_dir = os.path.dirname(utils_dir)
borzoi_examples_dir = f"{borzoi_api_dir}/borzoi/examples"

input_data = pd.read_csv(f'{borzoi_examples_dir}/targets_human.txt', sep='\t', header=0)
input_data = input_data[['description']]

CAGE = input_data[input_data['description'].str.contains("CAGE")]
CAGE = CAGE['description'].str.split(r'[/;:]', expand=True)
CAGE = CAGE.iloc[:, :2]
CAGE.columns = ['Assay', 'Cell Type']

DNASE = input_data[input_data['description'].str[:5] == 'DNASE']
DNASE = DNASE['description'].str.split(r'[;:]', expand=True)
DNASE = DNASE.iloc[:, :2]
DNASE.columns = ['Assay','Cell Type']

ATAC = input_data[input_data['description'].str[:4] == 'ATAC']
ATAC = ATAC['description'].str.split(r'[;:]', expand=True)
ATAC = ATAC.iloc[:, :2]
ATAC.columns = ['Assay','Cell Type']

CHIP = input_data[input_data['description'].str[:4] == 'CHIP']
CHIP = CHIP['description'].str.split(r'[;:]', expand=True)
CHIP = CHIP.iloc[:, :3]
CHIP.columns = ['Assay', 'Molecule','Cell Type']

RNA = input_data[input_data['description'].str[:3] == 'RNA']
RNA = RNA['description'].str.split(r'[/;:]', expand=True)
RNA = RNA.iloc[:, :2]
RNA.columns = ['Assay', 'Cell Type']

# Merged data: Note that CHIP will have one extra columns
targets_borzoi = pd.concat([CAGE, DNASE, ATAC, CHIP, RNA], ignore_index=True)
targets_borzoi.to_csv(f'{utils_dir}/borzoi_human_targets_simplified.txt', sep='\t')
