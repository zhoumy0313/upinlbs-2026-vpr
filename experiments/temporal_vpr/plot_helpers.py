"""Turn actual development counts into labelled scientific plot points."""
def baseline_plot_points(metrics):
    points=[]
    for row in metrics['results']:
        s=row['settings']
        if row['split']!='validation' or not row['method'].startswith('temporal_') or len(s['velocities'])!=3:
            continue
        value=row['common']['R@1'];n=value['queries'];correct=value['correct']
        if n<=0 or not 0<=correct<=n or abs(value['recall']-correct/n)>1e-12:
            raise ValueError('Inconsistent numerator/denominator for plot point')
        points.append(dict(method=row['method'],length=s['length'],weight=s['weight'],correct=correct,
            queries=n,R1=correct/n,data_role='development validation common mask'))
    if not points:raise ValueError('No actual predeclared full-velocity grid points')
    return points
