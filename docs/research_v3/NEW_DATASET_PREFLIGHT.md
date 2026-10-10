# New dataset preflight (metadata only)

Run g4_metadata_preflight_20261010T165525Z_4f8cf68e; actual HTTP status/errors and sizes are saved. Oxford camera downloads require account registration; no account/terms action performed. SFU is explicitly CC BY 4.0 with manual place bundles and ordered low-rate JPEGs; 15m GPS at 95% for dry/wet is unsuitable for strict independent 10m accuracy claims. Dry/wet left-A first, selected by listed order and compatible calibration, never by scores. Formatted downloader alternatives require independent source-license/order validation; SVOX/Tokyo/Pitts are not assumed temporal.

{
  "sources": [
    {
      "name": "Oxford_RobotCar",
      "url": "https://robotcar-dataset.robots.ox.ac.uk/ground_truth/",
      "status": 200,
      "bytes": 7882,
      "seconds": 2.3981779379973887,
      "source_content_sha256": "da484daaf341856553ec46d006f1e0c64e5b58a428ff1dd484110e0b5396ecdb"
    },
    {
      "name": "Oxford_login",
      "url": "https://mrgdatashare.robots.ox.ac.uk/",
      "status": 200,
      "bytes": 3491,
      "seconds": 2.7301665769991814,
      "source_content_sha256": "e2082f672bfaa0594575e0eb6ac36831f928f20f0762d6ce33a17155f1131c13",
      "login_required": true,
      "registration_not_performed": true
    },
    {
      "name": "SFU",
      "url": "https://autonomy.cs.sfu.ca/sfu-mountain-dataset/",
      "status": 200,
      "bytes": 106006,
      "seconds": 0.3851692819953314,
      "source_content_sha256": "72176737baa75107878b51966c12fc12301956fcb80964dffed06943f8e16143",
      "license_CC_BY_4": true,
      "manual_place_matches_available": true,
      "no_10m_metric_GT": true
    },
    {
      "name": "downloader",
      "url": "https://raw.githubusercontent.com/gmberton/VPR-datasets-downloader/main/README.md",
      "status": 200,
      "bytes": 11303,
      "seconds": 1.0171253090011305,
      "source_content_sha256": "c1e69c81d86c6f8277b2fe696865a29773c851af5dac637dd7008836f2e78095"
    }
  ],
  "heads": [
    {
      "url": "http://autolab.cmpt.sfu.ca/files/datasets/sfu-mountain-journal-version/place-matches/places-stereo_left-a.tar",
      "status": 502,
      "final_url": "http://autolab.cmpt.sfu.ca/files/datasets/sfu-mountain-journal-version/place-matches/places-stereo_left-a.tar",
      "content_length": 0,
      "content_type": "",
      "seconds": 3.4124970639968524
    },
    {
      "url": "https://autolab.cmpt.sfu.ca/files/datasets/sfu-mountain-journal-version/place-matches/places-stereo_left-a.tar",
      "error": "SSLError: HTTPSConnectionPool(host='autolab.cmpt.sfu.ca', port=443): Max retries exceeded with url: /files/datasets/sfu-mountain-journal-version/place-matches/places-stereo_left-a.tar (Caused by SSLError(SSLEOFError(8, '[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1007)')))",
      "seconds": 3.0020376870015753
    },
    {
      "url": "http://autolab.cmpt.sfu.ca/files/datasets/sfu-mountain-journal-version/zip/sfumd-dry-a-camera_stereo_left-0.3fps.tar",
      "status": 502,
      "final_url": "http://autolab.cmpt.sfu.ca/files/datasets/sfu-mountain-journal-version/zip/sfumd-dry-a-camera_stereo_left-0.3fps.tar",
      "content_length": 0,
      "content_type": "",
      "seconds": 10.490771355005563
    },
    {
      "url": "https://autolab.cmpt.sfu.ca/files/datasets/sfu-mountain-journal-version/zip/sfumd-dry-a-camera_stereo_left-0.3fps.tar",
      "error": "SSLError: HTTPSConnectionPool(host='autolab.cmpt.sfu.ca', port=443): Max retries exceeded with url: /files/datasets/sfu-mountain-journal-version/zip/sfumd-dry-a-camera_stereo_left-0.3fps.tar (Caused by SSLError(SSLEOFError(8, '[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1007)')))",
      "seconds": 3.001855330003309
    },
    {
      "url": "http://autolab.cmpt.sfu.ca/files/datasets/sfu-mountain-journal-version/zip/sfumd-wet-a-camera_stereo_left-0.3fps.tar",
      "status": 502,
      "final_url": "http://autolab.cmpt.sfu.ca/files/datasets/sfu-mountain-journal-version/zip/sfumd-wet-a-camera_stereo_left-0.3fps.tar",
      "content_length": 0,
      "content_type": "",
      "seconds": 10.616080673004035
    },
    {
      "url": "https://autolab.cmpt.sfu.ca/files/datasets/sfu-mountain-journal-version/zip/sfumd-wet-a-camera_stereo_left-0.3fps.tar",
      "error": "SSLError: HTTPSConnectionPool(host='autolab.cmpt.sfu.ca', port=443): Max retries exceeded with url: /files/datasets/sfu-mountain-journal-version/zip/sfumd-wet-a-camera_stereo_left-0.3fps.tar (Caused by SSLError(SSLEOFError(8, '[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1007)')))",
      "seconds": 3.0020665080010076
    }
  ]
}
