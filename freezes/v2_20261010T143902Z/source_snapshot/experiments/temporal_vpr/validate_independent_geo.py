"""Reproject every listed GPS position with existing PROJ; no images or retrieval scores."""
import re,json,csv
from pathlib import Path
import numpy as np
from prepare_independent import parse_name
from runtime import Run,digest,update_state
ROOT=Path(__file__).resolve().parents[2]

def main():
    listing=ROOT/'outputs_v2/g1_independent_metadata_20261010T132115Z_756b6ce2/stdout.log'
    rows=[dict(path=l.split()[-1],**parse_name(l.split()[-1])) for l in listing.read_text().splitlines() if l.startswith('-') and l.endswith('.jpg')]
    assert len(rows)==3013
    run=Run(ROOT,'g4_GPS_UTM_crosscheck',dict(role='independent metadata only',source='https://proj.org/en/stable/apps/cs2cs.html',
        WGS84_to_UTM_zone56_south=True,rounding_consistency_tolerance_m=2),dict(listing_sha256=digest(listing)))
    print(run.id,flush=True)
    coordinates=run.path/'coordinates.tsv';coordinates.write_text(''.join(f'{r["longitude"]} {r["latitude"]}\n' for r in rows))
    run.command(['cs2cs','-f','%.3f','+proj=longlat','+datum=WGS84','+to','+proj=utm','+zone=56','+south','+datum=WGS84',str(coordinates)])
    values=[list(map(float,l.split()[:2])) for l in (run.path/'stdout.log').read_text().splitlines() if re.match(r'^\d+\.\d+\s+\d+\.\d+',l)]
    assert len(values)==len(rows)
    distances=np.linalg.norm(np.array(values)-np.array([[r['easting'],r['northing']] for r in rows]),axis=1)
    assert distances.max()<2,distances.max()
    run.write('metrics.json',dict(metadata_only=True,positions_verified=len(rows),maximum_GPS_reprojection_difference_m=float(distances.max()),
        median_difference_m=float(np.median(distances)),expected_rounding='lat/lon five decimal degrees; UTM two decimal metres',UTM='WGS84 zone56 south, latitude bandJ'))
    run.write('checks.json',dict(passed=True,all_positions_geographic_projected_consistent=True,independent_retrieval_unopened=True))
    with (run.path/'per_query.csv').open('w',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=['source_path','GPS_UTM_difference_m']);w.writeheader();w.writerows(dict(source_path=r['path'],GPS_UTM_difference_m=float(d)) for r,d in zip(rows,distances))
    (run.path/'interpretation.md').write_text('Existing system PROJ reprojects public dataset GPS into WGS84 zone56 south. All labels agree within the declared rounding tolerance. GPS is offline GT only; no image matching or independent performance read. No system package installed.\n')
    update_state(ROOT,g4_geo_audit_run=run.id,latest_run_id=run.id)
    print(json.dumps(dict(run=run.id,maximum_m=float(distances.max()))),flush=True)

if __name__=='__main__':main()
