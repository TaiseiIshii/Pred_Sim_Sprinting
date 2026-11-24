# Pred_Sim_Sprinting – Python/CasADi (MATLABなし)

MATLABを使わずにCasADi Python APIで走行最適制御シミュレーションを実行するための  
ポート実装です。元のリポジトリ `Pred_Sim_Sprinting/` が必要です。

---

## 要件

| ツール | バージョン | 備考 |
|--------|-----------|------|
| Python | 3.11+ | |
| [uv](https://docs.astral.sh/uv/) | 最新 | パッケージ管理 |
| CasADi | 3.6+ | 自動微分・最適化 |
| IPOPT | (CasADiに同梱) | 内点法ソルバー |

### オプション依存関係

| パッケージ | 用途 |
|-----------|------|
| `opensim` (condaチャネル) | 筋肉特性を精密に読み込む場合。なければXML fallbackを使用 |

---

## セットアップ手順

```bash
# 1. uvをインストール (未インストールの場合)
pip install uv

# 2. このディレクトリに移動
cd path/to/Pred_Sim_Sprinting/python

# 3. 仮想環境の作成と依存関係のインストール
uv sync
```

---

## 実行方法

```bash
cd python

# 標準シミュレーション
uv run pred-sim

# シミュレーションタイプの指定
uv run pred-sim --sim-type _HTD_Plus_6

# 前回の解を初期値として使用 (warm start)
uv run pred-sim --sim-type _Nominal --prev-sol ../Results/previous_result.mat

# ヘルプ
uv run pred-sim --help
```

### 利用可能な `--sim-type` 値

| タイプ | 説明 |
|-------|------|
| `_Nominal` | 標準 |
| `_HTD_Plus_N` (N=1..10) | 水平着地距離 +N cm |
| `_HTD_Minus_N` (N=1..10) | 水平着地距離 -N cm |
| `_IKTD_Plus_N` (N=1..10) | 膝間着地距離 +N cm |
| `_IKTD_Minus_N` (N=1..10) | 膝間着地距離 -N cm |

---

## ファイル構成

```
python/
├── pyproject.toml                     # uv プロジェクト設定
├── README.md                          # このファイル
└── src/pred_sim_sprinting/
    ├── __init__.py
    ├── main.py                        # エントリポイント
    ├── collocation.py                 # 直接コロケーション補間多項式
    ├── muscle_model.py                # Hill型筋モデル
    ├── polynomials.py                 # 筋・腱長多項式近似
    ├── casadi_functions.py            # CasADiシンボリック関数
    ├── nlp_builder.py                 # NLP定式化
    ├── bounds_scaling.py              # 境界値・スケーリング・初期推定
    ├── joint_muscle_indices.py        # 関節・筋インデックス定義
    └── io_utils.py                    # ファイル入出力ユーティリティ
```

---

## 元のMATLABコードとの対応

| Python ファイル | MATLAB 関数 |
|----------------|------------|
| `main.py` | `main_pred_sim_sprinting.m` (メインスクリプト) |
| `collocation.py` | `CollocationScheme.m` |
| `muscle_model.py` | `ForceEquilibrium_FtildeState_all_tendon_M.m` |
| `polynomials.py` | `n_art_mat_3_cas_SX.m` |
| `nlp_builder.py` | `buildNLP()` (サブ関数) |
| `bounds_scaling.py` | `createScaledBounds()`, `createGuess()`, `calcObjRange()` |
| `io_utils.py` | `readMOT.m`, `extractMuscProperties.m` |

---

## 既知の制限事項

1. **外部DLL** (`Spr_Imp_GRFs_ownCont_V21.dll`) – 元のWindowsバイナリが必要です。  
   CasADiの `external()` 関数でロードします。LinuxではDLLを再コンパイルしてください。

2. **OpenSimモデル** – `.osim` ファイルは `OpenSimModel/` フォルダに必要です。  
   `opensim` Pythonパッケージがない場合はXML直接パースにフォールバックします。

3. **実験データ** – `MainFunctions/ExperimentalData/IK_Splined/p02_maxVel_01.mot` が必要です。

---

## 依存関係のアップデート

```bash
cd python
uv add <package_name>      # 依存関係を追加
uv remove <package_name>   # 依存関係を削除
uv lock --upgrade          # lockファイルを最新バージョンで更新
```
