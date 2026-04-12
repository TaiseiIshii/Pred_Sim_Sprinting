# Pred_Sim_Sprinting - ローカルPC再現実装ガイド

**作成日:** 2026年2月3日  
**MATLAB対応バージョン:** 2017b以上  
**Python対応バージョン:** 3.7〜3.10  

---

## 概要

本ドキュメントは、Pred_Sim_Sprinting（スプリント走動作予測シミュレーション）をローカルPCで再現実装するための完全なセットアップ手順です。Conda仮想環境を使用して、他のプロジェクトに影響を与えない独立した環境を構築します。

### 環境構成

- **MATLAB 2017b** (64-bit)
- **CasADi 3.3.0** (MATLAB 2017b対応)
- **Python 3.9** (Conda仮想環境)
- **補助ライブラリ:** NumPy 1.21, Pandas 1.3, Matplotlib 3.4, SciPy 1.7

---

## セットアップ手順

### Step 1: システム前提条件の確認

**実行前に以下を確認してください:**

- [ ] **Windows 10/11 (64-bit)**
- [ ] **MATLAB 2017b (64-bit)** がインストール済み
  - 確認方法: MATLAB起動時に左下に "R2017b" と表示されることを確認
  - または MATLAB CommandWindow で `version` を実行
- [ ] **Miniconda または Anaconda** がインストール済み
  - 確認方法: PowerShell/CMD で `conda --version` を実行
- [ ] **Visual Studio 2015 Update 3 以上** (DLLコンパイルが必要な場合)
  - 本プロジェクトには64-bit DLLが同梱されているため、通常は不要です
  - DLLの再コンパイルが必要な場合のみ、C++ワークロードをインストール

### Step 2: Conda仮想環境の構築

#### 2.1 PowerShell/CMD を開く

```powershell
# Windows PowerShell を右クリック → 管理者として実行
# または CMD を右クリック → 管理者として実行
```

#### 2.2 プロジェクトディレクトリに移動

```bash
cd "c:\Users\<ユーザー名>\OneDrive - 国立研究開発法人産業技術総合研究所\ドキュメント\VSCODE\Pred_Sim_Sprinting\Pred_Sim_Sprinting"
```

#### 2.3 環境を構築

```bash
# 環境構築（初回のみ、5〜10分かかります）
conda env create -f environment.yml

# 環境の有効化
conda activate pred_sim_sprinting

# 検証
python -c "import numpy, pandas, matplotlib, scipy; print('[OK] All packages imported successfully')"
```

**出力例:**
```
[OK] All packages imported successfully
```

---

### Step 3: DLL互換性の確認

Pred_Sim_Springtingに同梱されているすべてのDLLが64-bitであることを確認します。

```powershell
# PowerShell で実行
powershell -NoProfile -ExecutionPolicy Bypass -File "check_dll_architecture.ps1"
```

**期待される出力:**
```
[OK] All DLLs are 64-bit compatible!
MATLAB 2017b (64-bit) should work without issues.
```

---

### Step 4: CasADi MATLAB Toolbox のインストール

#### 4.1 CasADiをダウンロード

1. https://web.casadi.org/get/ にアクセス
2. **MATLAB Toolbox** セクションから、**CasADi 3.3.0** (またはより新しい2017b対応バージョン) をダウンロード
3. ファイル名例: `casadi-3.3.0-win64-matlab2014b.zip`

#### 4.2 MATLAB にインストール

1. ダウンロードした ZIP ファイルを解凍
2. MATLAB を起動
3. MATLAB Command Window で以下を実行:

```matlab
% CasADiをMATLABパスに追加（フォルダ選択ダイアログが表示されます）
addpath(genpath('C:\path\to\casadi'));  % 解凍したフォルダを指定
savepath  % パスを保存

% インポート確認
import casadi.*
disp('[OK] CasADi imported successfully')
```

**トラブル時の確認:**
- `casadi/+casadi/` フォルダが存在するか確認
- MATLAB 2017b 64-bit で実行しているか確認

---

### Step 5: MATLAB パス設定とセットアップテスト

#### 5.1 MATLAB を起動

```
スタート → MATLAB R2017b
```

#### 5.2 プロジェクトルートを作業フォルダに設定

MATLAB Command Window で:

```matlab
% プロジェクトルートを現在のフォルダに設定
cd "c:\Users\<ユーザー名>\OneDrive - 国立研究開発法人産業技術総合研究所\ドキュメント\VSCODE\Pred_Sim_Sprinting\Pred_Sim_Sprinting"

% 確認
pwd  % プロジェクトルートが表示されることを確認
```

#### 5.3 セットアップテストを実行

```matlab
% 全パス・データファイルを自動設定
test_initial_setup

% 期待される出力:
% ✓ All required folders present
% ✓ All critical data files present
% ✓ CasADi imported successfully
```

**エラーが表示された場合:**
- Missing files の場合: Step 6 を実行してポリノミアルデータを生成
- CasADi import error の場合: Step 4 を再確認

---

### Step 6: ポリノミアルデータの生成（初回のみ）

一部のデータファイル（筋肉スパニング情報など）は自動生成が必要です。

