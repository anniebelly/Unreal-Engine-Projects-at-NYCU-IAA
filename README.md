# NYCU ZhuMing Hall：把 3D 掃描變成會呼吸的畫

用 Unreal Engine 5.6，把陽明交大竹銘館的 3D Gaussian Splatting 掃描，一步步變成有輪廓線、色塊、自然風和可調陽光的風格化場景。

![七個階段的變化](20261006_NYCU%20ZhuMing%20Hall/demo/seven_stages.gif)

**[⬇ 下載完整專案（約 1 GB）](https://github.com/anniebelly/Unreal-Engine-Projects-at-NYCU-IAA/releases/download/v1.0-zhuming-hall/Test_1006_public_v4_20261104.zip)** · **[看七個階段的完整過程](20261006_NYCU%20ZhuMing%20Hall/ITERATIONS.md)**

## Demo

實際畫面錄影：樹葉和灌木隨陣風擺動，樹幹、地面和圍欄不動。

![自然風](20261006_NYCU%20ZhuMing%20Hall/demo/wind.gif)

## 怎麼打開

你需要安裝 **Unreal Engine 5.6**。下載上面的壓縮檔並解壓，然後：

### Mac（Apple Silicon）

UE 要裝在預設位置 `/Users/Shared/Epic Games/UE_5.6`。這個專案的外掛沒有 Apple 認證，所以第一次要放行兩次，**第三次打開 `Test_1006.uproject` 就會順利開啟**：

1. **第一次打開** `Test_1006.uproject`：出現「Apple 無法驗證」的警告時按 **完成**（不要按丟到垃圾桶），錯誤訊息按 **OK**。
2. 到 **系統設定 > 隱私權與安全性**，捲到最下面，按 **強制允許**（有些 macOS 顯示為「強制打開」）。
3. **第二次打開** `Test_1006.uproject`：有詢問就選 **打開**。第二個外掛檔案會再被擋一次，一樣按 **完成** 和 **OK**。
4. 再到 **系統設定 > 隱私權與安全性**，捲到最下面，按 **強制允許**。
5. **第三次打開** `Test_1006.uproject`，有詢問就選 **打開**，專案就會順利開啟。

**打不開時**

- **沒有警告、UE 一直停著或跳一下就沒反應**：強制結束 UnrealEditor（`Cmd + Option + Esc`），把解壓後的資料夾改個名字，再打開一次。
- **系統設定裡找不到「強制允許」**：開啟「終端機」，輸入 `xattr -dr com.apple.quarantine ` 後把解壓後的資料夾拖進視窗，按 Enter，再打開專案。這會解除這個資料夾的下載隔離，請只用在你信任的檔案上。

### Windows

打開 `Test_1006.uproject`。Windows 版尚未實際測試，遇到問題歡迎開 [Issue](https://github.com/anniebelly/Unreal-Engine-Projects-at-NYCU-IAA/issues)。

第一次打開要編譯 shader，停在某個百分比很久是正常的。

## 調整陽光

點編輯器最上方選單的 **太陽把手 > 打開滑桿面板**，再到右側 **Details** 分頁，就能調整時間、方位、亮度和暖色。

## 想深入了解

| 我想看 | 去這裡 |
|---|---|
| 每個階段怎麼做、程式碼和截圖 | [迭代紀錄](20261006_NYCU%20ZhuMing%20Hall/ITERATIONS.md) |
| 所有設定的文字版（Markdown、JSON） | [專案規格](20261006_NYCU%20ZhuMing%20Hall/project_spec/PROJECT.md) |
| 把效果裝到自己有這份掃描的專案 | [使用說明](20261006_NYCU%20ZhuMing%20Hall/README.md) |

## 致謝與授權

後製材質的基礎和 `_CMgit` 素材來自 CMHsieh（Computing Aesthetics Lab）。

作者自己的內容採 [CC BY-NC 4.0](LICENSE)：可以自由使用和修改，要署名，不得商用。原始素材、NanoGS 和 Unreal 範本內容屬於各自的權利人。
