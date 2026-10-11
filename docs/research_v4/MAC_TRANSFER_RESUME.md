# Resume from official Mac downloads

Ubuntu acquisition failed; this is the bounded manual transfer alternative specified by the V4 goal. No account is required for these TUM archives. Do not download `_validation` files, videos, or a different sequence.

1. On Mac, open the [official download page](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/download), select the **tgz** links for **freiburg2_pioneer_slam** and **freiburg3_long_office_household**. Keep the original filenames. The official links redirect to webshare.cvg.cit.tum.de. Browser/network reachability on the Mac is not verified by this Ubuntu session.
2. In Mac Terminal, verify the downloads and save their identities:

```bash
tar -tzf "$HOME/Downloads/rgbd_dataset_freiburg2_pioneer_slam.tgz" >/dev/null
tar -tzf "$HOME/Downloads/rgbd_dataset_freiburg3_long_office_household.tgz" >/dev/null
shasum -a 256 "$HOME/Downloads/rgbd_dataset_freiburg2_pioneer_slam.tgz" "$HOME/Downloads/rgbd_dataset_freiburg3_long_office_household.tgz"
```

3. Replace `UBUNTU_HOST` with the host or alias already used for your Ubuntu SSH connection. Transfer to the existing project; never upload raw files to GitHub:

```bash
scp "$HOME/Downloads/rgbd_dataset_freiburg2_pioneer_slam.tgz" aaron@UBUNTU_HOST:/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/data/raw/v4/tum_rgbd/archives/
scp "$HOME/Downloads/rgbd_dataset_freiburg3_long_office_household.tgz" aaron@UBUNTU_HOST:/home/aaron/upinlbs_vpr/upinlbs_vpr_starter/data/raw/v4/tum_rgbd/archives/
```

4. Once both files are present, tell Codex to resume VPR-GOAL-V4 from G0. The saved command below creates a new append-only audit and extraction run. It checks full gzip/tar readability, SHA256, expected roots, mandatory RGB/GT lists, duplicate names and rejects all archive links/devices/path escapes before extracting into a new directory. It does **not** automatically accept G0 or run retrieval. Codex will compare the transferred SHA values, decode/audit RGB, associate GT, validate the universal protocol and then progress G1–G6.

```bash
cd /home/aaron/upinlbs_vpr/upinlbs_vpr_starter
.venv-p0/bin/python experiments/temporal_alignment_v4/audit_data.py
```

No repeated Ubuntu download retry is required while connectivity is unchanged. No SSL verification bypass, unknown mirror, proxy reconfiguration or driver modification was used. The independent test remains unopened. If Mac also cannot reach the official host, preserve its error and keep the V4 science unexecuted.
