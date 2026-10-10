# Eight real examples

Selection rule was committed before outputs. Photos remain local; regenerate with G1.
- repairable_r4: query 8 (st_lucia:independent_query:@0500273.42@6957730.69@56@J@-27.50408@0153.00276@210809_1210_00206@@@@@@@@.jpg); A/T/L3 distances 4.05m, 12.37m, 4.05m
- repairable_r4: query 16 (st_lucia:independent_query:@0500387.99@6957754.50@56@J@-27.50387@0153.00392@210809_1210_00307@@@@@@@@.jpg); A/T/L3 distances 6.85m, 21.80m, 6.85m
- unrepairable_r16: query 9 (st_lucia:independent_query:@0500285.60@6957734.94@56@J@-27.50404@0153.00289@210809_1210_00218@@@@@@@@.jpg); A/T/L3 distances 2.71m, 25.21m, 2.42m
- unrepairable_r16: query 10 (st_lucia:independent_query:@0500298.77@6957738.63@56@J@-27.50401@0153.00302@210809_1210_00231@@@@@@@@.jpg); A/T/L3 distances 3.00m, 11.58m, 2.18m
- A_correct_T_wrong: query 17 (st_lucia:independent_query:@0500402.48@6957758.56@56@J@-27.50383@0153.00407@210809_1210_00319@@@@@@@@.jpg); A/T/L3 distances 6.85m, 22.40m, 6.85m
- A_correct_T_wrong: query 18 (st_lucia:independent_query:@0500416.80@6957764.47@56@J@-27.50378@0153.00421@210809_1210_00334@@@@@@@@.jpg); A/T/L3 distances 6.94m, 11.43m, 6.94m
- multiwindow_disagreement: query 11 (st_lucia:independent_query:@0500312.93@6957741.77@56@J@-27.50398@0153.00316@210809_1210_00243@@@@@@@@.jpg); A/T/L3 distances 4.80m, 9.93m, 7.30m
- multiwindow_disagreement: query 12 (st_lucia:independent_query:@0500327.41@6957744.35@56@J@-27.50396@0153.00331@210809_1210_00257@@@@@@@@.jpg); A/T/L3 distances 4.89m, 8.58m, 4.89m

## Authoritative case audit correction
Original unrepairable_r16 rows were explicitly category_matches=false because H3/r16 covered all errors; those rows are fallback examples, not true negatives. Use g1_case_audit_20261010T170505Z_f3faea2a for all eight category-matched examples, centered on H1 for r16 negatives.
- repairable_H1_r4: q8; A=4.05m, fixed_L9=12.37m, full_L3=4.05m
- repairable_H1_r4: q16; A=6.85m, fixed_L9=21.80m, full_L3=6.85m
- unrepairable_H1_r16: q9; A=2.71m, fixed_L9=25.21m, full_L3=2.42m
- unrepairable_H1_r16: q10; A=3.00m, fixed_L9=11.58m, full_L3=2.18m
- A_correct_T_wrong: q17; A=6.85m, fixed_L9=22.40m, full_L3=6.85m
- A_correct_T_wrong: q18; A=6.94m, fixed_L9=11.43m, full_L3=6.94m
- multiwindow_disagreement: q11; A=4.80m, fixed_L9=9.93m, full_L3=7.30m
- multiwindow_disagreement: q12; A=4.89m, fixed_L9=8.58m, full_L3=4.89m
