# Helpful Tips and Notes

Working on and developing within a framework like GAME can come with a huge learning curve. Here are some tips and notes we compiled along the way.

## File Permissions

**Note:** You may need to change file permissions on your host machine before building the container. If you encounter permission errors during the build (specifically when copying files), try running `chmod 755 file_name` on your scripts/data before running the build command.

## Data & Dependencies

**Data Formatting:** Your data can be stored in any format in the `evaluator_data/` folder.

- If your data is already in the GAME API JSON format, you can use the generic evaluator API script directly.
- If your data is in another format (e.g. FASTA, BED), you can refer to the pre-built GAME modules for examples of how to parse these custom formats.

**Adding Dependencies:** Additional dependencies (Python libraries, system tools) should be added to the `.def` files in the `%post` section.

## Runtime & Isolation

**Binding Paths (`-B`):** By default, Apptainer may not see files on your host system. The `-B` flag is used to "bind" (mount) local directories into the container so it can access them.

- *Example:* `-B /scratch/user/local_data:/data` maps a folder on your host to `/data` inside the container.
- **Default Isolation:** Our pre-built GAME containers include the environment variable `APPTAINER_NO_MOUNT="home,tmp,proc,sys,dev"`. This provides a "safe default" by preventing these common host directories from being automatically mounted, keeping the container filesystem clean.
- **Full Isolation (`--containall`):** While our default settings hide host files, the `--containall` flag provides **complete isolation**. It creates separate namespaces for processes (PID) and IPC, and fully cleans the environment. We recommend using this flag to guarantee the most reproducible runs.

## GPU Support

If your model requires a GPU, you must add the `--nv` flag to your run command to expose the host's NVIDIA drivers to the container. For AMD GPUs, refer to [Apptainer's documentation](https://apptainer.org/docs/user/1.0/gpu.html#amd-gpus-rocm).
