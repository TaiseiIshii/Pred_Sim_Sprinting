# 実行例とスクリーンショットガイド

各ステップでの **具体的な画面出力**と **問題が起きた時の対応法**を詳しく説明します。

---

## Step 1: Conda 環境作成の実行例

### 実行コマンド

```powershell
PS C:\Users\T11648sTb\OneDrive...> .\setup_environment.ps1
```

### 期待される画面出力（成功時）

```
========================================
Pred_Sim_Sprinting Automated Setup
========================================

Project Root: c:\Users\T11648sTb\OneDrive - 国立研究開発法人産業技術総合研究所\ドキュメント\VSCODE\Pred_Sim_Sprinting\Pred_Sim_Sprinting

Checking Conda installation...
[OK] conda 4.13.0

Checking existing environment...

========================================
Creating Conda environment...
========================================

Collecting package metadata (repodata.json): done
Solving environment: done

Downloading and Extracting Packages
numpy-1.21.6          | 5.1 MB | ############ | 100%
pandas-1.3.5          | 2.3 MB | ############ | 100%
matplotlib-3.4.3      | 8.2 MB | ############ | 100%
scipy-1.7.3           | 12.3 MB | ############ | 100%
...

[OK] Environment created successfully

========================================
Testing installed packages...
========================================

[OK] All core packages imported successfully

========================================
Checking DLL compatibility...
========================================

Found 16 DLL file(s):

[OK] Running_ID.dll: 64-bit (x64)
[OK] Running_implicit.dll: 64-bit (x64)
[OK] Spr_Imp_GRFs_ownCont_V21.dll: 64-bit (x64)
... (全て [OK] で表示される)

[OK] All DLLs are 64-bit compatible!
MATLAB 2017b (64-bit) should work without issues.

========================================
Setup Complete!
========================================

Next steps:
1. Install CasADi MATLAB Toolbox (v3.3.0+)
   Download: https://web.casadi.org/get/

2. Open MATLAB R2017b and run:
   cd "プロジェクトルート"
   test_initial_setup

... (以下省略)

Press Enter to continue...
```

### よくあるエラーと対応

#### エラー: `conda: コマンドが見つかりません`

```
.\setup_environment.ps1 : ファイル C:\... を読み込めません。
このシステムではスクリプトの実行が禁止されています。
```

**対応:**

PowerShell を再度開いて、以下を実行：

```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\setup_environment.ps1
```

#### エラー: `Permission denied`

```
[ERROR] This script must be run as Administrator!
```

**対応:**

1. PowerShell を**右クリック**
2. **「管理者として実行」**を選択
3. 再度実行

#### 実行途中で止まる

```
Solving environment: |████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░| (時間がかかっています)
```

**対応:**

- このまま待ってください（5〜10分かかる場合もあります）
- キーボードを触らないでください

---

## Step 2: CasADi のダウンロード・インストール

### CasADi ダウンロードページの見方

ブラウザで https://web.casadi.org/get/ を開いた時の画面：

```
┌─────────────────────────────────────────────┐
│  CasADi - Get Started                       │
├─────────────────────────────────────────────┤
│                                             │
│ ▼ MATLAB Toolbox                            │
│   ┌─────────────────────────────────────┐  │
│   │ Get CasADi for MATLAB               │  │
│   │                                     │  │
│   │ CasADi 3.3.0                       │  │
│   │ casadi-3.3.0-win64-matlab2014b.zip │  │
│   │ [ Get CasADi ]  [Info]              │  │
│   │                                     │  │
│   │ CasADi 3.5.5                       │  │
│   │ casadi-3.5.5-win64-matlab2014b.zip │  │
│   │ [ Get CasADi ]  [Info]              │  │
│   │                                     │  │
│   │ CasADi 3.6.0                       │  │
│   │ casadi-3.6.0-win64-matlab2014b.zip │  │
│   │ [ Get CasADi ]  [Info]              │  │
│   │                                     │  │
│   └─────────────────────────────────────┘  │
│                                             │
│ ▼ Python Package                            │
│ ...                                         │
│                                             │
└─────────────────────────────────────────────┘
```

**3.3.0 または 3.5.0+ のいずれかをクリック**

### ZIP 解凍後のフォルダ構造

```
C:\casadi\  （解凍先）
├── casadi\  （★重要！このフォルダ）
│   ├── +casadi\  （さらに重要！）
│   │   ├── @DM\
│   │   ├── @Function\
│   │   ├── @GenericType\
│   │   └── ... その他のクラス
│   ├── examples\
│   │   ├── c_documentation.m
│   │   └── python_documentation.py
│   └── README.txt
├── LICENSE
└── CHANGELOG.txt
```

