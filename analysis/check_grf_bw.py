#!/usr/bin/env python3
import sys, os, re, math

def split_tokens(line):
    return [t for t in re.split(r'[\t, ]+', line.strip()) if t!='']

def read_mot(path):
    with open(path,'r',encoding='latin-1') as f:
        lines = f.readlines()
    header_idx = None
    labels = None
    for i,line in enumerate(lines):
        toks = split_tokens(line)
        if len(toks)>1 and toks[0].lower()=='time':
            header_idx = i
            labels = toks
            break
    if header_idx is None:
        raise RuntimeError('Could not find header labels line starting with "time"')
    data_lines = [ln for ln in lines[header_idx+1:] if ln.strip()!='' and not ln.strip().lower().startswith('endheader')]
    data = []
    for ln in data_lines:
        toks = split_tokens(ln)
        try:
            row = [float(x) for x in toks]
            data.append(row)
        except ValueError:
            continue
    if len(data)==0:
        raise RuntimeError('No numeric data parsed from file')
    return labels, data

def main():
    if len(sys.argv)<2:
        print('Usage: check_grf_bw.py <path_to_.mot> [mass_kg]')
        sys.exit(1)
    mot = sys.argv[1]
    mass = float(sys.argv[2]) if len(sys.argv)>2 else 72.17
    labels, data = read_mot(mot)
    ncols = len(labels)
    print(f'Parsed {ncols} columns, {len(data)} rows from {mot}')

    # find indices
    try:
        idx_vx = labels.index('ground_force_vx')
        idx_vy = labels.index('ground_force_vy')
        idx_vz = labels.index('ground_force_vz')
    except ValueError:
        print('Total ground_force_vx/vy/vz labels not found in header')
        sys.exit(2)
    per_sphere_vy_idx = [i for i,l in enumerate(labels) if l.endswith('_ground_force_vy') and l != 'ground_force_vy']
    per_sphere_vx_idx = [i for i,l in enumerate(labels) if l.endswith('_ground_force_vx') and l != 'ground_force_vx']
    per_sphere_vz_idx = [i for i,l in enumerate(labels) if l.endswith('_ground_force_vz') and l != 'ground_force_vz']

    print(f'Found {len(per_sphere_vy_idx)} per-sphere vertical columns')

    total_vy = [row[idx_vy] for row in data]
    total_vx = [row[idx_vx] for row in data]
    total_vz = [row[idx_vz] for row in data]

    summed_vy = [sum(row[i] for i in per_sphere_vy_idx) if per_sphere_vy_idx else 0.0 for row in data]
    summed_vx = [sum(row[i] for i in per_sphere_vx_idx) if per_sphere_vx_idx else 0.0 for row in data]
    summed_vz = [sum(row[i] for i in per_sphere_vz_idx) if per_sphere_vz_idx else 0.0 for row in data]

    # Check both signs (some pipelines negate per-sphere sums)
    diffs_vy = [abs(t - s) for t,s in zip(total_vy, summed_vy)]
    diffs_vy_neg = [abs(t + s) for t,s in zip(total_vy, summed_vy)]
    max_diff_vy = max(diffs_vy)
    max_diff_vy_neg = max(diffs_vy_neg)
    use_neg = max_diff_vy_neg < max_diff_vy
    best_max_vy = max_diff_vy_neg if use_neg else max_diff_vy

    # Horizontal resultant
    horiz_res_total = [math.hypot(x,z) for x,z in zip(total_vx,total_vz)]
    horiz_res_summed = [math.hypot(x,z) for x,z in zip(summed_vx,summed_vz)]
    diffs_h = [abs(a-b) for a,b in zip(horiz_res_total,horiz_res_summed)]
    max_diff_h = max(diffs_h)

    peak_vy = max(abs(x) for x in total_vy)
    peak_h = max(horiz_res_total)
    BW = mass * 9.80665
    bw_vy = peak_vy / BW
    bw_h = peak_h / BW

    print('\n--- Comparison results ---')
    print(f'Use negation of per-sphere when comparing: {use_neg}')
    print(f'Max absolute vertical difference (best): {best_max_vy:.6f} N')
    print(f'Max absolute horizontal resultant difference: {max_diff_h:.6f} N')
    print(f'Peak total vertical: {peak_vy:.3f} N ({bw_vy:.3f} BW)')
    print(f'Peak total horizontal resultant: {peak_h:.3f} N ({bw_h:.3f} BW)')
    print(f'Model mass used: {mass:.3f} kg; 1 BW = {BW:.3f} N')

    # tolerance check
    tol = 1e-6 if best_max_vy==0 else max(1e-6, 1e-3 * abs(peak_vy))
    consistent = best_max_vy <= tol
    print(f'Consistency within tolerance {tol:.6f} N: {consistent}')

if __name__=='__main__':
    main()
