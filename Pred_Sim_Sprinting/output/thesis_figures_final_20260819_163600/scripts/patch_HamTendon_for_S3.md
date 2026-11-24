# HamTendon patch (for reproducing Figure S3 tendon-slack-length family)

To respect "do not overwrite original files", the source edits used to generate the
`_HamTendon_*` results were **reverted** after the MAT files were produced
(`MainFunctions/main_pred_sim_sprinting.m` and `MainFunctions/checkSimulationType.m`
are back to their committed state at `e7b8de9`, verified `git diff` clean).

The two result MAT files already exist and Figure S3 reads them directly:
- `Results/pred_sprinting_data_19-August-2026__19-57-24___HamTendon_m10.mat` (TSL x0.90, strict)
- `Results/pred_sprinting_data_19-August-2026__21-27-52___HamTendon_p10.mat` (TSL x1.10, Maximum_CpuTime_Exceeded)

To RE-GENERATE from scratch, re-apply these three ADDITIVE, ASCII-only edits (they mirror the
existing HamFascicle/HamStrength hook and leave all other conditions byte-identical), then run
`run_pelvic_td_sweep({'_HamTendon_m10','_HamTendon_p10'})` at N=50 with `addpath('C:\casadi')`.

## 1. `MainFunctions/checkSimulationType.m` — after the `HamStrength` clause, before `HamPareto`:
```matlab
elseif ~isempty(strfind(simulation_type,'HamTendon'))
    % Hamstring muscle-architecture study (parameter sensitivity, Fig S3):
    % scales hamstring TENDON SLACK LENGTH (row 3). e.g. _HamTendon_m10 -> TSL
    % x0.90, _HamTendon_p10 -> TSL x1.10. Muscle parameters change only.
    file_ext = simulation_type;
```

## 2. `MainFunctions/main_pred_sim_sprinting.m` — archStudy parse (~L186):
```matlab
archStudy.active = ~isempty(strfind(simulation_type,'HamFascicle')) || ...
                   ~isempty(strfind(simulation_type,'HamStrength')) || ...
                   ~isempty(strfind(simulation_type,'HamTendon'));
...
    if ~isempty(strfind(simulation_type,'HamFascicle'))
        archStudy.mode = 'fascicle';
        aTok = simulation_type(strfind(simulation_type,'HamFascicle_')+numel('HamFascicle_'):end);
    elseif ~isempty(strfind(simulation_type,'HamStrength'))
        archStudy.mode = 'strength';
        aTok = simulation_type(strfind(simulation_type,'HamStrength_')+numel('HamStrength_'):end);
    else
        archStudy.mode = 'tendon';
        aTok = simulation_type(strfind(simulation_type,'HamTendon_')+numel('HamTendon_'):end);
    end
```

## 3. `MainFunctions/main_pred_sim_sprinting.m` — archStudy scaling (~L893):
```matlab
    if strcmp(archStudy.mode,'fascicle')
        MTparameters_m(2,hamIdx) = MTparameters_m(2,hamIdx) * archStudy.factor;
    elseif strcmp(archStudy.mode,'strength')
        MTparameters_m(1,hamIdx) = MTparameters_m(1,hamIdx) * archStudy.factor;
    elseif strcmp(archStudy.mode,'tendon')
        MTparameters_m(3,hamIdx) = MTparameters_m(3,hamIdx) * archStudy.factor;   % row 3 = tendon slack length
    end
```

Row 3 of `MTparameters_m` is tendon slack length (see main L958 `TSL_2_nsc = MTparameters_m(3,...)`);
`hamIdx = [7 8 9 10 53 54 55 56]` are the hamstring columns. Muscle 25 (`quad_fem_r`) is NOT touched.

## Finding
Tendon slack length is a FRAGILE parameter: -10% converged strict but with a large whole-motion
change (speed 11.57 m/s = -2.4%, tilt drift, biartic peak lMtilde 1.32); +10% FAILED
(Maximum_CpuTime_Exceeded, speed collapsed to 7.12). This contrasts with the well-behaved,
graded oMFL and Fmax families. Reported honestly in Figure S3 (red drift ring, failure x).