**`+casadi\` フォルダが見えることが重要です**

### MATLAB での CasADi 登録の実行例

```matlab
>> addpath(genpath('C:\casadi'))
>> savepath
Path saved to C:\Users\T11648sTb\AppData\Roaming\MathWorks\MATLAB\R2017b\pathdef.m
>> import casadi.*
>>
```

**最後に `>>` が表示されて、エラーが出なければ成功**

### よくあるエラーと対応

#### エラー: `警告: ディレクトリ ... が見つかりません`

```matlab
>> addpath(genpath('C:\wrong_path'))
警告: C:\wrong_path を見つけることができません。
```

**対応：**

1. フォルダパスを確認（ファイルエクスプローラーで確認）
2. 正しいパスで再度実行

#### エラー: `CasADi関数が見つからない`（後で出た場合）

```matlab
>> F = casadi.DM([1 2; 3 4])
未定義の関数または変数 'casadi' です。
```

**対応：**

```matlab
>> clear all
>> import casadi.*
>> F = casadi.DM([1 2; 3 4])
```

---

## Step 3: MATLAB セットアップテストの実行例

### 実行コマンドの例

```matlab
>> cd "c:\Users\T11648sTb\OneDrive - 国立研究開発法人産業技術総合研究所\ドキュメント\VSCODE\Pred_Sim_Sprinting\Pred_Sim_Sprinting"
>> pwd
ans =
    'c:\Users\...\Pred_Sim_Sprinting'
>> test_initial_setup
```

### 期待される出力（成功時）

```
========================================
Pred_Sim_Sprinting Initial Setup Test
========================================

Project Root: c:\Users\...\Pred_Sim_Sprinting

TEST 1: Path Setup
----------------------------------------
[OK] Path setup successful

TEST 2: CasADi Import
----------------------------------------
[OK] CasADi imported successfully
     Available CasADi functions can be used

TEST 3: Required Folders
----------------------------------------
[OK] MainFunctions
[OK] ExternalFunctions
[OK] MuscleModel
[OK] Polynomials
[OK] CollocationScheme
[OK] UtilityFunctions
[OK] OpenSimModel
[OK] Results

TEST 4: Critical Data Files
----------------------------------------
[OK] MuscleModel\Faparam.mat
[OK] MuscleModel\Fpparam.mat
[OK] MuscleModel\Fvparam.mat
[OK] Polynomials\muscle_spanning_joint_INFO_subject9.mat
[OK] OpenSimModel\Scaled_FullBody_HamnerModel_Muscle_withContact.osim

TEST 5: External DLL Files
----------------------------------------
[OK] Found 16 DLL file(s):
     - Running_ID.dll
     - Running_implicit.dll
     - Spr_Imp_GRFs_ownCont_V21.dll
     ... and 13 more

TEST 6: Main Script Availability
----------------------------------------
[OK] main_pred_sim_sprinting.m found

========================================
Setup Verification Summary
========================================
[OK] All required folders present
[OK] All critical data files present

Next Steps:
1. Ensure CasADi MATLAB toolbox is installed
   Download: https://web.casadi.org/get/
2. Run mainPolynomials.m to generate missing polynomial data
3. Run main_pred_sim_sprinting.m to start the simulation

========================================
Setup test completed!
========================================
```

### よくあるエラーと対応

#### エラー: `Undefined function or variable 'test_initial_setup'`

```
未定義の関数または変数 'test_initial_setup' です。
```

**原因：** プロジェクトフォルダが正しく設定されていない

**対応：**

```matlab
>> pwd
ans =
    'C:\Users\...'  ← これが Pred_Sim_Sprinting で終わっていない！

>> cd "c:\Users\T11648sTb\OneDrive..."  ← 正しいパスを入力
>> pwd
ans =
    'c:\Users\...\Pred_Sim_Sprinting'  ← OK！
>> test_initial_setup
```

#### エラー: `CasADi import failed`

```
TEST 2: CasADi Import
[ERROR] Failed to import CasADi: ...
```

**対応：**

Step 2.3 を再度実行：

```matlab
>> addpath(genpath('C:\casadi'))
>> savepath
>> import casadi.*
>> test_initial_setup  ← 再度実行
```

#### ファイルが見つからない警告

```
TEST 4: Critical Data Files
[WARN] Missing file: Polynomials\muscle_spanning_joint_INFO_subject9.mat
```

**対応：** 正常です！Step 4 でこのファイルを生成します

---

## Step 4: ポリノミアルデータ生成の実行例

### 実行コマンド

```matlab
>> setup_paths

