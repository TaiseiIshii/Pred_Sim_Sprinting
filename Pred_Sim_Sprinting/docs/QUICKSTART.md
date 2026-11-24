# Pred_Sim_Sprinting - 初学者向けセットアップガイド（修正版）

**完全ステップバイステップ実装手順（初心者向け）**

このガイドは、プログラミング初心者でもわかるように、各ステップを詳しく説明しています。

---

## 必要な前提条件

セットアップを始める前に、以下を確認してください：

- ✅ **MATLAB 2017b (64-bit)** がインストール済み
- ✅ **Conda/Miniconda** がインストール済み  
- ✅ Windows 10/11 (64-bit)
- ✅ インターネット接続

---

## Step 1: Conda環境を作成（5〜10分）

### 1.1 PowerShell を管理者として起動

1. キーボードの **Windows キー** を押す
2. **「PowerShell」**と入力
3. **「Windows PowerShell」** を**右クリック**
4. **「管理者として実行」**を選択

### 1.2 プロジェクトフォルダに移動

PowerShell で以下を実行：

```powershell
cd "c:\Users\T11648sTb\OneDrive - 国立研究開発法人産業技術総合研究所\ドキュメント\VSCODE\Pred_Sim_Sprinting\Pred_Sim_Sprinting"
```

### 1.3 自動セットアップを実行

```powershell
.\setup_environment.ps1
```

**完了時に表示される内容：**
```
[OK] All core packages imported successfully
[OK] All DLLs are 64-bit compatible!
Setup Complete!
```

---

## Step 2: CasADi MATLAB Toolbox をインストール（10分）

### 2.1 CasADi をダウンロード

1. https://web.casadi.org/get/ にアクセス
2. **「MATLAB Toolbox」** セクションで **CasADi 3.3.0** 以上をダウンロード
3. ZIP ファイルを **`C:\casadi`** に解凍

### 2.2 MATLAB で登録

MATLAB R2017b を起動して、Command Window に以下を入力：

```matlab
addpath(genpath('C:\casadi'))
savepath
import casadi.*
```

各行で **Enter** を押す

**成功時：** エラーが出ず、`>>` が表示されます

---

## Step 2.5: OpenSim MATLAB インターフェースをインストール（15分）

**重要：このステップを完了しないと、シミュレーションは実行できません**

### 2.5.1 OpenSim 4.4+ をダウンロード・インストール

1. https://opensim.stanford.edu/download-and-install-opensim/ にアクセス
2. **OpenSim 4.4 以上**をダウンロード
3. インストーラーを実行（デフォルト設定で OK）
   - インストール先はデフォルト：`C:\OpenSim` または `C:\Program Files\OpenSim`

### 2.5.2 MATLAB で OpenSim を登録

**重要：OpenSim 4.2/4.5 は Java インターフェースで動作します**

#### (A) Java ライブラリパスを永続登録（必須）

MATLAB で以下を実行して **prefdir** を確認：

```matlab
prefdir
```

表示されたフォルダに **javalibrarypath.txt** を作成し、
1 行だけ以下を記載：

```
C:\OpenSim 4.2\bin
```

（OpenSim 4.5 を使う場合は `C:\OpenSim 4.5\bin` に変更）

#### (B) Java クラスパスの登録

同じフォルダに **javaclasspath.txt** を作成し、
1 行だけ以下を記載：

```
C:\OpenSim 4.2\sdk\Java\org-opensim-modeling.jar
```

（OpenSim 4.5 を使う場合は `C:\OpenSim 4.5\sdk\Java\org-opensim-modeling.jar` に変更）

#### (C) MATLAB を再起動

**必ず MATLAB を完全終了 → 再起動**してください。

#### インストール先の確認

OpenSimがどこにインストールされているか確認：

**PowerShellで確認：**
```powershell
Get-ChildItem "C:\OpenSim*\sdk" -Directory | Select-Object Parent, Name
```

**結果例：**
```
Parent              Name
------              ----
C:\OpenSim 4.2      sdk
C:\OpenSim 4.5      sdk
```

