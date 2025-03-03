# Copyright 2023 Calico LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =========================================================================

import json
import os
import sys

import numpy as np
import pandas as pd
import pysam
from tqdm import tqdm

from baskerville import dna

################################################################################
# bed.py
#
# Methods to work with BED files.
################################################################################


def make_bed_seqs(bed_file, fasta_file, seq_len, stranded=False):
    """Return BED regions as sequences and regions as a list of coordinate
    tuples, extended to a specified length."""
    """Extract and extend BED sequences to seq_len."""
    fasta_open = pysam.Fastafile(fasta_file)

    seqs_dna = []
    seqs_coords = []

    for line in open(bed_file):
        a = line.split()
        chrm = a[0]
        start = int(float(a[1]))
        end = int(float(a[2]))
        if len(a) >= 6:
            strand = a[5]
        else:
            strand = "+"

        # determine sequence limits
        mid = (start + end) // 2
        seq_start = mid - seq_len // 2
        seq_end = seq_start + seq_len

        # save
        if stranded:
            seqs_coords.append((chrm, seq_start, seq_end, strand))
        else:
            seqs_coords.append((chrm, seq_start, seq_end))

        # initialize sequence
        seq_dna = ""

        # add N's for left over reach
        if seq_start < 0:
            print(
                "Adding %d Ns to %s:%d-%s" % (-seq_start, chrm, start, end),
                file=sys.stderr,
            )
            seq_dna = "N" * (-seq_start)
            seq_start = 0

        # get dna
        seq_dna += fasta_open.fetch(chrm, seq_start, seq_end).upper()

        # add N's for right over reach
        if len(seq_dna) < seq_len:
            print(
                "Adding %d Ns to %s:%d-%s" % (seq_len - len(seq_dna), chrm, start, end),
                file=sys.stderr,
            )
            seq_dna += "N" * (seq_len - len(seq_dna))

        # reverse complement
        if stranded and strand == "-":
            seq_dna = dna.dna_rc(seq_dna)

        # append
        seqs_dna.append(seq_dna)

    fasta_open.close()

    return seqs_dna, seqs_coords


def read_bed_coords(bed_file, seq_len):
    """Return BED regions as a list of coordinate
    tuples, extended to a specified length."""
    seqs_coords = []

    for line in open(bed_file):
        a = line.split()
        chrm = a[0]
        start = int(float(a[1]))
        end = int(float(a[2]))

        # determine sequence limits
        mid = (start + end) // 2
        seq_start = mid - seq_len // 2
        seq_end = seq_start + seq_len

        # save
        seqs_coords.append((chrm, seq_start, seq_end))

    return seqs_coords


def write_bedgraph(
    preds, targets, data_dir: str, out_dir: str, split_label: str, bedgraph_indexes=None
):
    """Write BEDgraph files for predictions and targets from a dataset..

    Args:
      preds (np.array): Predictions.
      targets (np.array): Targets.
      data_dir (str): Data directory, for identifying sequences and statistics.
      out_dir (str): Output directory.
      split_label (str): Split label.
      bedgraph_indexes (list): List of target indexes to write.
    """
    # get shapes
    num_seqs, target_length, num_targets = targets.shape

    # set bedgraph indexes
    if bedgraph_indexes is None:
        bedgraph_indexes = np.arange(num_targets)

    # read data parameters
    with open("%s/statistics.json" % data_dir) as data_open:
        data_stats = json.load(data_open)
        pool_width = data_stats["pool_width"]

    # read sequence positions
    seqs_df = pd.read_csv(
        "%s/sequences.bed" % data_dir, sep="\t", names=["chr", "start", "end", "split"]
    )
    seqs_df = seqs_df[seqs_df.split == split_label]
    assert seqs_df.shape[0] == num_seqs

    # initialize output directory
    os.makedirs(out_dir, exist_ok=True)

    print("Writing BEDgraph files")
    for ti in tqdm(bedgraph_indexes):
        # slice preds/targets
        preds_ti = preds[:, :, ti]
        targets_ti = targets[:, :, ti]

        # initialize raw predictions/targets
        preds_out = open("%s/preds_t%d.bedgraph" % (out_dir, ti), "w")
        targets_out = open("%s/targets_t%d.bedgraph" % (out_dir, ti), "w")

        # write raw predictions/targets
        for si, seq in enumerate(seqs_df.itertuples()):
            # write bin values
            bin_start = seq.start
            for bi in range(target_length):
                bin_end = bin_start + pool_width
                cols = [
                    seq.chr,
                    str(bin_start),
                    str(bin_end),
                    "%.2f" % preds_ti[si, bi],
                ]
                print("\t".join(cols), file=preds_out)
                cols = [
                    seq.chr,
                    str(bin_start),
                    str(bin_end),
                    "%.2f" % targets_ti[si, bi],
                ]
                print("\t".join(cols), file=targets_out)
                bin_start = bin_end

        preds_out.close()
        targets_out.close()