========================================
Pred_Sim_Sprinting Path Setup
========================================
Project Root: c:\Users\...\Pred_Sim_Sprinting

[OK] Added: c:\Users\...\MainFunctions
[OK] Added: c:\Users\...\ExternalFunctions
...
[OK] CasADi imported successfully
========================================

>> run Polynomials/mainPolynomials.m
```

### 実行中の表示（進行状況）

```
Running polynomial fitting for muscles...
Processing muscle 1: Adductors
  Fitting moment arm polynomial...
  Fitting muscle length polynomial...
  Fitting velocity polynomial...
  [OK] Saved muscle data

Processing muscle 2: Biceps
  Fitting moment arm polynomial...
  ...

... (全筋肉について同様に処理)

Generating cache files...
[OK] Saving muscle_spanning_joint_INFO_subject9.mat
[OK] Saving MuscleInfo_subject9.mat
[OK] Saving MuscleData_subject9.mat

All polynomial data generated successfully!
>>
```

### 実行時間と進度の目安

| 進度 | 実行時間 | 目安 |
|------|--------|------|
| 筋肉 1-5 処理中 | 2-3 分 | 開始直後 |
| 筋肉 6-15 処理中 | 5-10 分 | 中盤 |
| キャッシュ生成 | 10-20 分 | ほぼ完了 |

**この間、MATLAB は反応しなくなりますが、大丈夫です**

### よくあるエラーと対応

#### エラー: `File not found: ExperimentalData`

```
Error: Cannot find file MainFunctions\ExperimentalData\...
```

**対応：** プロジェクト構造が破損しています

```matlab
>> pwd
>> ls MainFunctions/ExperimentalData
```

で確認し、ファイルが表示されるか確認

#### 実行途中で MATLAB が止まる

**これは正常です**。何もしないで待ってください。

**確認方法：**
- タスクマネージャーで MATLAB のプロセスが動作中か確認
- CPU 使用率が高い（50% 以上）か確認

#### メモリ不足エラー

```
Error: Out of memory
```

**対応：**

1. MATLAB を再起動
2. 他のアプリケーションを閉じる
3. 再度実行

---

## Step 5: メインシミュレーション実行の例

### 実行コマンド

```matlab
>> setup_paths
>> run MainFunctions/main_pred_sim_sprinting.m
```

### 実行開始直後の表示

```
========================================
Pred_Sim_Sprinting Main Simulation
========================================

Simulation type: Nominal
Loading OpenSim model...
[OK] Model loaded: Scaled_FullBody_HamnerModel_Muscle_withContact

Building NLP (Non-Linear Programming) problem...
[OK] NLP structure initialized

Building optimisation solver...
[OK] IPOPT solver configured
```

### 最適化が進行中の表示

```
Starting optimization...
========================================
NLP Solver Output:
========================================

Iteration 1: Optimality Error = 1.25e+01
Iteration 2: Optimality Error = 3.42e+00
Iteration 3: Optimality Error = 1.89e+00
Iteration 4: Optimality Error = 8.23e-01
Iteration 5: Optimality Error = 3.12e-01
...
Iteration 48: Optimality Error = 1.23e-04
Iteration 49: Optimality Error = 5.67e-05
Iteration 50: Optimality Error = 1.23e-06

========================================
Optimization completed successfully!
========================================
```

### 完了時の表示

```
Solution found!
Results:
  Final optimality: 1.23e-06
  Iterations: 50
  Time elapsed: 1247 seconds (約 20 分)

Saving results...
Exporting motion file (GRF)...
[OK] Saved to Results/pred_sprinting_2026-02-03__10-30-45__Nominal_GRF.mot

Exporting motion file (GRF Single)...
[OK] Saved to Results/pred_sprinting_2026-02-03__10-30-45__Nominal_GRF_Single.mot

