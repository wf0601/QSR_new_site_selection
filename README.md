[🇯🇵 日本語](README.md) | [🇬🇧 English](README_EN.md)

# Geo-Intelligence 意思決定システム（Demo）

TabelogやGoogleMap等のクローリング可能なデータソースからレストランデータを収集し、HDBSCANで東京の飲食需要ゾーン(Demand Zone)をクラスタリングして、マクドナルド(仮名)の新規出店候補地をスコアリングするデータパイプライン。

![インタラクティブマップ プレビュー](assets/thumbnail.png)

---

## 仕組み

```
スクレイピング → 需要クラスタリング（HDBSCAN）→ 候補地スコアリング → インタラクティブマップ
```

1. **スクレイピング** — マクドナルドおよび競合チェーンの位置情報・レビュー数を収集
2. **クラスタリング** — 全レストランをレビュー数で重み付けしてHDBSCANを実行し、飲食需要ゾーンを発見
3. **スコアリング** — クラスター需要・マクドナルド空白度・距離バッファの3指標で候補地をランキング
4. **選定** — 貪欲法NMS（最小間隔1.5km）で地理的に分散した上位50候補を選出
5. **出力** — インタラクティブFoliumマップ＋ランキングCSV

---

## プロジェクト構成

```
├── assets/
│   └── thumbnail.png                  # マップのプレビュー画像
│
├── output/
│   ├── interactive_map.html           # 自己完結型インタラクティブマップ（メイン成果物）
│   └── top_candidates.csv            # 候補地ランキング
│
├── scraper.py                         # Tabelogスクレイパー＋共通スクレイピングループ
├── scrape_location.py                 # 単一ブランド・区のスクレイプユーティリティ
├── scrape_tokyo_burger_chains.py      # バーガー競合チェーンのスクレイプ
├── scrape_tokyo_teishoku_chains.py    # 定食競合チェーンのスクレイプ
├── scrape_tokyo_family_chains.py      # ファミレス競合チェーンのスクレイプ
│
├── config.py                          # スクレイピング設定（チェーン・区・エイリアス）
├── config_modeling.py                 # モデリングパラメータ一覧
├── spatial_features.py                # BallTreeヘルパー（ハーバーサイン距離）
│
├── site_selection.py                  # フルパイプライン：クラスタリング → スコアリング → CSV出力
├── app_interactive.py                 # ライブコントロール付きインタラクティブHTMLマップ
│
└── requirements.txt
```

---

## セットアップ

```bash
pip install -r requirements.txt
```

---

## 使い方

### 1 — データの収集

各スクリプトは`data/`にデータが存在しないチェーンのみスクレイピングします。既存ブランドはキャッシュから自動読み込みされます。

```bash
python scrape_tokyo_burger_chains.py
python scrape_tokyo_teishoku_chains.py
python scrape_tokyo_family_chains.py
```

新しいチェーンを追加する場合は、`config.py`の該当する`DEFAULT_*_CHAINS`リストにスラグを追加し（必要に応じて`BRAND_ALIASES`にエイリアスも追加）、スクリプトを再実行してください。

### 2 — 候補地選定の実行

```bash
python site_selection.py     # output/top_candidates.csv を出力
python app_interactive.py    # output/interactive_map.html を出力
```

---

## インタラクティブマップ

`output/interactive_map.html` は完全自己完結型 — サーバー不要、任意のブラウザで開くだけで使用可能。実装の時、Dockerの使用をおすすめ。

**コントロール（右上レイヤーパネル）**
- **バーガー / 定食 / ファミレス ウェイト** — 各競合カテゴリが需要スコアに与える影響を調整（`0` = 無視、`1.0` = デフォルト、`2.0` = 2倍の影響）

**コントロール（右下パネル）**
- **スパースエリア信頼度** — HDBSCANノイズ再割り当て候補のメンバーシップウェイト（`0` = 非表示、`0.5` = デフォルト、`1` = 確定クラスターと同等）
- **表示候補数** — ランキング上位5〜50件を表示（デフォルト50件）

**マップ要素**
- 緑バッジ — 確定需要クラスターからの候補地
- 橙バッジ — 潜在需要のあるスパースエリアからの候補地
- 赤 **M** バッジ — 既存マクドナルド店舗
- バッジの数字 = ランク　・　透明度 = スコア

---

## 競合カテゴリ

| カテゴリ | チェーン | ウェイト |
|---|---|---|
| バーガー（直接競合） | モスバーガー、KFC、ウェンディーズ | 1.0 |
| 定食（間接競合） | 松屋、吉野家、すき家、なか卯、大戸屋 | 0.5 |
| ファミレス（間接競合） | ガスト、サイゼリヤ | 0.3 |

---

## スコアリング計算式

```
base_score  = 0.40 × cluster_demand + 0.40 × mcd_gap + 0.20 × distance_buffer
final_score = base_score × membership_strength   （[0, 1]に正規化）
```

| コンポーネント | 説明 |
|---|---|
| `cluster_demand` | 候補地が属する需要ゾーンのレビュー加重需要の合計 |
| `mcd_gap` | そのゾーンにおけるマクドナルド以外のレストランの割合 |
| `distance_buffer` | 既存店舗からの安全距離（最大2km） |
| `membership_strength` | HDBSCANのソフトクラスター信頼度（スパースエリアで調整可能） |

---

## 主要パラメータ（`config_modeling.py`）

| パラメータ | デフォルト | 効果 |
|---|---|---|
| `HDBSCAN_PARAMS.min_cluster_size` | 15 | 需要クラスターを形成するための最小レストラン数 |
| `MIN_DIST_TO_OWN_KM` | 0.8 km | カニバリゼーション防止ガード |
| `MAX_DIST_TO_COMP_KM` | 3.0 km | 何らかの市場活動の近辺であること |
| `MIN_SPREAD_KM` | 1.5 km | 選定候補地間の最小距離 |
| `TOP_N_SITES` | 50 | 出力する候補地数 |
| `GRID_STEP_DEG` | 0.003°（約330m） | 候補グリッドの解像度 |

## Contact
Please mail me if you have any question. 
ご質問などある場合、お気軽にメールでご連絡ください。