```matlab
% プロジェクトルートが作業フォルダであることを確認
cd "Pred_Sim_Sprinting_root"

% ポリノミアル生成スクリプトを実行
run Polynomials/mainPolynomials.m

% 生成確認
% → Polynomials/ フォルダに以下が作成されます:
%    - muscle_spanning_joint_INFO_subject9.mat
%    - MuscleInfo_subject9.mat
%    - MuscleData_subject9.mat
```

**実行時間:** 5〜15分

---

### Step 7: 初回シミュレーション実行

基本的なシミュレーション（_Nominal条件）を実行します。

```matlab
% プロジェクトルートが作業フォルダであることを確認
cd "Pred_Sim_Sprinting_root"

% 初期化スクリプトを実行
setup_paths

% メインシミュレーションを実行
run MainFunctions/main_pred_sim_sprinting.m

% simulation_type = '_Nominal' で実行されます
```

**実行時間:** 10〜30分（PCのスペックに依存）

**出力ファイル:**
- `Results/pred_sprinting_<TIMESTAMP>_Nominal_GRF.mot`
- `Results/pred_sprinting_<TIMESTAMP>_Nominal_GRF_Single.mot`

---

### Step 8: 結果の後処理（Python）

Conda環境で結果ファイルをCSV化・可視化します。

#### 8.1 Conda環境を有効化

```bash
conda activate pred_sim_sprinting
```

#### 8.2 後処理スクリプトを実行

```bash
# プロジェクトルートで実行
python post_process_results.py
```

**出力:**
- `Results/*.csv` (各 .mot ファイルのCSV版)
- `Results/plots/*.png` (グラフ画像)

---

## その他のシミュレーション条件

`MainFunctions/main_pred_sim_sprinting.m` の以下の行を変更して、異なる条件でシミュレーションを実行できます:

```matlab
% Line 28 付近
simulation_type = '_Nominal';  % ← ここを変更
```

### 利用可能な条件

| 条件名 | simulation_type | 説明 |
|--------|---|---|
| **基準条件** | `'_Nominal'` | 標準設定 |
| **水平接地距離** | `'_HTD_Plus_1'` ～ `'_HTD_Plus_10'` | 接地距離を増加 |
| | `'_HTD_Minus_1'` ～ `'_HTD_Minus_10'` | 接地距離を減少 |
| **膝間接地距離** | `'_IKTD_Plus_1'` ～ `'_IKTD_Plus_10'` | 膝間距離を増加 |
| | `'_IKTD_Minus_1'` ～ `'_IKTD_Minus_10'` | 膝間距離を減少 |

**例:**
```matlab
simulation_type = '_HTD_Plus_5';  % 接地距離を中程度増加
```

---

## トラブルシューティング

### Q1: "CasADi module not found" エラー

**原因:** CasADi MATLAB Toolbox が正しくインストールされていない

**解決策:**
1. CasADi をダウンロードし直す: https://web.casadi.org/get/
2. MATLAB で `addpath(genpath('<CasADi_folder>'))`
3. `savepath` を実行
4. MATLAB を再起動

### Q2: "Unknown external function" エラー

**原因:** DLL ファイルが見つからない、または互換性がない

**解決策:**
```powershell
# DLLをチェック
check_dll_architecture.ps1

# 実行環境が 64-bit MATLAB か確認
matlab -arch win64
```

### Q3: Conda 環境がアクティベートできない

**原因:** Conda が初期化されていない

**解決策:**
```bash
# Conda を初期化
conda init powershell
# または
conda init cmd.exe

# PowerShell/CMD を再起動
```

### Q4: "Permission denied" エラー

**原因:** 管理者権限がない

**解決策:**
- PowerShell を右クリック → **管理者として実行**
- または CMD を右クリック → **管理者として実行**

### Q5: ポリノミアルデータ生成が失敗

**原因:** 必要なファイルが不完全

**解決策:**
```matlab
% 以下の確認
file1 = dir('MainFunctions/ExperimentalData/*.mat');  % 実験データ
file2 = dir('OpenSimModel/*.osim');                   % OpenSimモデル

% ファイルが表示されない場合は、プロジェクト全体が正しくダウンロードされているか確認
```

---

## 環境の再利用・管理

### 環境を再度アクティベート

```bash
conda activate pred_sim_sprinting
```

### 環境を削除（不要な場合）

```bash
conda deactivate
conda env remove --name pred_sim_sprinting
```

### 環境情報を確認

```bash
conda info --envs
conda list -n pred_sim_sprinting
```

### environment.yml を更新

新しいパッケージを追加した場合:

```bash
conda env export > environment.yml
```

---

## 参考資料

- **CasADi 公式ドキュメント:** https://web.casadi.org/
- **MATLAB ドキュメント:** https://jp.mathworks.com/help/matlab/
- **OpenSim ドキュメント:** https://opensim.stanford.edu/

---

## サポート情報

このセットアップに関する問題が発生した場合:

1. 上記の **トラブルシューティング** セクションを確認
2. ログファイルを確認（MATLAB Command History）
3. CasADi 検証: `import casadi.*; casadi.Dae()` を実行

---

**セットアップ完了後、メインシミュレーションの実行準備ができました。**
