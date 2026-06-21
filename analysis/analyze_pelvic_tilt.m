function analyze_pelvic_tilt()
% ANALYZE_PELVIC_TILT  Cross-condition hamstring strain-risk analysis for the
% pelvic-tilt sprinting study. Loads every _PelvisTilt_* result (plus the
% newest _Nominal as reference) from the Results folder, computes hamstring
% strain-injury metrics, and writes a summary CSV + figures to
% Results/PelvicTilt_Study/.
%
% Run headless:  matlab -nosplash -nodesktop -wait -r "analyze_pelvic_tilt; exit"

scriptDir = fileparts(mfilename('fullpath'));     % analysis
projRoot  = fileparts(scriptDir);
resDir    = fullfile(projRoot,'Results');
outDir    = fullfile(resDir,'PelvicTilt_Study');
if ~exist(outDir,'dir'); mkdir(outDir); end

diary(fullfile(outDir,'analysis_log.txt')); diary on;
fprintf('=== analyze_pelvic_tilt %s ===\n', datestr(now));

% ---- Hamstring rows in the 92-muscle muscleValues arrays --------------
% Rows 1-46 = LEFT side, 47-92 = RIGHT side; within a side the order follows
% muscleNames: semimem, semiten, bifemlh, bifemsh at positions 7,8,9,10.
hamNames = {'semimem','semiten','bifemlh','bifemsh'};
hamL = [7 8 9 10];
hamR = [53 54 55 56];

% ---- Gather condition files ------------------------------------------
ptFiles = dir(fullfile(resDir,'pred_sprinting_data_*PelvisTilt*.mat'));
% Newest N=50 Nominal as reference, matching the sweep mesh. Fall back to the
% newest Nominal if older results do not expose options.N.
nomFiles = dir(fullfile(resDir,'pred_sprinting_data_*Nominal.mat'));
refList = {};
if ~isempty(nomFiles)
    bestIx = 0; bestTime = -inf; fallbackIx = 0; fallbackTime = -inf;
    for iNom = 1:numel(nomFiles)
        if nomFiles(iNom).datenum > fallbackTime
            fallbackTime = nomFiles(iNom).datenum; fallbackIx = iNom;
        end
        try
            tmp = load(fullfile(nomFiles(iNom).folder,nomFiles(iNom).name),'optimumOutput');
            if isfield(tmp,'optimumOutput') && isfield(tmp.optimumOutput,'options') && ...
                    isfield(tmp.optimumOutput.options,'N') && tmp.optimumOutput.options.N == 50 && ...
                    nomFiles(iNom).datenum > bestTime
                bestTime = nomFiles(iNom).datenum; bestIx = iNom;
            end
        catch
        end
    end
    if bestIx == 0; bestIx = fallbackIx; end
    refList = {fullfile(nomFiles(bestIx).folder,nomFiles(bestIx).name)};
end

% For each PelvisTilt condition keep only the newest file of that token
tokens = containers.Map('KeyType','char','ValueType','char');
tokTime = containers.Map('KeyType','char','ValueType','double');
for i=1:numel(ptFiles)
    nm = ptFiles(i).name;
    tk = regexp(nm,'PelvisTilt_[mp]\d+','match','once');
    if isempty(tk); continue; end
    if ~isKey(tokTime,tk) || ptFiles(i).datenum > tokTime(tk)
        tokTime(tk) = ptFiles(i).datenum;
        tokens(tk)  = fullfile(ptFiles(i).folder,nm);
    end
end
ptList = values(tokens);

allFiles = [refList, ptList];
if isempty(ptList)
    fprintf('No _PelvisTilt_* results found in %s\n', resDir);
end

