# 規格說明

完成拍賣網站的實作。你必須滿足以下要求：

## Models 資料模型
除了 User model 之外，你的應用程式至少要有三個 models：
- 拍賣清單 model
- 出價 model  
- 拍賣清單留言 model

你可以自行決定每個 model 應該有哪些欄位以及欄位的型別。如有需要也可以新增其他 models。

## 功能需求

### 建立拍賣清單
- 使用者可以前往頁面建立新的拍賣清單
- 可以指定拍賣標題、文字描述、起標價格
- 可選擇性提供圖片 URL 和/或分類 (例如:時尚、玩具、電子產品、家居等)

### 活躍拍賣清單頁面
- 網站預設路由應顯示所有目前活躍的拍賣清單
- 每個活躍清單至少要顯示:
  - 標題
  - 描述
  - 目前價格
  - 圖片(如果有的話)

### 拍賣清單詳細頁面
- 點擊清單後進入該清單的詳細頁面
- 使用者可以查看清單的所有詳細資訊，包括目前價格
- 已登入使用者功能:
  - 可將商品加入/移除"關注清單"
  - 可對商品出價
    - 出價必須大於等於起標價
    - 出價必須高於其他出價(如果有的話)
    - 不符合條件時應顯示錯誤訊息
  - 若為建立該清單的使用者:
    - 可以"結束"拍賣
    - 結束後最高出價者為得標者
    - 清單狀態變更為非活躍
  - 若為得標者:
    - 在已結束的拍賣頁面應顯示得標訊息
  - 可以對清單添加留言
  - 頁面應顯示該清單的所有留言

### 關注清單頁面
- 已登入使用者可以查看其關注清單頁面
- 顯示使用者加入關注的所有清單
- 點擊任何清單可前往該清單的詳細頁面

### 分類頁面
- 使用者可以查看所有拍賣分類列表
- 點擊任何分類名稱可前往該分類的頁面
- 分類頁面顯示該分類下所有活躍的拍賣清單

### Django Admin 介面
網站管理員可以透過 Django admin 介面:
- 查看
- 新增
- 編輯
- 刪除
任何拍賣清單、留言和出價紀錄

---

# Specification
Complete the implementation of your auction site. You must fulfill the following requirements:

## Models
Your application should have at least three models in addition to the User model: one for auction listings, one for bids, and one for comments made on auction listings. It's up to you to decide what fields each model should have, and what the types of those fields should be. You may have additional models if you would like.

## Create Listing
Users should be able to visit a page to create a new listing. They should be able to specify a title for the listing, a text-based description, and what the starting bid should be. Users should also optionally be able to provide a URL for an image for the listing and/or a category (e.g. Fashion, Toys, Electronics, Home, etc.).

## Active Listings Page
The default route of your web application should let users view all of the currently active auction listings. For each active listing, this page should display (at minimum) the title, description, current price, and photo (if one exists for the listing).

## Listing Page
Clicking on a listing should take users to a page specific to that listing. On that page, users should be able to view all details about the listing, including the current price for the listing.

If the user is signed in, the user should be able to add the item to their "Watchlist." If the item is already on the watchlist, the user should be able to remove it.

If the user is signed in, the user should be able to bid on the item. The bid must be at least as large as the starting bid, and must be greater than any other bids that have been placed (if any). If the bid doesn't meet those criteria, the user should be presented with an error.

If the user is signed in and is the one who created the listing, the user should have the ability to "close" the auction from this page, which makes the highest bidder the winner of the auction and makes the listing no longer active.

If a user is signed in on a closed listing page, and the user has won that auction, the page should say so.

Users who are signed in should be able to add comments to the listing page. The listing page should display all comments that have been made on the listing.

## Watchlist
Users who are signed in should be able to visit a Watchlist page, which should display all of the listings that a user has added to their watchlist. Clicking on any of those listings should take the user to that listing's page.

## Categories
Users should be able to visit a page that displays a list of all listing categories. Clicking on the name of any category should take the user to a page that displays all of the active listings in that category.

## Django Admin Interface
Via the Django admin interface, a site administrator should be able to view, add, edit, and delete any listings, comments, and bids made on the site.