### 2.5.3 OpenSim が正しく登録されたか確認

MATLAB で以下を入力：

```matlab
import org.opensim.modeling.*
help Model
```

必要なら `java.library.path` を確認：

```matlab
char(java.lang.System.getProperty('java.library.path'))
```

**成功時：** 文字列内に `C:\OpenSim 4.2\bin`（または 4.5）を含む

**成功時：** `Model` クラスのヘルプが表示される

**失敗時の例：**
```
未定義の関数または変数 'Model'
```
→ インストール先とパスを再度確認してください

---

## Step 3: 環境テスト（5分）

MATLAB で以下を実行：

```matlab
cd "c:\Users\T11648sTb\OneDrive - 国立研究開発法人産業技術総合研究所\ドキュメント\VSCODE\Pred_Sim_Sprinting\Pred_Sim_Sprinting"
run quicktest.m
```

**前提条件：** 
- Step 2 (CasADi) が完了している
- Step 2.5 (OpenSim) が完了している

**成功時の表示：**
```
[OK] All required folders are present

Next Steps:
1. CasADi をインストール（✓ 完了）
2. OpenSim をインストール（✓ 完了）
3. run Polynomials/mainPolynomials.m を実行
4. run MainFunctions/main_pred_sim_sprinting.m を実行
```

---

## Step 4: ポリノミアルデータ準備（5分、1回のみ）

MATLAB で以下を実行：

```matlab
cd "c:\Users\T11648sTb\OneDrive - 国立研究開発法人産業技術総合研究所\ドキュメント\VSCODE\Pred_Sim_Sprinting\Pred_Sim_Sprinting\Polynomials"
run mainPolynomials.m
```

**実行内容：**
- プリセットの筋肉モデルデータを読み込む
- CasADi シンボリック関数を生成
- 多項式フィッティングの精度をテスト

**完了：** `>>` が表示される（通常 2〜3 分）

**期待される出力の最後：**
```
[OK] Polynomial setup completed successfully!

========================================
Setup Complete!
========================================
Ready to run main simulation.
Next: run MainFunctions/main_pred_sim_sprinting.m
```

---

## Step 5: メインシミュレーション（20〜40分）

MATLAB で以下を実行（キーボードを触らずに待つ）：

```matlab
cd "c:\Users\T11648sTb\OneDrive - 国立研究開発法人産業技術総合研究所\ドキュメント\VSCODE\Pred_Sim_Sprinting\Pred_Sim_Sprinting\MainFunctions"
main_pred_sim_sprinting
```

**実行内容：**
- スプリント走動作の最適化計算が実行される
- 最適化ループが反復される
- 結果がファイルに保存される

**完了：** `>>` が表示される（通常 20〜40 分）

**期待される出力の最後：**
```
Saving results...
Results saved to: c:\Users\...\Results\pred_sprinting_YYYY_MM_DD__HH_MM_SS__Nominal_GRF.mot
```

**注：** 初期条件ファイルが存在しない場合、初期値から計算を開始します（実行時間が長くなる可能性があります）

---

## Step 6: 結果を CSV・グラフ化（オプション、3分）

PowerShell で以下を実行：

```powershell
conda activate pred_sim_sprinting
cd "c:\Users\T11648sTb\OneDrive - 国立研究開発法人産業技術総合研究所\ドキュメント\VSCODE\Pred_Sim_Sprinting\Pred_Sim_Sprinting"
python post_process_results.py
```

**完了：**
```
Post-processing completed!
```

---

## 別の条件でシミュレーション

`MainFunctions/main_pred_sim_sprinting.m` の 28行目：

```matlab
simulation_type = '_Nominal';  % ← これを変更
```

選択肢：
```
'_Nominal'              基準条件
'_HTD_Plus_1'～10       水平接地距離 増加
'_HTD_Minus_1'～10      水平接地距離 減少
'_IKTD_Plus_1'～10      膝間接地距離 増加
'_IKTD_Minus_1'～10     膝間接地距離 減少
```

---

## エラーが出た場合

