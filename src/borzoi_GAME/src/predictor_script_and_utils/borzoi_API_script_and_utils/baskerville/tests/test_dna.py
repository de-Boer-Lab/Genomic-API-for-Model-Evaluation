import pytest

import numpy as np

from baskerville import dna


def test_dna_rc():
    seq_dna = "GATTACA"
    seq_rc = dna.dna_rc(seq_dna)
    assert seq_rc == "TGTAATC"


ACGT_ARRAY = np.array(
    [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], dtype="bool"
)
ACNGT_FF_ARRAY = np.array(
    [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
    dtype="bool",
)
ACNGT_TF_ARRAY = np.array(
    [[1, 0, 0, 0], [0, 1, 0, 0], [0.25, 0.25, 0.25, 0.25], [0, 0, 1, 0], [0, 0, 0, 1]]
)

dna_1hot_cases = [
    (
        "ACGT",
        False,
        False,
        ACGT_ARRAY,
    ),
    (
        "ACNGT",
        False,
        False,
        ACNGT_FF_ARRAY,
    ),
    (
        "ACNGT",
        True,
        False,
        ACNGT_TF_ARRAY,
    ),
]


@pytest.mark.parametrize("seq_dna, n_uniform, n_sample, seq_1hot_hard", dna_1hot_cases)
def test_dna_1hot(seq_dna, n_uniform, n_sample, seq_1hot_hard):
    seq_1hot = dna.dna_1hot(seq_dna, n_uniform=n_uniform, n_sample=n_sample)
    assert np.array_equal(seq_1hot_hard, seq_1hot)


def test_dna_1hot_sum():
    seq_dna = "ACNGT"
    seq_1hot = dna.dna_1hot(seq_dna, n_sample=True)
    assert seq_1hot[2].sum() == 1


dna_1hot_index_cases = [
    ("ACGT", np.array([0, 1, 2, 3], dtype="uint8")),
    ("ACNGT", np.array([0, 1, 4, 2, 3], dtype="uint8")),
]


@pytest.mark.parametrize("seq_dna, seq_1hot_hard", dna_1hot_index_cases)
def test_dna_1hot_index(seq_dna, seq_1hot_hard):
    seq_1hot = dna.dna_1hot_index(seq_dna)
    assert np.array_equal(seq_1hot_hard, seq_1hot)


def test_dna_1hot_index_sample():
    seq_dna = "ACNGT"
    seq_1hot = dna.dna_1hot_index(seq_dna, n_sample=True)
    assert seq_1hot[2] in [0, 1, 2, 3]


def test_hot1_delete():
    seq_dna = "GATTACA"
    seq_1hot = dna.dna_1hot(seq_dna)
    dna.hot1_delete(seq_1hot, 3, 2)
    seq_dna_del = dna.hot1_dna(seq_1hot)
    assert "GATCANN" == seq_dna_del


def test_hot1_insert():
    seq_dna = "GATTACA"
    seq_1hot = dna.dna_1hot(seq_dna)
    dna.hot1_insert(seq_1hot, 3, "AG")
    seq_dna_ins = dna.hot1_dna(seq_1hot)
    assert "GATAGTA" == seq_dna_ins


def test_hot1_rc():
    #########################################
    # construct sequences
    seq1 = "GATTACA"
    seq1_1hot = dna.dna_1hot(seq1)

    seq2 = "TAGATAC"
    seq2_1hot = dna.dna_1hot(seq2)

    seqs_1hot = np.array([seq1_1hot, seq2_1hot])

    #########################################
    # reverse complement
    seqs_1hot_rc = dna.hot1_rc(seqs_1hot)

    seq1_rc = dna.hot1_dna(seqs_1hot_rc[0])
    seq2_rc = dna.hot1_dna(seqs_1hot_rc[1])

    #########################################
    # compare
    assert "TGTAATC" == seq1_rc
    assert "GTATCTA" == seq2_rc

    #########################################
    # reverse complement again
    seqs_1hot_rcrc = dna.hot1_rc(seqs_1hot_rc)

    seq1_rcrc = dna.hot1_dna(seqs_1hot_rcrc[0])
    seq2_rcrc = dna.hot1_dna(seqs_1hot_rcrc[1])

    #########################################
    # compare
    assert seq1 == seq1_rcrc
    assert seq2 == seq2_rcrc


seqs1 = np.array([dna.dna_1hot("GATTACA")])
dna_1hot_augment_cases = [
    (seqs1, True, 0, "GATTACA"),
    (seqs1, False, 0, "TGTAATC"),
    (seqs1, True, 1, "NGATTAC"),
    (seqs1, False, 1, "GTAATCN"),
    (seqs1, True, -1, "ATTACAN"),
    (seqs1, False, -1, "NTGTAAT"),
]


@pytest.mark.parametrize("seq_dna, fwdrc, shift, seq_aug_cmp", dna_1hot_augment_cases)
def test_dna_1hot_augment(seq_dna, fwdrc, shift, seq_aug_cmp):
    seq_aug = dna.hot1_augment(seq_dna, fwdrc=fwdrc, shift=shift)
    seq_aug_1hot = dna.hot1_dna(seq_aug)[0]
    assert seq_aug_cmp == seq_aug_1hot


def test_hot1_set():
    seq_dna = "GATTACA"
    seq_1hot = dna.dna_1hot(seq_dna)
    dna.hot1_set(seq_1hot, 3, "C")
    seq_dna_set = dna.hot1_dna(seq_1hot)
    assert "GATCACA" == seq_dna_set
