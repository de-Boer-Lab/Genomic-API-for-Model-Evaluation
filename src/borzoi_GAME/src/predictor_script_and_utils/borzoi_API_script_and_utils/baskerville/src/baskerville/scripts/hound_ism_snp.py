#!/usr/bin/env python
# Copyright 2017 Calico LLC
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
from optparse import OptionParser
import json
import os

import h5py
import numpy as np
import pandas as pd

from baskerville import dataset
from baskerville import dna
from baskerville import seqnn
from baskerville import snps
from baskerville import vcf

"""
hound_ism_snp.py

Perform an in silico saturated mutagenesis of the sequences surrounding variants
given in a VCF file.
"""


def main():
    usage = "usage: %prog [options] <params_file> <model_file> <vcf_file>"
    parser = OptionParser(usage)
    parser.add_option(
        "-d",
        dest="mut_down",
        default=0,
        type="int",
        help="Nucleotides downstream of center sequence to mutate [Default: %default]",
    )
    parser.add_option(
        "-f",
        dest="genome_fasta",
        default=None,
        help="Genome FASTA [Default: %default]",
    )
    parser.add_option(
        "-l",
        dest="mut_len",
        default=200,
        type="int",
        help="Length of centered sequence to mutate [Default: %default]",
    )
    parser.add_option(
        "-o",
        dest="out_dir",
        default="ism_snp_out",
        help="Output directory [Default: %default]",
    )
    parser.add_option(
        "--rc",
        dest="rc",
        default=False,
        action="store_true",
        help="Ensemble forward and reverse complement predictions [Default: %default]",
    )
    parser.add_option(
        "--shifts",
        dest="shifts",
        default="0",
        help="Ensemble prediction shifts [Default: %default]",
    )
    parser.add_option(
        "--stats",
        dest="snp_stats",
        default="logSUM",
        help="Comma-separated list of stats to save. [Default: %default]",
    )
    parser.add_option(
        "-t",
        dest="targets_file",
        default=None,
        type="str",
        help="File specifying target indexes and labels in table format",
    )
    parser.add_option(
        "-u",
        dest="mut_up",
        default=0,
        type="int",
        help="Nucleotides upstream of center sequence to mutate [Default: %default]",
    )
    parser.add_option(
        "--untransform_old",
        dest="untransform_old",
        default=False,
        action="store_true",
        help="Untransform old models [Default: %default]",
    )
    (options, args) = parser.parse_args()

    if len(args) != 3:
        parser.error("Must provide parameters and model files and VCF")
    else:
        params_file = args[0]
        model_file = args[1]
        vcf_file = args[2]

    if not os.path.isdir(options.out_dir):
        os.mkdir(options.out_dir)

    options.shifts = [int(shift) for shift in options.shifts.split(",")]
    options.snp_stats = [snp_stat for snp_stat in options.snp_stats.split(",")]

    if options.mut_up > 0 or options.mut_down > 0:
        options.mut_len = options.mut_up + options.mut_down
    else:
        assert options.mut_len > 0
        options.mut_up = options.mut_len // 2
        options.mut_down = options.mut_len - options.mut_up

    #################################################################
    # read parameters and targets

    # read model parameters
    with open(params_file) as params_open:
        params = json.load(params_open)
    params_model = params["model"]

    # read targets
    if options.targets_file is None:
        parser.error("Must provide targets file to clarify stranded datasets")
    targets_df = pd.read_csv(options.targets_file, sep="\t", index_col=0)

    # handle strand pairs
    if "strand_pair" in targets_df.columns:
        # prep strand
        targets_strand_df = dataset.targets_prep_strand(targets_df)

        # set strand pairs (using new indexing)
        orig_new_index = dict(zip(targets_df.index, np.arange(targets_df.shape[0])))
        targets_strand_pair = np.array(
            [orig_new_index[ti] for ti in targets_df.strand_pair]
        )
        params_model["strand_pair"] = [targets_strand_pair]

        # construct strand sum transform
        strand_transform = dataset.make_strand_transform(targets_df, targets_strand_df)
    else:
        targets_strand_df = targets_df
        strand_transform = None

    num_targets = targets_strand_df.shape[0]

    #################################################################
    # setup model

    seqnn_model = seqnn.SeqNN(params_model)
    seqnn_model.restore(model_file)
    seqnn_model.build_slice(targets_df.index)
    seqnn_model.build_ensemble(options.rc)

    #################################################################
    # SNP sequence dataset

    # load SNPs
    variants = vcf.vcf_snps(vcf_file)

    # get one hot coded input sequences
    seqs_1hot, seq_headers, variants, seqs_dna = vcf.snps_seq1(
        variants, params_model["seq_length"], options.genome_fasta, return_seqs=True
    )
    num_seqs = seqs_1hot.shape[0]

    # determine mutation region limits
    seq_mid = params_model["seq_length"] // 2
    mut_start = seq_mid - options.mut_up
    mut_end = mut_start + options.mut_len

    #################################################################
    # setup output

    scores_h5_file = "%s/scores.h5" % options.out_dir
    if os.path.isfile(scores_h5_file):
        os.remove(scores_h5_file)
    scores_h5 = h5py.File(scores_h5_file, "w")
    scores_h5.create_dataset("label", data=np.array(seq_headers, dtype="S"))
    scores_h5.create_dataset("seqs", dtype="bool", shape=(num_seqs, options.mut_len, 4))
    for snp_stat in options.snp_stats:
        scores_h5.create_dataset(
            snp_stat, dtype="float16", shape=(num_seqs, options.mut_len, 4, num_targets)
        )

    #################################################################
    # predict scores and write output

    for si in range(seqs_1hot.shape[0]):
        print("Predicting %d" % si, flush=True)

        # 1-hot encode reference
        ref_1hot = np.expand_dims(seqs_1hot[si], axis=0)

        # save sequence
        scores_h5["seqs"][si] = ref_1hot[0, mut_start:mut_end].astype("bool")

        # predict reference
        ref_preds = []
        for shift in options.shifts:
            # shift sequence and predict
            ref_1hot_shift = dna.hot1_augment(ref_1hot, shift=shift)
            ref_preds_shift = seqnn_model.predict_transform(
                ref_1hot_shift,
                targets_df,
                strand_transform,
                options.untransform_old,
            )
            ref_preds.append(ref_preds_shift)
        ref_preds = np.array(ref_preds)

        # for mutation positions
        for mi in range(mut_start, mut_end):
            # for each nucleotide
            for ni in range(4):
                # if non-reference
                if ref_1hot[0, mi, ni] == 0:
                    # copy and modify
                    alt_1hot = np.copy(ref_1hot)
                    alt_1hot[0, mi, :] = 0
                    alt_1hot[0, mi, ni] = 1

                    # predict alternate
                    alt_preds = []
                    for shift in options.shifts:
                        # shift sequence and predict
                        alt_1hot_shift = dna.hot1_augment(alt_1hot, shift=shift)
                        alt_preds_shift = seqnn_model.predict_transform(
                            alt_1hot_shift,
                            targets_df,
                            strand_transform,
                            options.untransform_old,
                        )
                        alt_preds.append(alt_preds_shift)
                    alt_preds = np.array(alt_preds)

                    ism_scores = snps.compute_scores(
                        ref_preds, alt_preds, options.snp_stats, None
                    )
                    for snp_stat in options.snp_stats:
                        scores_h5[snp_stat][si, mi - mut_start, ni] = ism_scores[
                            snp_stat
                        ]

    # close output HDF5
    scores_h5.close()


################################################################################
# __main__
################################################################################
if __name__ == "__main__":
    main()