| エラー | 対処方法 |
|-------|--------|
| **PowerShell 実行エラー** | PowerShell を「管理者として実行」 |
| **CasADi import failed** | Step 2 の CasADi インストール確認 |
| **OpenSim Model 未定義** | Step 2.5 の OpenSim インストール確認 |
| **File not found** | Step 3 で`pwd`コマンドを実行して確認 |
| **Permission denied** | 管理者として実行 |
| **DLL読み込みエラー（Compressed Column Storage）** | 下記を参照 |

### OpenSim Model エラーの対処

**症状:**
```
関数または変数 'Model' が未定義です
エラー: extractMuscProperties (line 13)
    model = Model(modelName);
```

**原因：** OpenSim MATLAB インターフェースが正しくインストール/登録されていない

**解決方法：**
1. OpenSim 4.4+ がインストール済みか確認
2. Step 2.5 を再度実行（`addpath` と `savepath`）
3. MATLAB を再起動してから `import org.opensim.modeling.*` を実行
4. `help Model` でヘルプが表示されるか確認

詳細は **TROUBLESHOOTING_GUIDE.md** を参照

### DLL読み込みエラーの対処

**症状:**
```
Error calling External::init for 'F_cont_v21'
Compressed Column Storage is not sane
```

**原因：** CasADi 3.3.0 とDLLファイルの互換性問題

**解決方法：**
1. CasADiのバージョンを確認
   ```matlab
   casadi.CasADi.version()
   ```

2. CasADi 3.5.0 以上をダウンロード（より新しいバージョン）
   - https://web.casadi.org/get/
   - Step 2 を再度実行してアップデート

3. MATLAB を再起動してから Step 5 を再度実行

詳細は **TROUBLESHOOTING_GUIDE.md** を参照

---

## 環境を再利用（次回）

```matlab
% MATLAB
cd "プロジェクトルート"
run setup_paths.m
run MainFunctions/main_pred_sim_sprinting.m
```

```powershell
# Python後処理
conda activate pred_sim_sprinting
python post_process_results.py
```

---

**成功を祈ります！🎉**

**完全ステップバイステップ実装手順（初心者向け）**

このガイドは、プログラミング初心者でもわかるように、各ステップを詳しく説明しています。

---

## 事前確認：必要なものをすべてインストール済みか確認

セットアップを始める前に、以下がインストール済みか確認してください：

### ✅ MATLAB 2017b がインストール済みか確認

1. **Windows スタートメニュー**を開く
2. **「MATLAB」**と検索
3. **「MATLAB R2017b」**が見つかるか確認

**見つかった場合:** OKです。Step 1 に進んでください。

**見つからない場合:**
- MATLAB をインストールする必要があります
- ライセンス情報については、組織内のIT部門に確認してください

### ✅ Conda（Miniconda または Anaconda）がインストール済みか確認

1. **PowerShell** または **コマンドプロンプト**を開く
   - キーボードの Windows キー + R を押す
   - `powershell` と入力して Enter

2. 以下のコマンドを入力
   ```
   conda --version
   ```

3. 結果を確認
   - **出力例:** `conda 4.10.3` ← **OK です！**
   - **エラーメッセージ:** `conda: コマンドが見つかりません` ← Conda をインストール必要

**Conda がない場合の対応:**
- Miniconda をダウンロード: https://docs.conda.io/en/latest/miniconda.html
- インストーラーを実行（デフォルト設定で OK）

---

## Step 1: Conda環境を作成（初回：5〜10分）

### 1.1 PowerShell を管理者として起動

**具体的な手順:**

1. キーボードの **Windows キー** を押す
2. **「PowerShell」**と入力
3. **「Windows PowerShell」**が出てくる
4. **右クリック**して **「管理者として実行」**を選択

**画面イメージ:**
```
PowerShell が立ち上がり、以下の表示が見えます：
PS C:\Users\ユーザー名>
```

### 1.2 プロジェクトフォルダに移動

PowerShell で以下を実行（コピー＆ペーストで OK）：

