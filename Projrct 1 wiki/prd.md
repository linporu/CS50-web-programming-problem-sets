# Wiki 百科全書專案規格文件

## 功能需求

### 1. Entry Page 條目頁面
- 路徑: `/wiki/TITLE`
- 功能:
  - 顯示對應 encyclopedia entry 的內容
  - 使用 util function 獲取條目內容
  - 若條目不存在，顯示錯誤頁面
  - 若條目存在，顯示條目內容及標題

### 2. Index Page 首頁
- 更新 `index.html`
- 功能:
  - 列出所有 encyclopedia entries
  - 每個條目名稱可點擊並連結至對應頁面

### 3. Search 搜尋功能
- 位置: sidebar 搜尋框
- 功能:
  - 完全匹配: 直接導向對應條目頁面
  - 部分匹配: 顯示包含搜尋字串的所有條目列表
  - 搜尋結果頁面中的條目可點擊連結

### 4. New Page 新增頁面
- 位置: sidebar "Create New Page" 按鈕
- 功能:
  - 提供表單輸入:
    - 標題輸入欄
    - Markdown 內容 textarea
  - 儲存功能:
    - 檢查標題是否重複
    - 若重複則顯示錯誤訊息
    - 若無重複則儲存並導向新頁面

### 5. Edit Page 編輯功能
- 位置: 每個條目頁面
- 功能:
  - 編輯頁面預載現有 Markdown 內容
  - 提供儲存按鈕
  - 儲存後重新導向至該條目頁面

### 6. Random Page 隨機頁面
- 位置: sidebar
- 功能: 隨機導向任一 encyclopedia entry

### 7. Markdown 轉換
- 功能: 將條目內的 Markdown 內容轉換為 HTML
- 實作方式:
  - 基本版: 使用 `python-markdown2` 套件
  - 進階版: 自行實作轉換功能，支援:
    - 標題
    - 粗體文字
    - 無序列表
    - 連結
    - 段落

## 技術需求
- Framework: Django
- 套件相依: `python-markdown2` (基本版)
- 檔案儲存: 使用 Django 的檔案系統
