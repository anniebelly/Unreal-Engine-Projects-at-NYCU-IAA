# 專案規格：NYCU ZhuMing Hall

這份文件用文字描述專案的最終狀態。人讀這份 Markdown，程式讀同資料夾的 JSON。`.uasset`、掃描和貼圖是二進位檔，這裡只記錄它們的設定和來源，內容本身要從 [Release](https://github.com/anniebelly/Unreal-Engine-Projects-at-NYCU-IAA/releases/tag/v1.0-zhuming-hall) 下載。

| 檔案 | 內容 |
|---|---|
| `project.json` | `.uproject` 專案設定 |
| `config.json` | Config 資料夾的全部設定（已遮掉 token） |
| `level.json` | 關卡裡每個物件的位置和屬性 |
| `material.json` | 材質節點、連線和完整 HLSL |
| `parameters.json` | 最終腳本的全部參數 |
| `assets.json` | 資產分類、大小、來源、授權狀態和外掛 |

## 專案

- 引擎：Unreal Engine 5.6
- 主要關卡：`Lvl_ZhuMingHall`（World Partition）
- 外掛：`ModelingToolsEditorMode`、`GameplayStateTree`、`OSC`、`NanoGS`、`Water`
- 效果全部在一個後製材質裡，由 Python 腳本寫入，專案沒有 C++ 或 Blueprint 邏輯

## 關卡物件

共 15 個（不含暫時的太陽把手面板）。

| 物件 | 類型 | 位置 (cm) | 備註 |
|---|---|---|---|
| `Cube` | StaticMeshActor | [-240.0, -140.0, 330.0] | 遊戲中隱藏 |
| `ExponentialHeightFog` | ExponentialHeightFog | [-5600.0, -50.0, -6850.0] |  |
| `Floor` | StaticMeshActor | [0.0, 0.0, 0.0] | 遊戲中隱藏 |
| `MatPreviewMesh` | StaticMeshActor | [639.0, 249.0, -137.455] | 遊戲中隱藏 |
| `PlayerStart` | PlayerStart | [256.32, -72.112, 80.0] |  |
| `PostProcessVolume` | PostProcessVolume | [0.0, 0.0, 0.0] | 後製材質：CM_3DGS_PP |
| `PreviewMannequin` | SkeletalMeshActor | [256.32, -72.112, -20.0] | 遊戲中隱藏 |
| `SM_SkySphere` | StaticMeshActor | [0.0, 0.0, 0.0] |  |
| `SkyAtmosphere` | SkyAtmosphere | [0.0, 0.0, 1020.0] |  |
| `SkyLight` | SkyLight | [0.0, 0.0, 690.0] |  |
| `SunHandle` | DirectionalLight | [256.32, -72.112, 690.0] | Intensity 4.21，可移動，大氣太陽 |
| `VolumetricCloud` | VolumetricCloud | [0.0, 0.0, 820.0] |  |
| `WorldDataLayers` | WorldDataLayers | [0.0, 0.0, 0.0] | 遊戲中隱藏 |
| `WorldPartitionMiniMap` | WorldPartitionMiniMap | [0.0, 0.0, 0.0] | 遊戲中隱藏 |
| `YangMing_NCTU_ZhuMingHall_Back` | GaussianSplatActor | [-10.0, -400.0, -250.0] |  |

## 太陽把手

關卡的 DirectionalLight 叫 `SunHandle`，目前旋轉為 pitch -77.791、yaw -19.188，Intensity 4.21。材質用 `View.AtmosphereLightDirection[0]` 和 `View.AtmosphereLightIlluminanceOnGroundPostTransmittance[0]` 即時讀取。

編輯器上方選單「太陽把手」由 `Content/Python/init_unreal.py` 載入 `sun_panel.py`，提供時間、方位、亮度、暖色四條滑桿和五個時段。

## 材質 CM_3DGS_PP

- 路徑：`/Game/_CMgit/_HLSL/CM_3DGS_PP`
- 類型：後製材質，混合位置在 Tonemapping 之後
- 所有效果都在一個 Custom 節點裡，輸出接到 Emissive Color

| 節點 | 接到 |
|---|---|
| Custom，輸入：`ScreenUV`、`sceneTexture`、`WorldPos`、`CamPos`、`CanopyTex`、`ShrubTex` | EmissiveColor |
| TextureObject（`T_LowShrubs`） | Custom_1 |
| TextureObject（`T_SunCanopy`） | Custom_1 |
| CameraPositionWS | Custom_1 |
| WorldPosition | Custom_1 |
| SceneTexture | Custom_1 |
| ScreenPosition | Custom_1 |

畫面處理順序：樹葉和灌木擺動 → 邊緣偵測 → 色塊筆觸 → 太陽遮光 → 對比、色階、飽和度 → 康莊大道和日光 → 暗部融入輪廓色 → 畫上輪廓線 → 光束。

完整程式碼在 `material.json`，也可以直接看 [material.hlsl](https://github.com/anniebelly/Unreal-Engine-Projects-at-NYCU-IAA/blob/main/20261006_NYCU%20ZhuMing%20Hall/stages/07_sun_handle/material.hlsl)。

## 烘焙資料

| 資料 | 用途 | 產生方式 |
|---|---|---|
| `T_SunCanopy` | 三個高度層的遮光圖，算地面光斑 | `scripts/bake_canopy.py` |
| `T_LowShrubs` | 低矮灌木分布，決定哪些地方會擺動 | `scripts/bake_low_shrubs.py` |
| `zhuming_trunks.json` | 樹幹位置，用來分開每棵樹和鎖住樹幹 | 從點雲偵測 |
| `GROUND_FIT` | 地形的三次曲面（誤差中位數 8 公分） | 擬合 `zhuming_ground.json` |

兩張圖都是 512×512、線性色彩，涵蓋掃描座標 -3200 到 4800 公分。

## 參數

### 輪廓線

| 參數 | 值 | 說明 |
|---|---|---|
| `THICKNESS` | `1.5` | line width in pixels |
| `DEPTH_THRESHOLD` | `0.03` | relative depth jump that starts a line (smaller = more lines) |
| `COLOR_THRESHOLD` | `0.25` | brightness jump that starts a line, for edges the depth misses (bigger = fewer) |
| `LINE_COLOR` | `[0.02, 0.02, 0.02]` |  |
| `MONET_LINE_COLOR` | `[0.05, 0.05, 0.11]` | deep blue-violet ink shared by outlines and darks |
| `LINE_STRENGTH` | `1.0` | outline opacity in Monet mode |

### 色塊與調色

| 參數 | 值 | 說明 |
|---|---|---|
| `MONET` | `true` |  |
| `PAINT_RADIUS` | `2` | brush-dab samples per side (Kuwahara filter radius; 0 = off) |
| `PAINT_SCALE` | `0.3` | brush-dab size multiplier (smaller = finer patches) |
| `LIGHT_TINT` | `[1.0, 0.93, 0.76]` | warm sunlight in the highlights |
| `SATURATION` | `1.4` |  |
| `CONTRAST` | `1.36` | light/dark separation (1 = unchanged) |
| `PIVOT` | `0.3` | brightness that contrast pivots around |
| `BANDS` | `12` | tonal steps for clear 濃淡 (0 = smooth) |
| `PASTEL` | `0.1` | mix toward white, only in the lit areas |
| `DARK_LO` | `0.08` | darks below DARK_HI fade into the line colour, fully at DARK_LO |
| `DARK_HI` | `0.224` | darks below DARK_HI fade into the line colour, fully at DARK_LO |
| `BRIGHTNESS` | `1.1` | overall brightness (1.1 = +10 %) |
| `HIGHLIGHT_BOOST` | `0.4` | extra brightness in the lit areas (0 = off) |

### 康莊大道

| 參數 | 值 | 說明 |
|---|---|---|
| `ROAD` | `true` |  |
| `ROAD_HALF_WIDTH` | `170.0` | cm, fully lit half width |
| `ROAD_SOFT` | `140.0` | cm, soft falloff beyond that |
| `ROAD_HEIGHT` | `120.0` | cm above the road that still gets light (keeps trees/fence out) |
| `ROAD_BOOST` | `1.1` | how much brighter the road gets |
| `ROAD_TINT` | `[1.0, 0.94, 0.8]` |  |

### 色塊流動（最終關閉）

| 參數 | 值 | 說明 |
|---|---|---|
| `FLOW` | `false` | paint patches keep flowing along "life veins": |
| `FLOW_UP_SPEED` | `0.35` | upward stream cycles per second (trunks) |
| `LEAF_SPEED` | `4.68` | leaves flow this many times faster than trunks |
| `FLOW_UP_LENGTH` | `7.2` | pixels a patch travels upward per cycle |
| `FLOW_CIRCLE_SPEED` | `1.2` | soil circling, radians per second |
| `FLOW_CIRCLE_RADIUS` | `3.0` | pixels |
| `ALIVE_SAT` | `[0.12, 0.25]` | saturation range where things start to count as living (green/brown); |
| `LEAF_STREAM` | `0.0` | bottom-to-top colour stream kept on green areas (1 = full) |

### 自然風

| 參數 | 值 | 說明 |
|---|---|---|
| `SWAY` | `true` | big trees' leaves and the rows of shrubs move in the wind; everything else stays put |
| `SWAY_AMOUNT` | `0.03` | peak swing in a gust, fraction of screen width (48 px on a 1600 px screen) |
| `SWAY_RHYTHM` | `2.6` | seconds per left-right swing |
| `SWAY_RATE_SPREAD` | `0.25` | each tree's rhythm differs by up to this fraction |
| `TREE_GUST_SPREAD` | `0.7` | how far apart in the gust cycle trees are hit (0 = together, 1 = fully scattered) |
| `GUST_PERIOD` | `7.0` | seconds between gusts |
| `GUST_SHARPNESS` | `3.0` | higher = shorter gusts with longer calm between them |
| `SWAY_CALM` | `0.12` | strength left between gusts (0 = fully still) |
| `GUST_SPEED` | `400.0` | cm per second the gust front travels, reaching one tree after another |
| `CROWN_RADIUS` | `300.0` | cm; how far around a trunk that tree's own sway reaches |
| `TREE_COUNT` | `48` | strongest trunks from zhuming_trunks.json that get their own sway |
| `TREE_SPACING` | `300.0` | cm; trunk detections closer than this count as the same tree |
| `WIND_DIR` | `[0.8, 0.6]` | gusts travel this way, reaching one tree after another |
| `TREE_SPEED` | `0.5` | tree motion speed: their swing and gusts run at this fraction of the base timing |
| `TRUNK_RADIUS` | `90.0` | cm around each detected trunk that never moves, and that leaves can't drag along |
| `PLANT_MIN_HEIGHT` | `35.0` | cm above the ground; green lower than this (grass, moss on the soil) stays still |
| `SHRUB_SCALE` | `0.5` | shrub swing relative to SWAY_AMOUNT |
| `SHRUB_TOP` | `250.0` | cm; below this counts as shrub, which ripples along its row instead of following a tree |
| `SHRUB_BEND_HEIGHT` | `150.0` | cm; shrubs are rooted: the foot stays put, full swing from this height up |
| `ROW_RIPPLE` | `0.012` | how quickly the swing changes along a shrub row, radians per cm |
| `LOW_SHRUB_SWING` | `0.75` | low shrubs from low_shrubs.png swing at least this much of the shrub setting, despite being short |
| `LEAF_MASK_RADIUS` | `0.032` | how far leaves may swing over their surroundings; keep at least SWAY_AMOUNT |
| `GROUND_FIT` | `[174.82, -72.22, -49.3, 11.34, 14.51, 5.02, -1.05, -1.46, -3.94, -1.19]` |  |

### 太陽與光線

| 參數 | 值 | 說明 |
|---|---|---|
| `SUN` | `true` |  |
| `SUN_NOON_PITCH` | `-78.0` | set once, on the first run: the light points almost straight down |
| `SUN_POOL` | `0.6` | how much brighter open ground gets; same soft multiply as the road light, kept below it |
| `SUN_SOFTNESS` | `0.06` | blur of the pool edges, per cm of canopy height (bigger = softer) |
| `CANOPY_ABSORB` | `2.5` | how much sun the canopy blocks (bigger = smaller, sharper pools) |
| `SUN_MAP_MIN` | `-3200.0` | same as bake_canopy.py |
| `SUN_MAP_SPAN` | `8000.0` | same as bake_canopy.py |
| `SUN_BANDS` | `[425.0, 800.0, 1400.0]` | middle height of each baked band, cm above ground |

### 光束

| 參數 | 值 | 說明 |
|---|---|---|
| `RAYS` | `true` |  |
| `RAY_SAMPLES` | `48` |  |
| `RAY_LENGTH` | `0.9` | how far toward the sun each pixel looks (0-1 of the way) |
| `RAY_DECAY` | `0.965` | falloff along a shaft |
| `RAY_INTENSITY` | `2.2` |  |
| `RAY_COLOR` | `[1.0, 0.9, 0.68]` |  |
| `RAY_SKY_DEPTH` | `3000.0` | cm; only gaps farther than this (sky) let light through |

其他參數見 `parameters.json`：`GROUND_HEIGHT`、`ROAD_A`、`ROAD_B`、`TREE_LIST`

## 資產

| 資料夾 | 檔案數 | 大小 | 來源 | 狀態 |
|---|---|---|---|---|
| `StarterContent` | 267 | 614.7 MB | Epic 範本 | Epic 授權 |
| `NanoGS` | 1 | 404.2 MB | 竹銘館掃描（NanoGS 匯入） | 公開版含，需確認拍攝者與學校 |
| `Characters` | 128 | 125.3 MB | Epic 範本 | Epic 授權 |
| `(Content 根目錄)` | 912 | 98.2 MB | RenderMan Shipshape 挑戰賽素材 | 未使用，公開版已排除 |
| `LevelPrototyping` | 36 | 3.0 MB | Epic 範本 | Epic 授權 |
| `__ExternalActors__` | 160 | 2.6 MB | 關卡物件 | 本專案 |
| `_CMgit` | 14 | 0.7 MB | CMHsieh 課程教材 | 公開版含，權利屬原作者 |
| `113_PostProcess Material-20261103` | 13 | 0.7 MB | _CMgit 副本 | 公開版已排除 |
| `ForestGlow` | 13 | 0.3 MB | 本專案 | CC BY-NC 4.0 |
| `Input` | 9 | 0.3 MB | Epic 範本 | Epic 授權 |
| `ZhuMingClean` | 3 | 0.3 MB | 本專案 | CC BY-NC 4.0 |
| `ThirdPerson` | 6 | 0.3 MB | 範本 + 本專案關卡 | 關卡為本專案 |
| `WarmMorning` | 1 | 0.0 MB | 本專案 | CC BY-NC 4.0 |
| `__ExternalObjects__` | 8 | 0.0 MB | 關卡物件 | 本專案 |
| `Python` | 3 | 0.0 MB | 本專案 | CC BY-NC 4.0 |

本機外掛：`DynamicSky`、`NanoGS`。`DynamicSky` 是暫停中的自製外掛，NanoGS 沒有授權檔。