```powershell
cd "c:\Users\T11648sTb\OneDrive - 国立研究開発法人産業技術総合研究所\ドキュメント\VSCODE\Pred_Sim_Sprinting\Pred_Sim_Sprinting"
```

**実行後の表示例:**
```
PS C:\Users\T11648sTb\OneDrive - 国立研究開発法人産業技術総合研究所\ドキュメント\VSCODE\Pred_Sim_Sprinting\Pred_Sim_Sprinting>
```

### 1.3 自動セットアップスクリプトを実行

PowerShell で以下を実行：

```powershell
.\setup_environment.ps1
```

**実行内容：**
- Conda 環境 `pred_sim_sprinting` が作成される
- NumPy、Pandas、Matplotlib などが自動インストールされる
- DLL ファイルが 64-bit 対応か自動チェック

**時間目安：** 5〜10分（インターネット速度に依存）

**画面表示例：**
```
========================================
Pred_Sim_Sprinting Automated Setup
========================================

Checking Conda installation...
[OK] conda 4.10.3

Creating Conda environment...
Solving environment: done
...
[OK] Environment created successfully
```

**完了した場合：** 「Setup Complete!」という表示が出て、次のステップが表示されます

**エラーが出た場合：** 
- `Permission denied` → PowerShell を「管理者として実行」し直してください
- `conda: コマンドが見つかりません` → Conda のインストールを確認してください

---

## Step 2: CasADi MATLAB Toolbox をダウンロード＆インストール（10分）

### 2.1 CasADi をダウンロード

**具体的な手順：**

1. ウェブブラウザで以下のサイトを開く：
   ```
   https://web.casadi.org/get/
   ```

2. ページを下にスクロール

3. **「MATLAB Toolbox」**セクションを探す
   - 「Get CasADi」という青いボタンがあります

4. **CasADi 3.3.0**（または 3.5.0+）を見つけて**ダウンロード**
   - ファイル名例：`casadi-3.3.0-win64-matlab2014b.zip`

5. **ダウンロードフォルダに保存**

**画面イメージ:**
```
[MATLAB Toolbox]
CasADi 3.3.0 ← これを探す
┣ casadi-3.3.0-win64-matlab2014b.zip  [Download]
```

### 2.2 ダウンロードしたファイルを解凍

**具体的な手順：**

1. **ダウンロードフォルダ**を開く
2. `casadi-3.3.0-win64-matlab2014b.zip` を見つける
3. **右クリック** → **「すべて展開」**を選択
4. 展開先を選択（わかりやすい場所、例：`C:\casadi`）
5. **「展開」**をクリック

**解凍後の表示例：**
```
C:\casadi\
├── casadi\  （フォルダ）
│   ├── +casadi\  （重要！このフォルダが必要）
│   └── examples\
└── LICENSE
```

### 2.3 MATLAB で CasADi を登録

**具体的な手順：**

1. **MATLAB R2017b を起動**
   - Windows スタートメニュー → MATLAB R2017b をクリック

2. **MATLAB が起動**して、「Command Window」が表示されるのを待つ

3. **Command Window** に以下を入力（大文字小文字を区別します）：

```matlab
addpath(genpath('C:\casadi'))
```

**重要：** `C:\casadi` は Step 2.2 で解凍したフォルダパスに置き換えてください

4. **Enter キー**を押す

**実行例：**
```matlab
>> addpath(genpath('C:\casadi'))
```

5. 次に以下を入力：

```matlab
savepath
```

6. **Enter キー**を押す

**実行後の表示例：**
```
Path saved to C:\Users\<ユーザー名>\AppData\Roaming\MathWorks\MATLAB\R2017b\pathdef.m
```

7. 最後に CasADi がインポートできるか確認：

```matlab
import casadi.*
```

8. **Enter キー**を押す

**成功時：** 何も表示されず、新しいコマンドプロンプト `>>` が表示されます

**失敗時の例：**
```
警告: ディレクトリ C:\casadi が見つかりません
```
→ フォルダパスが正しいか確認してください

---

