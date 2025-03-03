import subprocess

import h5py
import numpy as np
import pandas as pd

from baskerville.dataset import targets_prep_strand

stat_keys = ["logSUM", "logD2"]
fasta_file = "tests/data/hg38_1m.fa.gz"
targets_file = "tests/data/tiny/hg38/targets.txt"
params_file = "tests/data/eval/params.json"
model_file = "tests/data/eval/model.h5"
snp_out_dir = "tests/data/snp/eqtl_out"


def test_snp():
    cmd = [
        "src/baskerville/scripts/hound_snp.py",
        "-f",
        fasta_file,
        "-o",
        snp_out_dir,
        "--stats",
        ",".join(stat_keys),
        "-t",
        targets_file,
        params_file,
        model_file,
        "tests/data/snp/eqtl.vcf",
    ]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)

    scores_file = "tests/data/snp/eqtl_out/scores.h5"
    with h5py.File(scores_file, "r") as scores_h5:
        for sk in stat_keys:
            score = scores_h5[sk][:]
            score_var = score.var(axis=0, dtype="float32")

            # verify shapes
            assert score.shape == (8, 47)

            # verify not NaN
            assert not np.isnan(score).any()

            # verify variance
            assert (score_var > 0).all()


def test_flip():
    # score SNPs
    flip_out_dir = "tests/data/snp/flip_out"
    cmd = [
        "src/baskerville/scripts/hound_snp.py",
        "-f",
        fasta_file,
        "-o",
        flip_out_dir,
        "--stats",
        ",".join(stat_keys),
        "-t",
        targets_file,
        params_file,
        model_file,
        "tests/data/snp/eqtl_flip.vcf",
    ]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)

    scores_file = f"{snp_out_dir}/scores.h5"
    with h5py.File(scores_file, "r") as scores_h5:
        score_sum = scores_h5["logSUM"][:]
        score_d2 = scores_h5["logD2"][:]

    scores_flip_file = f"{flip_out_dir}/scores.h5"
    with h5py.File(scores_flip_file, "r") as scores_h5:
        score_sum_flip = scores_h5["logSUM"][:]
        score_d2_flip = scores_h5["logD2"][:]

    assert np.allclose(score_sum, -score_sum_flip)
    assert np.allclose(score_d2, score_d2_flip)


def test_slice():
    # slice targets
    targets_df = pd.read_csv(targets_file, sep="\t", index_col=0)
    rna_mask = np.array([desc.startswith("RNA") for desc in targets_df.description])
    targets_rna_df = targets_df[rna_mask]
    targets_rna_file = targets_file.replace(".txt", "_rna.txt")
    targets_rna_df.to_csv(targets_rna_file, sep="\t")

    # score SNPs
    slice_out_dir = "tests/data/snp/slice_out"
    cmd = [
        "src/baskerville/scripts/hound_snp.py",
        "-f",
        fasta_file,
        "-o",
        slice_out_dir,
        "--stats",
        ",".join(stat_keys),
        "-t",
        targets_rna_file,
        params_file,
        model_file,
        "tests/data/snp/eqtl.vcf",
    ]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)

    # stranded mask
    targets_strand_df = targets_prep_strand(targets_df)
    rna_strand_mask = np.array(
        [desc.startswith("RNA") for desc in targets_strand_df.description]
    )

    # verify all close
    for sk in stat_keys:
        with h5py.File(f"{snp_out_dir}/scores.h5", "r") as scores_h5:
            score_full = scores_h5[sk][:].astype("float32")
            score_full = score_full[..., rna_strand_mask]
        with h5py.File(f"{slice_out_dir}/scores.h5", "r") as scores_h5:
            score_slice = scores_h5[sk][:].astype("float32")
        assert np.allclose(score_full, score_slice)
