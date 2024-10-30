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

---

# Specification

Complete the implementation of your Wiki encyclopedia. You must fulfill the following requirements:

## Entry Page
- Visiting `/wiki/TITLE`, where TITLE is the title of an encyclopedia entry, should render a page that displays the contents of that encyclopedia entry
- The view should get the content of the encyclopedia entry by calling the appropriate util function
- If an entry is requested that does not exist, the user should be presented with an error page indicating that their requested page was not found
- If the entry does exist, the user should be presented with a page that displays the content of the entry. The title of the page should include the name of the entry

## Index Page 
- Update index.html such that, instead of merely listing the names of all pages in the encyclopedia, user can click on any entry name to be taken directly to that entry page

## Search
- Allow the user to type a query into the search box in the sidebar to search for an encyclopedia entry
- If the query matches the name of an encyclopedia entry, the user should be redirected to that entry's page
- If the query does not match the name of an encyclopedia entry:
  - The user should be taken to a search results page
  - Display a list of all encyclopedia entries that have the query as a substring
  - Example: if search query is "ytho", then "Python" should appear in results
- Clicking on any entry name in search results should take user to that entry's page

## New Page
- Clicking "Create New Page" in sidebar should take user to new page creation form
- Users should be able to:
  - Enter a title for the page
  - Enter Markdown content in a textarea
  - Click button to save the new page
- When saving:
  - If entry exists with same title, show error message
  - Otherwise, save entry to disk and redirect to new entry's page

## Edit Page
- On each entry page, provide link to edit page
- Edit page should:
  - Show textarea pre-populated with existing Markdown content
  - Have button to save changes
  - Redirect to entry page after saving

## Random Page
- Clicking "Random Page" in sidebar should take user to random encyclopedia entry

## Markdown to HTML Conversion
- Convert Markdown content to HTML before display
- Basic: Use python-markdown2 package (install via pip3 install markdown2)
- Advanced Challenge:
  - Implement conversion without external libraries
  - Support:
    - Headings
    - Boldface text
    - Unordered lists
    - Links
    - Paragraphs
  - Tip: Consider using Python regular expressions