% ---- Build results table ---------------------------------------------
R = struct([]);
n = 0;
for i=1:numel(allFiles)
    f = allFiles{i};
    S = load(f); o = S.optimumOutput;
    nm = '';
    tk = regexp(f,'PelvisTilt_[mp]\d+','match','once');
    if isempty(tk)
        imposed = NaN; label = 'Nominal';
    else
        sgn = 1; if tk(12)=='m'; sgn=-1; end
        imposed = sgn*str2double(tk(13:end));
        label = sprintf('%+d deg', imposed);
    end

    q = o.optVars_nsc.q;
    ptilt = rad2deg(q(1,:));
    mv = o.muscleValues;

    try; status = o.stats.return_status; catch; status = 'unknown'; end

    % GRF sanity (peak vertical, body weight units) -- mass*g unknown here, so
    % report peak vertical GRF in N; report ~ if available
    try
        gv = max(o.GRFs.R(:,2));
    catch
        gv = NaN;
    end

    n = n+1;
    R(n).file     = f;
    R(n).label    = label;
    R(n).imposed  = imposed;
    R(n).status   = status;
    R(n).speed    = o.ave_speed;
    R(n).time     = o.optVars_nsc.totalTime;
    R(n).ptMean   = mean(ptilt);
    R(n).ptMin    = min(ptilt);
    R(n).ptMax    = max(ptilt);
    R(n).grfVpeak = gv;

    ncol = size(mv.lMtilde,2);
    for s = 1:2
        if s==1; rows=hamL; side='L'; else; rows=hamR; side='R'; end
        for h = 1:4
            r = rows(h);
            lM   = mv.lMtilde(r,:);
            vM   = mv.vMtilde(r,:);
            Fpe  = mv.Fpetilde(r,:);
            Fce  = mv.Fce(r,:);
            FMv  = mv.FMvtilde(r,:);
            ecc  = max(0,vM);
            if isfield(mv,'Fiso')
                Fiso = mv.Fiso(r,:);
                FceNorm = Fce ./ max(Fiso, eps);
            else
                FceNorm = Fce ./ max(max(abs(Fce)), eps);
            end
            eccLoad = ecc .* FMv;
            comp = lM .* ecc .* FceNorm;
            [peakLM, ix] = max(lM);
            fld = sprintf('%s_%s',hamNames{h},side);
            R(n).([fld '_peakLM'])   = peakLM;
            R(n).([fld '_tPeakPct']) = 100*(ix-1)/(ncol-1);
            R(n).([fld '_peakVMecc'])= max(ecc);
            R(n).([fld '_peakEccLoad']) = max(eccLoad);
            R(n).([fld '_peakFpe'])  = max(Fpe);
            R(n).([fld '_peakFceN']) = max(Fce);
            R(n).([fld '_peakFceNorm']) = max(FceNorm);
            R(n).([fld '_comp'])     = max(comp);
        end
    end
    for h = 1:4
        lFld = sprintf('%s_L_peakLM',hamNames{h});
        rFld = sprintf('%s_R_peakLM',hamNames{h});
        aFld = sprintf('%s_LRasym_peakLM_pct',hamNames{h});
        R(n).(aFld) = 100*abs(R(n).(lFld)-R(n).(rFld)) / max(mean([R(n).(lFld) R(n).(rFld)]), eps);
    end
end

% ---- Write summary CSV ------------------------------------------------
csvFile = fullfile(outDir,'pelvic_tilt_summary.csv');
flds = fieldnames(R);
flds = setdiff(flds,{'file'},'stable');
fid = fopen(csvFile,'w');
fprintf(fid,'%s,', flds{1:end-1}); fprintf(fid,'%s\n', flds{end});
for i=1:numel(R)
    for j=1:numel(flds)
        v = R(i).(flds{j});
        if ischar(v); fprintf(fid,'%s', v); else; fprintf(fid,'%.6g', v); end
        if j<numel(flds); fprintf(fid,','); end
    end
    fprintf(fid,'\n');
end
fclose(fid);
fprintf('Wrote %s\n', csvFile);

