# ZhuMing 3DGS Stylize

在 Unreal Engine 5.6 裡，把 3D Gaussian Splatting 掃描（陽明交大博愛校區竹銘館後方）做成有輪廓線、色塊和自然風的風格化場景。所有效果都寫在一個後製材質裡，並用 Python 腳本產生。

![最終畫面](stages/07_sun_handle/screenshot.png)

## 七個迭代階段

完整的過程說明、截圖和程式碼連結見 **[迭代紀錄](ITERATIONS.md)**。

每個階段的資料夾都有截圖、全部參數（`parameters.json`）、和上一階段的差異（`README.md`）、可重現的腳本（`apply.py`），以及實際的材質程式碼（`material.hlsl`）。

| 階段 | 內容 |
|---|---|
| [1](stages/01_outline/) | 畫出 outline |
| [2](stages/02_monet_patches/) | 以莫內風格色塊化 |
| [3](stages/03_tone_and_avenue/) | 細調色塊大小、對比、黑白點，中央道路的康莊大道聚光 |
| [4](stages/04_life_flow/) | 依生命方向流動：地面畫圈，樹木由下往上 |
| [5](stages/05_visible_sway/) | 擺動幅度加大到遊戲中可察覺 |
| [6](stages/06_natural_wind/) | 分開每棵樹，只動樹葉和灌木，模仿海邊陣風 |
| [7](stages/07_sun_handle/) | 調整光線的 UI：陽光把手 |

## 完整專案下載

到 [Releases](https://github.com/anniebelly/Unreal-Engine-Projects-at-NYCU-IAA/releases/tag/v1.0-zhuming-hall) 下載壓縮檔（約 1 GB），解壓後用 UE 5.6 打開 `Test_1006.uproject`，關卡為 `Lvl_ZhuMingHall`。

## 內容

- `scripts/outline_3dgs_pp.py`：最終版，所有參數都在檔案開頭
- `scripts/bake_canopy.py`、`scripts/bake_low_shrubs.py`：從 PLY 掃描產生遮光圖和灌木分布圖（用一般的 `python3` 執行）
- `scripts/face_gate_sun_handle.py`：開場視角
- `content_python/`：陽光把手面板，放到專案的 `Content/Python/`
- `data/`：烘焙好的兩張圖和樹幹位置

## 使用方式

需要 UE 5.6、Python Editor Script Plugin、NanoGS 外掛、一個 Gaussian Splat 場景，以及含 `CustomBrick` Custom 節點的後製材質 `/Game/_CMgit/_HLSL/CM_3DGS_PP`（節點要有 `ScreenUV` 輸入）。

1. 把 `data/` 裡的檔案複製到專案的 `Saved/CMgit/`。
2. 把 `content_python/` 裡的檔案複製到專案的 `Content/Python/`，重開編輯器。
3. 打開關卡，在 Output Log 的 Python 模式執行 `exec(open("腳本路徑").read())`。
4. 從上方選單「太陽把手」打開滑桿面板，在 Details 裡調整。

地形曲面 `GROUND_FIT`、遮光圖和樹幹位置都是這份掃描專屬的。換成別的掃描時，要改 `bake_*.py` 的路徑重新產生，並重新擬合地形。

## 已知限制

- 樹葉的擺動是畫面扭曲，不是真的移動點雲。要真實的單片葉子運動，需要修改 NanoGS 的 C++。
- 掃描本身不吃燈光，光線是在後製裡重算的，掃描裡原有的光影會留著。
- 陽光把手只存在於編輯器，打包後的遊戲沒有。

## 致謝與授權

後製材質的基礎和 `_CMgit` 素材來自 CMHsieh（Computing Aesthetics Lab）。NanoGS 外掛、掃描資料和這些素材只在 Release 的壓縮檔裡，不在 repo 的檔案中。

本作品採用 [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/deed.zh-hant) 授權（全文見 `LICENSE`）：可以自由使用、修改和分享，但要署名，且不得用於商業目的。此授權只涵蓋本 repo 中屬於作者的內容；CMHsieh 的原始素材、NanoGS 和 Unreal 範本內容不在授權範圍內。