## Step 3: MATLAB で環境をテストする（5分）

### 3.1 プロジェクトフォルダを MATLAB で開く

**具体的な手順：**

MATLAB の Command Window に以下を入力：

```matlab
cd "c:\Users\T11648sTb\OneDrive - 国立研究開発法人産業技術総合研究所\ドキュメント\VSCODE\Pred_Sim_Sprinting\Pred_Sim_Sprinting"
```

**Enter キー**を押す

**実行後の表示例：**
```matlab
>> cd "c:\Users\..."
>> （カーソルがここに移動）
```

### 3.2 パスを確認

MATLAB で以下を入力：

```matlab
pwd
```

**Enter キー**を押す

**期待される出力：**
```
ans =
    'c:\Users\T11648sTb\OneDrive - 国立研究開発法人産業技術総合研究所\ドキュメント\VSCODE\Pred_Sim_Sprinting\Pred_Sim_Sprinting'
```

### 3.3 セットアップテストを実行

MATLAB で以下を入力：

```matlab
run quicktest.m
```

**Enter キー**を押す

**実行時間：** 30秒〜1分

**期待される出力：**
```
Project Root: c:\Users\...\Pred_Sim_Sprinting

TEST 1: Path Setup
----------------------------------------
[OK] Added: c:\Users\...\MainFunctions
[OK] Added: c:\Users\...\ExternalFunctions
[OK] Path setup successful

TEST 2: CasADi Import
----------------------------------------
[OK] CasADi imported successfully

TEST 3: Required Folders
----------------------------------------
[OK] MainFunctions
[OK] ExternalFunctions
[OK] MuscleModel
[OK] Polynomials
[OK] OpenSimModel
[OK] Results

TEST 4: External DLL Files
----------------------------------------
[OK] Found 16 DLL file(s)

========================================
Setup Test Completed!
========================================

[OK] All required folders are present

Next Steps:
1. CasADi をインストール（https://web.casadi.org/get/）
2. run setup_paths を実行
3. run Polynomials/mainPolynomials.m を実行
4. run MainFunctions/main_pred_sim_sprinting.m を実行
```

**エラーが出た場合：**

| エラーメッセージ | 対処方法 |
|---|---|
| `Undefined function or variable 'quicktest'` | Step 3.1 でフォルダ移動が失敗しています。`pwd` で確認 |
| `CasADi import failed` | Step 2 の CasADi インストールを確認 |
| `Missing folder: Polynomials` | フォルダが欠落しています（正常ではありません） |

---

**実行時間：** 30秒〜1分

**期待される出力：**
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
...
```

**エラーが出た場合：**

| エラーメッセージ | 対処方法 |
|---|---|
| `Undefined function or variable 'test_initial_setup'` | Step 3.1 でフォルダ移動が失敗しています。`pwd` で確認 |
| `CasADi import failed` | Step 2 の CasADi インストールを確認 |
| `Missing folder: Polynomials` | フォルダが欠落しています（正常ではありません） |

---

## Step 4: ポリノミアルデータを生成（初回のみ、10〜20分）

### 重要：この作業は初回のみ必要です

MATLAB の Command Window で以下を実行：

```matlab
setup_paths
```

**Enter キー**を押す

**実行後の表示例：**
```matlab
========================================
Pred_Sim_Sprinting Path Setup
========================================

Project Root: c:\Users\...

