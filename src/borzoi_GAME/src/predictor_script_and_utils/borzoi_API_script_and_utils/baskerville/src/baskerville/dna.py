# Copyright 2023 Calico LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =========================================================================
import random
import sys

import numpy as np

"""
dna.py

Basic methods to interact with DNA sequences.
"""


def dna_rc(seq: str):
    """Reverse complement a DNA sequence.

    Args:
      seq (str): DNA sequence.

    Returns:
      Reverse complement of the input sequence.
    """
    return seq.translate(str.maketrans("ATCGatcg", "TAGCtagc"))[::-1]


def dna_1hot(
    seq: str, seq_len: int = None, n_uniform: bool = False, n_sample: bool = False
):
    """Convert a DNA sequence to a 1-hot encoding.

    Args:
      seq (str): DNA sequence.
      seq_len (int): length to extend/trim sequences to.
      n_uniform (bool): represent N's as 0.25, forcing float16,
      n_sample (bool):  sample ACGT for N

    Returns:
      seq_code (np.array): 1-hot encoding of DNA sequence.
    """
    if seq_len is None:
        seq_len = len(seq)
        seq_start = 0
    else:
        if seq_len <= len(seq):
            # trim the sequence
            seq_trim = (len(seq) - seq_len) // 2
            seq = seq[seq_trim : seq_trim + seq_len]
            seq_start = 0
        else:
            seq_start = (seq_len - len(seq)) // 2

    seq = seq.upper()

    # map nt's to a matrix len(seq)x4 of 0's and 1's.
    if n_uniform:
        seq_code = np.zeros((seq_len, 4), dtype="float16")
    else:
        seq_code = np.zeros((seq_len, 4), dtype="bool")

    for i in range(seq_len):
        if i >= seq_start and i - seq_start < len(seq):
            nt = seq[i - seq_start]
            if nt == "A":
                seq_code[i, 0] = 1
            elif nt == "C":
                seq_code[i, 1] = 1
            elif nt == "G":
                seq_code[i, 2] = 1
            elif nt == "T":
                seq_code[i, 3] = 1
            else:
                if n_uniform:
                    seq_code[i, :] = 0.25
                elif n_sample:
                    ni = random.randint(0, 3)
                    seq_code[i, ni] = 1

    return seq_code


def dna_1hot_index(seq: str, n_sample: bool = False):
    """Convert a DNA sequence to an index encoding.

    Args:
      seq (str): DNA sequence.
      n_sample (bool):  sample ACGT for N

    Returns:
      seq_code (np.array): Index encoding of DNA sequence.
    """
    seq_len = len(seq)
    seq = seq.upper()

    # map nt's to a len(seq) of 0,1,2,3
    seq_code = np.zeros(seq_len, dtype="uint8")

    for i in range(seq_len):
        nt = seq[i]
        if nt == "A":
            seq_code[i] = 0
        elif nt == "C":
            seq_code[i] = 1
        elif nt == "G":
            seq_code[i] = 2
        elif nt == "T":
            seq_code[i] = 3
        else:
            if n_sample:
                seq_code[i] = random.randint(0, 3)
            else:
                seq_code[i] = 4

    return seq_code


def hot1_augment(Xb, fwdrc: bool = True, shift: int = 0):
    """Transform a batch of one hot coded sequences to augment training.

    Args:
      Xb (np.array): Batch x Length x 4 one hot coded sequences.
      fwdrc (bool): Representing forward versus reverse complement strand.
      shift (int): Shift sequences by this many positions.

    Returns:
      Xbt (np.array): Transformed batch of sequences.
    """
    if Xb.ndim == 2:
        singleton = True
        Xb = np.expand_dims(Xb, axis=0)
    else:
        singleton = False

    if Xb.dtype == bool:
        nval = 0
    else:
        nval = 0.25

    if shift == 0:
        Xbt = Xb

    elif shift > 0:
        Xbt = np.zeros(Xb.shape, dtype=Xb.dtype)

        # fill in left unknowns
        Xbt[:, :shift, :] = nval

        # fill in sequence
        Xbt[:, shift:, :] = Xb[:, :-shift, :]
        # e.g.
        # Xbt[:,1:,] = Xb[:,:-1,:]

    elif shift < 0:
        Xbt = np.zeros(Xb.shape)

        # fill in right unknowns
        Xbt[:, shift:, :] = nval

        # fill in sequence
        Xbt[:, :shift, :] = Xb[:, -shift:, :]
        # e.g.
        # Xb_shift[:,:-1,:] = Xb[:,1:,:]

    if not fwdrc:
        Xbt = hot1_rc(Xbt)

    if singleton:
        Xbt = Xbt[0]

    return Xbt


def hot1_delete(seq_1hot, pos: int, delete_len: int, pad_value=None):
    """Delete nucleotides starting at a given position
       in the Lx4 1-hot encoded sequence.

    Args:
      seq_1hot (np.array): 1-hot encoded sequence.
      pos (int): Position to start deleting.
      delete_len (int): Number of nucleotides to delete.
      pad_value (float): Value to pad the end with.

    Returns:
      seq_1hot (np.array): In-place transformed sequence.
    """
    # shift left
    seq_1hot[pos:-delete_len, :] = seq_1hot[pos + delete_len :, :]
    # e.g.
    # seq_1hot[100:-3,:] = seq_1hot[100+3:,:]

    # change right end to N's
    if pad_value is None:
        if seq_1hot.dtype == bool:
            pad_value = 0
        else:
            pad_value = 0.25

    seq_1hot[-delete_len:, :4] = pad_value


