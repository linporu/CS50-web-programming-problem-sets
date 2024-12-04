# 社群網站開發備忘錄

## API Endpoints 設計

### Posts API

#### 貼文基本操作
- `POST /api/posts/`
  - 建立新貼文
  - Request Body: `{ "content": "string" }`
  - Response: `201 Created`

- `GET /api/posts/`
  - 取得所有貼文（支援分頁）
  - Query Parameters: 
    - `page`: 頁碼
    - `size`: 每頁數量
    - `ordering`: 排序方式 (-created_at)
    - `following`: 是否只看追蹤的人 (true/false)

- `GET /api/posts/{id}/`
  - 取得特定貼文

- `PUT /api/posts/{id}/`
  - 編輯貼文（限作者）
  - Request Body: `{ "content": "string" }`

- `DELETE /api/posts/{id}/`
  - 刪除貼文（限作者）

#### 貼文互動
- `POST /api/posts/{id}/like/`
  - 按讚/取消按讚
  - Response: `{ "likes_count": number, "is_liked": boolean }`

### Users API

#### 使用者資料
- `GET /api/users/{username}/`
  - 取得使用者資料
  - Response:     ```json
    {
      "username": "string",
      "followers_count": number,
      "following_count": number,
      "is_following": boolean,
      "posts_count": number
    }    ```

- `GET /api/users/{username}/posts/`
  - 取得使用者的貼文
  - 支援分頁

#### 社交功能
- `POST /api/users/{username}/follow/`
  - 追蹤/取消追蹤
  - Response: `{ "is_following": boolean }`

- `GET /api/users/{username}/followers/`
  - 取得追蹤者清單
  - 支援分頁

- `GET /api/users/{username}/following/`
  - 取得正在追蹤的清單
  - 支援分頁

### Feed API
- `GET /api/feed/`
  - 取得追蹤者的貼文
  - 支援分頁

## 開發步驟

### 1. 後端開發 (Django)

#### 1.1 基礎設定
- [ ] 設定 Django REST framework
- [ ] 設定 CORS
- [ ] 設定認證系統
- [ ] 設定測試環境

#### 1.2 Models
- [ ] User Model (擴展內建 User)
- [ ] Post Model
- [ ] Like Model
- [ ] Following Model

#### 1.3 Serializers
- [ ] UserSerializer
- [ ] PostSerializer
- [ ] PostCreateUpdateSerializer

#### 1.4 Views
- [ ] PostViewSet
- [ ] UserViewSet
- [ ] FeedView

#### 1.5 測試
- [ ] Model 測試
- [ ] API 測試
- [ ] 權限測試

### 2. 前端開發 (React)

#### 2.1 專案設定
- [ ] 建立 React 專案
- [ ] 設定路由 (React Router)
- [ ] 設定狀態管理 (Context/Redux)
- [ ] 設定 API 客戶端

#### 2.2 共用元件
- [ ] Layout
- [ ] Navigation
- [ ] PostCard
- [ ] UserCard
- [ ] Pagination

#### 2.3 頁面
- [ ] 首頁 (貼文列表)
- [ ] 個人頁面
- [ ] 追蹤者頁面
- [ ] 新增/編輯貼文

#### 2.4 功能實作
- [ ] 貼文 CRUD
- [ ] 按讚功能
- [ ] 追蹤功能
- [ ] 分頁功能

## 開發注意事項

### API 回應格式
json
{
    "count": number,
    "next": string|null,
    "previous": string|null,
    "results": [
        {
        "id": number,
        "content": string,
        "created_by": {
        "username": string,
        "profile_url": string
        },
        "created_at": string,
        "likes_count": number,
        "is_liked": boolean,
        "can_edit": boolean
        }
    ]
}

### 錯誤處理
- 400: 請求格式錯誤
- 401: 未認證
- 403: 權限不足
- 404: 資源不存在
- 500: 伺服器錯誤

### 安全性考慮
- [ ] CSRF 保護
- [ ] XSS 防護
- [ ] 權限控制
- [ ] 資料驗證

### 效能優化
- [ ] API 快取
- [ ] 資料庫索引
- [ ] 分頁優化
- [ ] 前端效能優化

## 測試清單

### 後端測試
- [ ] Model 單元測試
- [ ] API 整合測試
- [ ] 權限測試
- [ ] 效能測試

### 前端測試
- [ ] 元件測試
- [ ] 整合測試
- [ ] E2E 測試

## 部署檢查清單
- [ ] 環境變數設定
- [ ] 資料庫遷移
- [ ] 靜態檔案處理
- [ ] CORS 設定
- [ ] 安全性檢查
- [ ] 效能監控