[OK] Added: c:\Users\...\MainFunctions
[OK] Added: c:\Users\...\ExternalFunctions
...
[OK] CasADi imported successfully
```

次に、ポリノミアルデータを生成します：

```matlab
run Polynomials/mainPolynomials.m
```

**Enter キー**を押す

**実行内容：**
- 筋肉モデルの最適化多項式が計算される
- データがキャッシュファイルに保存される

**実行時間：** 10〜20分（PCのスペックによる）

**実行中の表示例：**
```
Running polynomial fitting...
Fitting polynomial for muscle 1...
Fitting polynomial for muscle 2...
...
Saving data files...
[OK] Polynomial generation completed
```

### この間、何もしないでください
- スクリプトが自動で進みます
- エラーメッセージが出なければ大丈夫です
- キーボードを触らないでください

**完了の合図：** Command Window に `>>` が表示されたら完了です

---

## Step 5: メインシミュレーションを実行（初回：20〜40分）

### 5.1 シミュレーション設定の確認

MATLAB で以下を実行：

```matlab
setup_paths
```

**Enter キー**を押す

### 5.2 メインシミュレーションを実行

MATLAB で以下を入力：

```matlab
run MainFunctions/main_pred_sim_sprinting.m
```

**Enter キー**を押す

**実行内容：**
- スプリント走動作の最適化計算が実行される
- 最適化ループが反復される
- 結果がファイルに保存される

**実行時間：** 20〜40分（PCのスペック・最適化の複雑さによる）

**実行中の表示例：**
```
NLP Solver Starting
========================================
Iteration: 1/100
Optimality Error: 1.2e-1
...
Iteration: 50/100
Optimality Error: 3.2e-3
...
Solution found!
Saving results...
```

### この間、何もしないでください
- スクリプトが自動で進みます
- 「Iteration」が増えていれば正常です
- キーボードを触らないでください

**完了の合図：** 
```
Saving results...
Results saved to: c:\Users\...\Results\pred_sprinting_YYYY_MM_DD__HH_MM_SS__Nominal_GRF.mot
```
という表示が出たら完了です

### 5.3 結果ファイルを確認

結果ファイルが作成されているか確認します：

MATLAB で以下を実行：

```matlab
ls Results/*.mot
```

**Enter キー**を押す

**期待される出力：**
```
pred_sprinting_2026-02-03__10-30-45__Nominal_GRF.mot
pred_sprinting_2026-02-03__10-30-45__Nominal_GRF_Single.mot
```

**出力されない場合：** Step 5.2 が正常に完了していない可能性があります

---

## Step 6: 結果を CSV とグラフに変換（オプション、3分）

### 6.1 Conda 環境をアクティベート

**PowerShell** または **コマンドプロンプト**を開いて：

```powershell
conda activate pred_sim_sprinting
```

**Enter キー**を押す

**実行後の表示例：**
```
(base) PS C:\Users\...>  ← これが
(pred_sim_sprinting) PS C:\Users\...>  ← こうなります
```

### 6.2 プロジェクトフォルダに移動

```powershell
cd "c:\Users\T11648sTb\OneDrive - 国立研究開発法人産業技術総合研究所\ドキュメント\VSCODE\Pred_Sim_Sprinting\Pred_Sim_Sprinting"
```

**Enter キー**を押す

### 6.3 結果処理スクリプトを実行

```powershell
python post_process_results.py
```

**Enter キー**を押す

**実行内容：**
- .mot ファイルが .csv に変換される
- グラフ画像が生成される

**実行時間：** 1〜3分

**実行後の表示例：**
```
==================================================
Pred_Sim_Sprinting Post-Processing Tool
==================================================

Results directory: c:\Users\...\Results

Processing: pred_sprinting_2026-02-03__10-30-45__Nominal_GRF.mot
[OK] Loaded pred_sprinting_2026-02-03__10-30-45__Nominal_GRF.mot
[OK] Exported to ...\Results\pred_sprinting_2026-02-03__10-30-45__Nominal_GRF.csv
```

**完了の合図：** 
```
Post-processing completed!
```

### 6.4 結果ファイルを確認

Results フォルダを開いて、以下のファイルが作成されたか確認：

```
Results/
├── pred_sprinting_YYYY_MM_DD__HH_MM_SS__Nominal_GRF.mot    （元のファイル）
├── pred_sprinting_YYYY_MM_DD__HH_MM_SS__Nominal_GRF.csv    （Excel で開ける）
├── plots/
│   ├── pred_sprinting_YYYY_MM_DD__HH_MM_SS__Nominal_GRF_plot.png
│   └── ... （その他のグラフ）
```

---

## 別の条件でシミュレーションを実行する方法

同じシミュレーションを、異なるパラメータで実行できます：

### 手順：

1. **MATLAB で以下を開く：**
   - VS Code で `MainFunctions/main_pred_sim_sprinting.m` をテキストエディタで開く
   - または、MATLAB のエディタで直接開く

2. **28行目付近の以下の部分を探す：**

```matlab
simulation_type = '_Nominal';
```

3. **`'_Nominal'` の部分を別の条件に変更：**

```matlab
% 例1: 水平接地距離を増やす
simulation_type = '_HTD_Plus_5';

% 例2: 膝間接地距離を減らす
simulation_type = '_IKTD_Minus_3';
```

4. **ファイルを保存**（Ctrl + S）

5. **MATLAB で実行：**

```matlab
run MainFunctions/main_pred_sim_sprinting.m
```

### 選択可能な条件：

```
'_Nominal'              基準条件（デフォルト）
'_HTD_Plus_1'           水平接地距離 少し増加
'_HTD_Plus_10'          水平接地距離 最大増加
'_HTD_Minus_1'          水平接地距離 少し減少
'_HTD_Minus_10'         水平接地距離 最大減少
'_IKTD_Plus_1'          膝間接地距離 少し増加
'_IKTD_Plus_10'         膝間接地距離 最大増加
'_IKTD_Minus_1'         膝間接地距離 少し減少
'_IKTD_Minus_10'        膝間接地距離 最大減少
```

---

## トラブルシューティング

### 症状: 「Unknown function or variable 'CasADi'」エラー

**原因：** CasADi が正しくインストール/登録されていない

**解決手順：**
1. MATLAB を再起動
2. Step 2.3 を再度実行（`addpath` と `savepath`）
3. MATLAB を再起動してから、`import casadi.*` を実行

### 症状: 「Permission denied」エラー

**原因：** 管理者権限がない

**解決手順：**
1. PowerShell を右クリック
2. **「管理者として実行」**を選択
3. Step 1 を再度実行

### 症状: ポリノミアル生成が途中で止まる

**原因：** ファイルが破損しているか、メモリ不足

**解決手順：**
1. MATLAB を再起動
2. Step 4 を再度実行
3. 数時間待つ（コンピューターは動作中です）

### 症状: 「File not found」エラー

**原因：** プロジェクトフォルダが正しく指定されていない

**解決手順：**
1. MATLAB で `pwd` を実行
2. 表示されたフォルダが `Pred_Sim_Sprinting` で終わるか確認
3. 違う場合は、Step 3.1 の `cd` コマンドを再度実行

---

## よくある質問

### Q: 実行が遅い気がするのですが…

**A:** 最適化計算は複雑なため、時間がかかります。これは正常です。
- 初回：20〜40分
- 以降（同じパラメータ）：キャッシュを使用するので短くなる可能性あり

### Q: エラーが出たらどうすればいい？

**A:** 以下の手順を試してください：
1. エラーメッセージをしっかり読む
2. 上記のトラブルシューティングセクションを確認
3. 関連する Step を再度実行

### Q: 結果ファイルはどこに保存される？

**A:** `Results/` フォルダに以下の形式で保存されます：
```
pred_sprinting_YYYY_MM_DD__HH_MM_SS__Nominal_GRF.mot
```

### Q: 別のパラメータで複数回実行してもいい？

**A:** はい、何度でも実行できます。
- 毎回新しい結果ファイルが作成されます
- 古い結果は上書きされません

---

## 環境の再利用（次回以降）

新しいセッションでシミュレーションを実行する場合：

### MATLAB の場合：
```matlab
cd "プロジェクトフォルダ"
setup_paths
run MainFunctions/main_pred_sim_sprinting.m
```

### Python（後処理）の場合：
```powershell
conda activate pred_sim_sprinting
cd "プロジェクトフォルダ"
python post_process_results.py
```

### 環境を削除する場合：
```powershell
conda deactivate
conda env remove -n pred_sim_sprinting
```

---

**これでセットアップ完了です！わかりにくい点があれば、各ステップを再度実行してください。**

