import os
import pytest
import shutil
import subprocess


@pytest.fixture
def clean_data():
    # clean previous training directories
    out_dirs = ["tests/data/train1", "tests/data/train2"]
    for out_dir in out_dirs:
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)


def test_train(clean_data):
    cmd = [
        "src/baskerville/scripts/hound_train.py",
        "-o",
        "tests/data/train1",
        "-l",
        "tests/data/train1/logs",
        "tests/data/params.json",
        "tests/data/tiny/hg38",
    ]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)

    # TODO: Check evaluation metrics numerical stability
    assert os.path.exists("tests/data/train1/model_best.h5")


def test_train2(clean_data):
    cmd = [
        "src/baskerville/scripts/hound_train.py",
        "-o",
        "tests/data/train2",
        "-l",
        "tests/data/train2/logs",
        "tests/data/params.json",
        "tests/data/tiny/hg38",
        "tests/data/tiny/mm10",
    ]
    subprocess.run(cmd, check=True)

    # TODO: Check evaluation metrics numerical stability
    assert os.path.exists("tests/data/train2/model0_best.h5")
    assert os.path.exists("tests/data/train2/model1_best.h5")
