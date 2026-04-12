# トラブルシューティングガイド（詳細版）

環境構築から実行まで、各段階で起こりやすい問題と解決方法をまとめました。

---

## 環境構築フェーズ

### 問題 1: PowerShell がスクリプト実行を拒否する

**症状:**
```
.\setup_environment.ps1 : このファイルを読み込むことはできません。
実行ポリシーのため、スクリプト実行が禁止されています。
```

**原因:** PowerShell の実行ポリシーが厳しい設定になっている

**解決方法:**

**方法 A: 一度だけ実行したい場合**
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\setup_environment.ps1
```

**方法 B: 永続的に許可したい場合**
```powershell
# PowerShell を管理者として実行してから：
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup_environment.ps1
```

---

### 問題 2: 「管理者として実行」のダイアログが出ない

**症状:**
```
[ERROR] This script must be run as Administrator!
```

**原因:** PowerShell が通常ユーザーで実行されている

**解決方法:**

1. **Windows キー**を押す
2. **PowerShell** と入力
3. **Windows PowerShell** を**右クリック**
4. **「管理者として実行」**を選択

**確認方法:**
```
管理者: Windows PowerShell  ← 左上にこう表示されている
```

---

### 問題 3: Conda 環境作成が途中で止まる

**症状:**
```
Solving environment: |████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░| 
（20分以上変わらない）
```

**原因:** インターネット接続が遅い、またはパッケージサーバーの問題

**解決方法:**

**方法 A: 待つ（推奨）**
- 30分〜1時間待つ
- コンピューターをスリープモードにしない
- インターネット接続を確認

**方法 B: キャンセルして再試行**
```powershell
# Ctrl + C を押してキャンセル
Ctrl + C

# 環境を削除
conda deactivate
conda env remove -n pred_sim_sprinting

# 再度実行
.\setup_environment.ps1
```

**方法 C: 別のサーバーから試す**
```powershell
# 清华大学の Conda ミラーサーバーを使用
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
conda env create -f environment.yml
```

---

### 問題 4: 「environment.yml ファイルが見つからない」エラー

**症状:**
```
CondaError: environment.yml not found at C:\Users\...
```

**原因:** プロジェクトフォルダが間違っている

**解決方法:**

```powershell
# 現在のフォルダを確認
pwd

# 正しいフォルダか確認
ls *.yml

# environment.yml が見えない場合：
cd "c:\Users\T11648sTb\OneDrive - 国立研究開発法人産業技術総合研究所\ドキュメント\VSCODE\Pred_Sim_Sprinting\Pred_Sim_Sprinting"

# 確認
ls environment.yml
```

---

## MATLAB セットアップフェーズ

### 問題 5: CasADi をダウンロードしたが、どこに解凍するかわからない

**症状:** ZIP ファイルはあるが、解凍後の場所が不明

**解決方法:**

1. `casadi-3.3.0-win64-matlab2014b.zip` を**右クリック**
2. **「すべて展開」**を選択
3. **展開先の選択**ダイアログが出る
4. **わかりやすい場所を選ぶ：**
   - `C:\casadi` （推奨）
   - または `C:\Users\<ユーザー名>\Downloads\casadi`
5. **「展開」**をクリック

**確認方法:**
```
C:\casadi\
├── casadi\  ← このフォルダが見えればOK
│   ├── +casadi\  ← これが重要！
```

**MATLAB で登録する時：**
```matlab
% 上の例なら：
addpath(genpath('C:\casadi'))

