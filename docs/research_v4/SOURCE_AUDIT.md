# Official TUM source audit — metadata only, acquisition pending

Accessed 2026-10-11 using the web tool. These are source descriptions, not locally verified dataset measurements.

- [Official download page](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/download): Pioneer SLAM uses a Kinect mounted on a Pioneer robot with several loops; Long Office uses a handheld Asus Xtion and has end/start overlap. The overview estimates 1.82GB/1.58GB, whereas detailed sections estimate 1.51GB/1.38GB. Only measured local bytes and SHA will establish archive identity.
- [Official formats](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats): RGB PNG; timestamps are Unix seconds; pose columns are timestamp, tx, ty, tz, qx, qy, qz, qw. Translation describes the optical center of the RGB camera in a fixed motion-capture world frame. This project will evaluate 3D place distances, not 6DoF estimated-pose RMSE.
- [Official benchmark/license](https://cvg.cit.tum.de/data/datasets/rgbd-dataset): dataset CC BY 4.0 unless stated otherwise; accompanying code BSD-2-Clause. Cite Sturm, Engelhard, Endres, Burgard and Cremers, IROS 2012. Raw images still stay local under this goal; no third-party source body is republished.
- The download page explicitly identifies validation files as without public ground truth. Neither selected sequence is a validation bundle.

Both requested official URLs redirect to webshare.cvg.cit.tum.de. Browser retrieval of archive links failed; that alone does not establish host download failure. Actual Ubuntu curl runs, sanitized existing proxy endpoints, HTTP status/final URL/exit codes and measured bytes are being retained under outputs_v4/g0_download_*.

The scientific protocol in configs/v4/protocol_draft.yaml is an initial predeclaration only. It is not accepted/frozen until real files pass G0 and G1. No V4 retrieval metrics have been computed.

## Final observed acquisition outcome

Both official proxy-route curl commands completed with exit 35 after five retries; sole IPv4 direct fallback completed with exit 28. Both archives have zero local bytes and no SHA. No tar extraction was possible. Exact final URLs/HTTP codes and logs are retained in G0 evidence; official-source descriptions above are not claimed as local measurements.

## Resumed official-data audit

User supplied both requested official archive files on Oct.11. Both complete tar/gzip streams and safe extraction passed; all 5,506 RGB PNGs decoded. Archive identities, pose/GT association counts and spans are in DATA_MANIFEST_r02.json, now also the canonical DATA_MANIFEST.json. First missing-data manifest remains byte-identical as DATA_MANIFEST_r01_failure.json; original network failures remain. Original upstream independent published checksums were not available; official source attribution and transferred-file provenance are declared rather than claiming external checksum certification.