def hot1_dna(seqs_1hot):
    """Convert 1-hot coded sequences to ACGTN.

    Args:
      seq_1hot (np.array): 1-hot encoded sequences.

    Returns:
      seqs [str]: List of DNA sequences.
    """

    singleton = False
    if seqs_1hot.ndim == 2:
        singleton = True
        seqs_1hot = np.expand_dims(seqs_1hot, 0)

    seqs = []
    for si in range(seqs_1hot.shape[0]):
        seq_list = ["A"] * seqs_1hot.shape[1]
        for li in range(seqs_1hot.shape[1]):
            if seqs_1hot[si, li, 0] == 1:
                seq_list[li] = "A"
            elif seqs_1hot[si, li, 1] == 1:
                seq_list[li] = "C"
            elif seqs_1hot[si, li, 2] == 1:
                seq_list[li] = "G"
            elif seqs_1hot[si, li, 3] == 1:
                seq_list[li] = "T"
            else:
                seq_list[li] = "N"

        seqs.append("".join(seq_list))

    if singleton:
        seqs = seqs[0]

    return seqs


def hot1_get(seqs_1hot, pos: int):
    """Return the nucleotide corresponding to the one hot coding
      of position "pos" in the Lx4 array seqs_1hot.

    Args:
      seqs_1hot (np.array): 1-hot encoded sequences.
      pos (int): Position to get nucleotide.

    Returns:
      nt (str): Nucleotide.
    """
    if seqs_1hot[pos, 0] == 1:
        nt = "A"
    elif seqs_1hot[pos, 1] == 1:
        nt = "C"
    elif seqs_1hot[pos, 2] == 1:
        nt = "G"
    elif seqs_1hot[pos, 3] == 1:
        nt = "T"
    else:
        nt = "N"
    return nt


def hot1_insert(seq_1hot, pos: int, insert_seq: str):
    """Insert sequence at a given position in the 1-hot encoded sequence.

    Args:
      seq_1hot (np.array): 1-hot encoded sequence.
      pos (int): Position to insert sequence.
      insert_seq (str): Sequence to insert.

    Returns:
      seq_1hot (np.array): In-place transformed sequence.
    """
    # shift right
    seq_1hot[pos + len(insert_seq) :, :] = seq_1hot[pos : -len(insert_seq), :]
    # e.g.
    # seq_1hot[100+3:,:] = seq_1hot[100:-3,:]

    # reset
    seq_1hot[pos : pos + len(insert_seq), :4] = 0

    for i in range(len(insert_seq)):
        nt = insert_seq[i]

        # set
        if nt == "A":
            seq_1hot[pos + i, 0] = 1
        elif nt == "C":
            seq_1hot[pos + i, 1] = 1
        elif nt == "G":
            seq_1hot[pos + i, 2] = 1
        elif nt == "T":
            seq_1hot[pos + i, 3] = 1
        else:
            print("Invalid nucleotide insert %s" % nt, file=sys.stderr)


def hot1_rc(seqs_1hot):
    """Reverse complement a batch of one hot coded sequences,
       while being robust to additional tracks beyond the four
       nucleotides.

    Args:
      seqs_1hot (np.array): 1-hot encoded sequences.

    Returns:
      seqs_1hot_rc (np.array): Reverse complemented sequences.
    """
    if seqs_1hot.ndim == 2:
        singleton = True
        seqs_1hot = np.expand_dims(seqs_1hot, axis=0)
    else:
        singleton = False

    seqs_1hot_rc = seqs_1hot.copy()

    # reverse
    seqs_1hot_rc = seqs_1hot_rc[:, ::-1, :]

    # swap A and T
    seqs_1hot_rc[:, :, [0, 3]] = seqs_1hot_rc[:, :, [3, 0]]

    # swap C and G
    seqs_1hot_rc[:, :, [1, 2]] = seqs_1hot_rc[:, :, [2, 1]]

    if singleton:
        seqs_1hot_rc = seqs_1hot_rc[0]

    return seqs_1hot_rc


def hot1_set(seq_1hot, pos: int, nt: str):
    """Set position in a 1-hot encoded sequence to given nucleotide.

    Args:
      seq_1hot (np.array): 1-hot encoded sequence.
      pos (int): Position to set nucleotide.
      nt (str): Nucleotide to set.

    Returns:
      seq_1hot (np.array): In-place transformed sequence.
    """
    # reset
    seq_1hot[pos, :4] = 0

    # set
    if nt == "A":
        seq_1hot[pos, 0] = 1
    elif nt == "C":
        seq_1hot[pos, 1] = 1
    elif nt == "G":
        seq_1hot[pos, 2] = 1
    elif nt == "T":
        seq_1hot[pos, 3] = 1
    else:
        print("Invalid nucleotide set %s" % nt, file=sys.stderr)