% ダウンロードフォルダなら：
addpath(genpath('C:\Users\T11648sTb\Downloads\casadi'))
```

---

### 問題 6: MATLAB で `addpath` 実行後、エラーが出ない

**症状:**
```matlab
>> addpath(genpath('C:\casadi'))
>> savepath
% エラーが出ない
% 大丈夫なのか？
```

**これは正常です！**

MATLAB では、成功時は何も表示されません。

確認方法：
```matlab
>> import casadi.*
>> % エラーが出なければ成功
>> % コマンドプロンプト >> が表示されて待機状態なら OK
```

---

### 問題 7: 「CasADi import failed」エラー

**症状:**
```
TEST 2: CasADi Import
[ERROR] Failed to import CasADi: ...
```

**原因の確認方法:**

```matlab
>> import casadi.*
% エラーメッセージを確認
```

**主なエラーと対処方法:**

| エラー | 対処方法 |
|-------|--------|
| `Invalid MEX-file` | DLL互換性問題。CasADi 64-bit版をダウンロード |
| `Path not found` | フォルダパスが違う。`addpath` を再実行 |
| `Undefined variable casadi` | `import casadi.*` を忘れている |
| `License error` | MATLAB ライセンス問題。ライセンス確認 |

---

### 問題 8: MATLAB が開かない

**症状:**
```
MATLAB が起動しない
またはライセンスエラーが出ている
```

**解決方法:**

1. **MATLAB を完全に終了**
   - タスクバーで MATLAB を右クリック
   - **「ウィンドウを閉じる」**

2. **ライセンスマネージャーをリセット**
   ```
   スタート → MATLAB → MATLAB License Center
   ```

3. **再度起動**

4. **それでも開かない場合：**
   - IT 部門に連絡
   - ライセンス情報を確認

---

## シミュレーション実行フェーズ

### 問題 9: `test_initial_setup` が見つからない

**症状:**
```
未定義の関数または変数 'test_initial_setup' です。
```

**原因:** MATLAB のフォルダが間違っている

**解決方法:**

```matlab
% 現在のフォルダを確認
>> pwd

% 表示例（これが Pred_Sim_Sprinting で終わっていない）:
ans =
    'C:\Users\...\Some Other Folder'

% 正しいフォルダに移動
>> cd "c:\Users\T11648sTb\OneDrive - 国立研究開発法人産業技術総合研究所\ドキュメント\VSCODE\Pred_Sim_Sprinting\Pred_Sim_Sprinting"

% 確認
>> pwd
ans =
    'c:\Users\...\Pred_Sim_Sprinting'

% 再度実行
>> test_initial_setup
```

---

### 問題 10: ポリノミアルデータ生成が途中で止まる

**症状:**
```
Processing muscle 5...
（30分以上変わらない）
```

**原因：** MATLAB が処理中（正常）か、フリーズしている

**確認方法:**

1. **MATLAB が反応するか確認**
   - Command Window をクリック
   - 何か入力してみる

2. **タスクマネージャーで確認**
   - Ctrl + Shift + Esc
   - MATLAB のプロセスを見つける
   - CPU 使用率が 80% 以上か確認

**CPU 使用率が高い場合：** 正常に処理中です。待ってください。

**CPU 使用率が低い場合：** フリーズしている可能性

**対処方法:**

```matlab
% フリーズしている場合：
% Ctrl + C を押してキャンセル

% MATLAB を再起動
% 再度実行
run Polynomials/mainPolynomials.m
```

---

### 問題 11: メインシミュレーション実行中、エラーが出た

**症状:**
```
Error using main_pred_sim_sprinting (line 415)
Undefined function or variable ...
```

**解決方法:**

1. **setup_paths を再度実行**
   ```matlab
   >> setup_paths
   ```

2. **すべてのフォルダが追加されたか確認**
   ```matlab
   >> which main_pred_sim_sprinting
   ans =
       'c:\Users\...\MainFunctions\main_pred_sim_sprinting.m'
   ```

3. **CasADi がインポートされているか確認**
   ```matlab
   >> import casadi.*
   ```

4. **再度実行**
   ```matlab
   >> run MainFunctions/main_pred_sim_sprinting.m
   ```

---

### 問題 12: 最適化が進まない（Iteration が増えない）

**症状:**
```
Iteration 1: Optimality Error = 1.25e+01
Iteration 1: Optimality Error = 1.25e+01  ← 変わらない
Iteration 1: Optimality Error = 1.25e+01
```

**原因：** 最適化が収束していない（または非常に遅い）

**解決方法：**

1. **しばらく待つ** （1-2時間）

2. **それでも進まない場合は中断**
   ```
   Ctrl + C
   ```

3. **シミュレーション条件を変更**
   ```matlab
   % MainFunctions/main_pred_sim_sprinting.m の 28 行目
   simulation_type = '_Nominal';  % 別の値を試す
   simulation_type = '_HTD_Plus_1';  % これなら進む可能性
   ```

4. **再度実行**

---

### 問題 13: 「Out of memory」エラー

**症状:**
```
Error: Out of memory. Type HELP MEMORY for your options.
```

**原因：** MATLAB がメモリを使い尽くした

**解決方法：**

1. **MATLAB を再起動**
   - ウィンドウを閉じる
   - 再度起動

2. **他のアプリケーションを閉じる**
   - Chrome、Word など不要なアプリを終了

3. **再度実行**

4. **それでもダメな場合：**
   - コンピューターを再起動
   - 仮想メモリを増やす（IT 部門に相談）

---

## 結果処理フェーズ

### 問題 14: Python の `post_process_results.py` が実行されない

**症状:**
```
(pred_sim_sprinting) PS C:\...> python post_process_results.py
ModuleNotFoundError: No module named 'pandas'
```

**原因：** Conda 環境がアクティベートされていない、または packages がインストールされていない

**解決方法：**

```powershell
# 環境がアクティベートされているか確認
# (pred_sim_sprinting) ← これが見えているか？