========================================
Simulation completed successfully!
========================================
>>
```

### 実行時間の目安

| 段階 | 実行時間 | CPU 使用率 |
|------|--------|----------|
| NLP 構築 | 1-2 分 | 10-20% |
| 最適化開始 | 1-2 分 | 80-100% |
| **最適化進行中** | **15-30 分** | **100%** |
| 結果保存 | 1-2 分 | 20-50% |

**CPU 使用率が 100% でも問題ありません**

### よくあるエラーと対応

#### エラー: `CasADi external function not found`

```
Error using main_pred_sim_sprinting (line 415)
External function 'F_cont_v21' not found in ExternalFunctions
```

**原因：** DLL ファイルが見つからない

**対応：**

```matlab
>> ls ExternalFunctions/*.dll
```

で DLL ファイルが表示されるか確認

#### エラー: `Infeasible problem`

```
IPOPT: Infeasible problem detected
```

**対応：**

- これはまれなエラーです
- シミュレーション条件を変更して再度実行してください

#### 実行が途中で止まる

**確認方法：**

1. MATLAB が反応しているか確認（Command Window をクリック）
2. タスクマネージャーで MATLAB プロセスが実行中か確認
3. 30分待ってから、再度確認

---

## Step 6: 結果の後処理

### 実行コマンド

```powershell
(base) PS C:\Users\...> conda activate pred_sim_sprinting
(pred_sim_sprinting) PS C:\Users\...> cd "c:\Users\...\Pred_Sim_Sprinting"
(pred_sim_sprinting) PS C:\Users\...> python post_process_results.py
```

### 期待される出力

```
==================================================
Pred_Sim_Sprinting Post-Processing Tool
==================================================

Results directory: c:\Users\...\Results

Found 2 .mot file(s)

Processing: pred_sprinting_2026-02-03__10-30-45__Nominal_GRF.mot
[OK] Loaded pred_sprinting_2026-02-03__10-30-45__Nominal_GRF.mot
     Time range: 0.000 to 1.234 seconds
     Data points: 124
     Columns: 27
[OK] Exported to ...\Results\pred_sprinting_2026-02-03__10-30-45__Nominal_GRF.csv
[OK] Saved plot to ...\Results\plots\pred_sprinting_2026-02-03__10-30-45__Nominal_GRF_plot.png

Processing: pred_sprinting_2026-02-03__10-30-45__Nominal_GRF_Single.mot
...

==================================================
Post-processing completed!
==================================================
```

### 出力ファイルの確認

```powershell
(pred_sim_sprinting) PS C:\Users\...> ls Results\

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a---          2026/2/3  10:30          25 pred_sprinting_2026-02-03__10-30-45__Nominal_GRF.mot
-a---          2026/2/3  10:45          18 pred_sprinting_2026-02-03__10-30-45__Nominal_GRF.csv
-a---          2026/2/3  10:45          45 pred_sprinting_2026-02-03__10-30-45__Nominal_GRF_Single.mot
-a---          2026/2/3  10:45          16 pred_sprinting_2026-02-03__10-30-45__Nominal_GRF_Single.csv
d----          2026/2/3  10:45               plots

(pred_sim_sprinting) PS C:\Users\...> ls Results\plots\

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a---          2026/2/3  10:45         312345 pred_sprinting_2026-02-03__10-30-45__Nominal_GRF_plot.png
-a---          2026/2/3  10:45         267890 pred_sprinting_2026-02-03__10-30-45__Nominal_GRF_Single_plot.png
```

---

## Excel で CSV ファイルを開く方法

### 方法 1: ダブルクリック（簡単）

1. ファイルエクスプローラーで `Results/` フォルダを開く
2. `.csv` ファイルを**ダブルクリック**
3. Excel が自動的に開く

### 方法 2: Excel メニューから開く

1. Excel を起動
2. **ファイル** → **開く**
3. `Results/` フォルダを選択
4. `.csv` ファイルを選択

### CSV の内容例

```
time,contact_GRF_r_vy,contact_GRF_r_vz,contact_GRF_r_fx,...
0.000,0.0,145.3,12.4,...
0.001,0.0,142.1,13.2,...
0.002,0.0,138.9,14.1,...
...
```

各列は：
- `time`: 時刻（秒）
- `contact_GRF_r_vy`: 右足接地反力（前後方向）
- `contact_GRF_r_vz`: 右足接地反力（垂直方向）
- その他の筋肉角度など

---

## グラフを見る方法

### PNG ファイルをプレビュー

1. ファイルエクスプローラーで `Results/plots/` を開く
2. `.png` ファイルをダブルクリック
3. 画像ビューアで表示

### グラフの種類

- **接地反力**: 歩行中の地面との力
- **関節角度**: 股関節・膝関節・足関節の角度変化
- **筋活動**: 各筋肉の活動レベル

---

## トラブル：コマンドが見つからない場合

### 症状: `python: コマンドが見つかりません`

```
(pred_sim_sprinting) PS C:\...> python post_process_results.py
python : 用語 'python' は、コマンドレット、関数、スクリプト ファイル、または操作可能なプログラムの名前として認識されません。
```

**対応：**

```powershell
# Conda 環境がアクティベートされているか確認
(pred_sim_sprinting)  ← これが見えているか確認

# 見えない場合：
conda activate pred_sim_sprinting

# 再度実行
python post_process_results.py
```

---

**これで初学者でも確実に実装できます！**
