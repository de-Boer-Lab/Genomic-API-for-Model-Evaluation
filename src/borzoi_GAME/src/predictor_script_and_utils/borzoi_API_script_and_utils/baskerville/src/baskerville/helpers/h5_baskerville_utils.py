import h5py
import numpy as np
import argparse


def collect_h5(file_name, out_dir, num_procs) -> None:
    """
    Concatenate all output files together
    Args:
        file_name: filename containing output (sad.h5)
        out_dir: directory containing output files
        num_procs: number of processes
    Returns: None
    """
    # count variants
    num_variants = 0
    for pi in range(num_procs):
        # open job
        job_h5_file = "%s/job%d/%s" % (out_dir, pi, file_name)
        job_h5_open = h5py.File(job_h5_file, "r")
        num_variants += len(job_h5_open["snp"])
        job_h5_open.close()

    # initialize final h5
    final_h5_file = "%s/%s" % (out_dir, file_name)
    final_h5_open = h5py.File(final_h5_file, "w")

    # keep dict for string values
    final_strings = {}

    job0_h5_file = "%s/job0/%s" % (out_dir, file_name)
    job0_h5_open = h5py.File(job0_h5_file, "r")
    for key in job0_h5_open.keys():
        if key in ["percentiles", "target_ids", "target_labels"]:
            # copy
            final_h5_open.create_dataset(key, data=job0_h5_open[key])

        elif key[-4:] == "_pct":
            values = np.zeros(job0_h5_open[key].shape)
            final_h5_open.create_dataset(key, data=values)

        elif job0_h5_open[key].dtype.char == "S":
            final_strings[key] = []

        elif job0_h5_open[key].ndim == 1:
            final_h5_open.create_dataset(
                key, shape=(num_variants,), dtype=job0_h5_open[key].dtype
            )

        else:
            num_targets = job0_h5_open[key].shape[1]
            final_h5_open.create_dataset(
                key, shape=(num_variants, num_targets), dtype=job0_h5_open[key].dtype
            )

    job0_h5_open.close()

    # set values
    vi = 0
    for pi in range(num_procs):
        # open job
        job_h5_file = "%s/job%d/%s" % (out_dir, pi, file_name)
        job_h5_open = h5py.File(job_h5_file, "r")

        # append to final
        for key in job_h5_open.keys():
            if key in ["percentiles", "target_ids", "target_labels"]:
                # once is enough
                pass

            elif key[-4:] == "_pct":
                # average
                u_k1 = np.array(final_h5_open[key])
                x_k = np.array(job_h5_open[key])
                final_h5_open[key][:] = u_k1 + (x_k - u_k1) / (pi + 1)

            else:
                if job_h5_open[key].dtype.char == "S":
                    final_strings[key] += list(job_h5_open[key])
                else:
                    job_variants = job_h5_open[key].shape[0]
                    try:
                        final_h5_open[key][vi : vi + job_variants] = job_h5_open[key]
                    except TypeError as e:
                        raise Exception(
                            f"{job_h5_file} ${key} has the wrong shape. Remove this file and rerun, {e}"
                        )

        vi += job_variants
        job_h5_open.close()

    # create final string datasets
    for key in final_strings:
        final_h5_open.create_dataset(key, data=np.array(final_strings[key], dtype="S"))

    final_h5_open.close()


def main():
    parser = argparse.ArgumentParser(description="Process and collect h5 files.")

    parser.add_argument("file_name", type=str, help="Path to the input file.")
    parser.add_argument(
        "out_dir", type=str, help="Output directory for processed data."
    )
    parser.add_argument("num_procs", type=int, help="Number of processes to use.")

    args = parser.parse_args()

    collect_h5(args.file_name, args.out_dir, args.num_procs)


if __name__ == "__main__":
    main()