# 見えない場合：
conda activate pred_sim_sprinting

# パッケージが正しくインストールされているか確認
conda list -n pred_sim_sprinting | grep pandas

# インストールされていない場合：
conda install -n pred_sim_sprinting pandas matplotlib numpy scipy

# 再度実行
python post_process_results.py
```

---

### 問題 15: Results フォルダに `.mot` ファイルがない

**症状:**
```
Results フォルダを見てみても、*.mot ファイルがない
```

**原因：** メインシミュレーションが完了していない

**確認方法：**

```matlab
% MATLAB で最後の出力を確認
% もし以下のような表示があれば、シミュレーション中：
% Iteration: 1/100
% Iteration: 2/100

% 以下のような表示があれば完了：
% Solution found!
% Saving results...
```

**対応方法：**

1. シミュレーションが完全に完了するまで待つ
2. MATLAB の Command Window を見て、エラーがないか確認

---

## 一般的なトラブル

### 問題 16: ファイルパスが長すぎるというエラー

**症状:**
```
Error: File path is too long (exceeds 260 characters)
```

**原因：** Windows のパス長制限（260文字）

**解決方法：**

**方法 A: パス短縮（推奨）**
```powershell
# プロジェクトを C ドライブ直下にコピー
# C:\Pred_Sim_Sprinting\  ← ここにコピー
```

**方法 B: Windows設定を変更（管理者権限が必要）**
```powershell
# グループポリシーエディタを開く
gpedit.msc

# コンピューター構成 → 管理用テンプレート → システム → ファイルシステム
# 「長いパスを有効にする」を有効化

# Windows を再起動
```

---

### 問題 17: ネットワークドライブ上で実行しようとしている

**症状:**
```
Error: Cannot write to network drive
```

**原因：** OneDrive などのクラウドストレージ上で実行している

**解決方法：**

1. **プロジェクトをローカルドライブ（C:\）にコピー**
   ```powershell
   robocopy "元のパス" "C:\Pred_Sim_Sprinting" /S /E
   ```

2. **ローカルコピーで実行**

3. **完了後、結果をクラウドにアップロード（オプション）**

---

### 問題 18: 「Permission denied」が頻出

**症状:**
```
Permission denied: ...
```

**原因：** ファイルがロック（他のプログラムで開かれている）

**解決方法：**

1. **Excel で `.csv` ファイルを開いていないか確認**
   - Excel を閉じる

2. **MATLAB を再起動**

3. **再度実行**

---

## 相談が必要な問題

以下の場合は、IT 部門または開発者に相談してください：

1. **MATLAB ライセンスエラー** - ライセンス管理者に連絡
2. **CasADi コンパイルエラー** - C++ コンパイラのインストール
3. **DLL 互換性エラー** - DLL の再コンパイルが必要
4. **ネットワークドライブ** - IT 部門でローカルコピーを推奨

---

## 問題が解決しない場合

### 情報を集める

```matlab
% MATLAB で以下を実行：
version  % MATLAB バージョン
pwd      % 現在フォルダ
import casadi.*  % CasADi 確認
```

```powershell
# PowerShell で以下を実行：
conda info --envs  % Conda 環境一覧
conda list -n pred_sim_sprinting  % インストール済みパッケージ
```

### サポートを受ける際に提供すべき情報

- MATLAB のバージョン（`version` コマンドの出力）
- エラーメッセージ全文（コピー＆ペースト）
- どの段階で失敗したか（環境構築、MATLAB、実行など）
- Windows のバージョン
- Conda バージョン（`conda --version`）

---

**これでほぼすべてのトラブルに対応できます！**