% ---- Sort PelvisTilt conditions by imposed angle for plotting ---------
ptIdx = find(~isnan([R.imposed]));
[~,ord] = sort([R(ptIdx).imposed]);
ptIdx = ptIdx(ord);
xv = [R(ptIdx).imposed];

cols = lines(4);
mk = {'-o','-s','-^','-d'};

% Figure 1: validation -- realized mean tilt vs imposed
f1 = figure('Visible','off','Position',[100 100 560 460]);
plot(xv,[R(ptIdx).ptMean],'-o','LineWidth',1.5,'MarkerFaceColor','b'); hold on;
plot(xv,xv,'k--');
xlabel('Imposed pelvis\_tilt centre (deg)');
ylabel('Realized mean pelvis\_tilt (deg)');
title('Imposed vs realized mean pelvic tilt');
legend('realized','identity','Location','best'); grid on;
print(f1,'-dpng','-r150',fullfile(outDir,'fig1_tilt_validation.png'));

% Figure 2: peak lMtilde vs imposed tilt (left & right hamstrings)
f2 = figure('Visible','off','Position',[100 100 900 420]);
for side=1:2
    sc = 'LR'; subplot(1,2,side);
    for h=1:4
        fld = sprintf('%s_%s_peakLM',hamNames{h},sc(side));
        plot(xv,[R(ptIdx).(fld)],mk{h},'Color',cols(h,:),'LineWidth',1.4,...
            'MarkerFaceColor',cols(h,:)); hold on;
    end
    plot([min(xv) max(xv)],[1.2 1.2],'k:');   % strain threshold guide
    xlabel('Imposed pelvis\_tilt (deg)'); ylabel('peak lMtilde');
    title(sprintf('%s hamstrings: peak fiber length', sc(side)));
    if side==1; legend(hamNames,'Location','best'); end
    grid on;
end
print(f2,'-dpng','-r150',fullfile(outDir,'fig2_peakLM.png'));

% Figure 3: peak passive force Fpetilde
f3 = figure('Visible','off','Position',[100 100 900 420]);
for side=1:2
    sc='LR'; subplot(1,2,side);
    for h=1:4
        fld = sprintf('%s_%s_peakFpe',hamNames{h},sc(side));
        plot(xv,[R(ptIdx).(fld)],mk{h},'Color',cols(h,:),'LineWidth',1.4,...
            'MarkerFaceColor',cols(h,:)); hold on;
    end
    xlabel('Imposed pelvis\_tilt (deg)'); ylabel('peak Fpetilde');
    title(sprintf('%s hamstrings: peak passive force', sc(side)));
    if side==1; legend(hamNames,'Location','best'); end
    grid on;
end
print(f3,'-dpng','-r150',fullfile(outDir,'fig3_peakFpe.png'));

% Figure 4: composite strain index + speed
f4 = figure('Visible','off','Position',[100 100 900 420]);
subplot(1,2,1);
for h=1:4
    fld = sprintf('%s_L_comp',hamNames{h});
    plot(xv,[R(ptIdx).(fld)],mk{h},'Color',cols(h,:),'LineWidth',1.4,...
        'MarkerFaceColor',cols(h,:)); hold on;
end
xlabel('Imposed pelvis\_tilt (deg)'); ylabel('peak lMtilde \cdot max(0,vMtilde) \cdot Fce/Fiso');
title('Composite strain-force risk index (L)'); legend(hamNames,'Location','best'); grid on;
subplot(1,2,2);
plot(xv,[R(ptIdx).speed],'-o','LineWidth',1.5,'MarkerFaceColor','b');
xlabel('Imposed pelvis\_tilt (deg)'); ylabel('average sprint speed (m/s)');
title('Sprint speed vs pelvic tilt'); grid on;
print(f4,'-dpng','-r150',fullfile(outDir,'fig4_composite_speed.png'));

fprintf('Figures written to %s\n', outDir);
fprintf('=== analysis done ===\n');
diary off;
end
