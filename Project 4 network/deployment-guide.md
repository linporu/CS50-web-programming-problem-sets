# Network 專案部署指南

本指南說明如何將 Network 專案部署到生產環境：
- 後端：部署到 Render.com
- 前端：部署到 GitHub Pages

## 目錄
1. [事前準備](#事前準備)
2. [後端部署 (Render.com)](#後端部署-rendercom)
3. [前端部署 (GitHub Pages)](#前端部署-github-pages)
4. [部署後測試](#部署後測試)
5. [常見問題](#常見問題)

---

## 事前準備

### 需要的帳號
- [ ] GitHub 帳號
- [ ] Render.com 帳號（可用 GitHub 登入）

### 專案結構確認
```
CS50-web-programming-problem-sets/
└── Project 4 network/
    ├── network-backend/    # Django 後端
    └── network-frontend/   # React 前端
```

---

## 後端部署 (Render.com)

### 步驟 1: 準備 Django 專案

1. **建立 requirements.txt**
   ```bash
   cd network-backend
   pip freeze > requirements.txt
   ```

2. **建立 render.yaml**
   在 `network-backend/` 目錄下建立 `render.yaml`：
   ```yaml
   services:
     - type: web
       name: network-backend
       env: python
       buildCommand: "pip install -r requirements.txt"
       startCommand: "gunicorn project4.wsgi:application"
       envVars:
         - key: PYTHON_VERSION
           value: 3.9.0
         - key: SECRET_KEY
           generateValue: true
         - key: DEBUG
           value: False
         - key: DATABASE_URL
           fromDatabase:
             name: network-db
             property: connectionString
   
   databases:
     - name: network-db
       plan: free
   ```

3. **修改 Django 設定**
   
   在 `network-backend/project4/settings.py` 中加入：
   ```python
   import os
   import dj_database_url
   
   # 生產環境設定
   DEBUG = os.environ.get('DEBUG', 'True') == 'True'
   
   ALLOWED_HOSTS = [
       'localhost',
       '127.0.0.1',
       '.onrender.com',  # Render.com domain
       # 之後加入 GitHub Pages 網域
   ]
   
   # 資料庫設定
   if os.environ.get('DATABASE_URL'):
       DATABASES = {
           'default': dj_database_url.config(
               default=os.environ.get('DATABASE_URL')
           )
       }
   
   # CORS 設定
   CORS_ALLOWED_ORIGINS = [
       "http://localhost:5173",  # Vite 開發伺服器
       "http://localhost:3000",
       # 之後加入 GitHub Pages URL
       # "https://<your-username>.github.io",
   ]
   
   # 靜態檔案設定
   STATIC_URL = '/static/'
   STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
   
   # 安全設定
   if not DEBUG:
       SECURE_SSL_REDIRECT = True
       SESSION_COOKIE_SECURE = True
       CSRF_COOKIE_SECURE = True
   ```

4. **安裝必要套件**
   ```bash
   pip install gunicorn
   pip install dj-database-url
   pip install whitenoise
   pip install django-cors-headers
   pip freeze > requirements.txt
   ```

5. **加入 Whitenoise 中介軟體**
   在 `settings.py` 的 `MIDDLEWARE` 中加入：
   ```python
   MIDDLEWARE = [
       'django.middleware.security.SecurityMiddleware',
       'whitenoise.middleware.WhiteNoiseMiddleware',  # 加在這裡
       'django.contrib.sessions.middleware.SessionMiddleware',
       'corsheaders.middleware.CorsMiddleware',  # CORS
       # ... 其他中介軟體
   ]
   ```

### 步驟 2: 部署到 Render.com

1. **將後端程式碼推送到 GitHub**
   ```bash
   cd network-backend
   git init
   git add .
   git commit -m "Prepare for Render deployment"
   git remote add origin <your-backend-repo-url>
   git push -u origin main
   ```

2. **在 Render.com 建立新服務**
   - 登入 Render.com
   - 點擊 "New +" → "Web Service"
   - 連結 GitHub 儲存庫
   - 選擇剛才推送的後端儲存庫
   - 確認設定：
     - Environment: Python
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `gunicorn project4.wsgi:application`

3. **設定環境變數**
   在 Render 控制台中設定：
   - `SECRET_KEY`: (自動生成)
   - `DEBUG`: `False`
   - `PYTHON_VERSION`: `3.9.0`

4. **部署並記錄 URL**
   - 點擊 "Create Web Service"
   - 等待部署完成
   - 記錄下部署後的 URL：`https://network-backend-xxxx.onrender.com`

---

## 前端部署 (GitHub Pages)

### 步驟 1: 修改前端設定

1. **建立環境變數檔案**
   在 `network-frontend/` 目錄下建立 `.env.production`：
   ```env
   VITE_API_BASE_URL=https://network-backend-xxxx.onrender.com
   ```

2. **修改 API 設定**
   更新 `network-frontend/src/services/api.ts`：
   ```typescript
   export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
   ```

3. **修改 Vite 設定**
   更新 `network-frontend/vite.config.ts`：
   ```typescript
   export default defineConfig({
     plugins: [react()],
     base: '/CS50-web-programming-problem-sets/',  // 改為你的 repo 名稱
     // ... 其他設定
   });
   ```

4. **處理 React Router**
   在 `network-frontend/public/` 建立 `404.html`：
   ```html
   <!DOCTYPE html>
   <html>
     <head>
       <meta charset="utf-8">
       <title>Network</title>
       <script type="text/javascript">
         var pathSegmentsToKeep = 1;
         var l = window.location;
         l.replace(
           l.protocol + '//' + l.hostname + (l.port ? ':' + l.port : '') +
           l.pathname.split('/').slice(0, 1 + pathSegmentsToKeep).join('/') + '/?/' +
           l.pathname.slice(1).split('/').slice(pathSegmentsToKeep).join('/').replace(/&/g, '~and~') +
           (l.search ? '&' + l.search.slice(1).replace(/&/g, '~and~') : '') +
           l.hash
         );
       </script>
     </head>
   </html>
   ```

### 步驟 2: 建立 GitHub Actions

1. **建立部署工作流程**
   建立 `.github/workflows/deploy.yml`：
   ```yaml
   name: Deploy to GitHub Pages
   
   on:
     push:
       branches: [ main ]
     workflow_dispatch:
   
   permissions:
     contents: read
     pages: write
     id-token: write
   
   concurrency:
     group: "pages"
     cancel-in-progress: false
   
   jobs:
     build:
       runs-on: ubuntu-latest
       steps:
         - name: Checkout
           uses: actions/checkout@v4
           
         - name: Setup Node
           uses: actions/setup-node@v4
           with:
             node-version: '20'
             cache: 'npm'
             cache-dependency-path: ./network-frontend/package-lock.json
             
         - name: Install dependencies
           working-directory: ./network-frontend
           run: npm ci
           
         - name: Build
           working-directory: ./network-frontend
           run: npm run build
           env:
             VITE_API_BASE_URL: ${{ secrets.VITE_API_BASE_URL }}
             
         - name: Upload artifact
           uses: actions/upload-pages-artifact@v3
           with:
             path: ./network-frontend/dist
   
     deploy:
       environment:
         name: github-pages
         url: ${{ steps.deployment.outputs.page_url }}
       runs-on: ubuntu-latest
       needs: build
       steps:
         - name: Deploy to GitHub Pages
           id: deployment
           uses: actions/deploy-pages@v4
   ```

### 步驟 3: 設定 GitHub

1. **設定 GitHub Secrets**
   - 到 GitHub repo → Settings → Secrets and variables → Actions
   - 新增 Secret：
     - Name: `VITE_API_BASE_URL`
     - Value: `https://network-backend-xxxx.onrender.com`

2. **啟用 GitHub Pages**
   - 到 Settings → Pages
   - Source: 選擇 "GitHub Actions"

3. **推送程式碼觸發部署**
   ```bash
   git add .
   git commit -m "Setup GitHub Pages deployment"
   git push
   ```

---

## 部署後測試

### 測試清單
- [ ] 後端 API 可以訪問：`https://network-backend-xxxx.onrender.com/api/posts`
- [ ] 前端頁面可以訪問：`https://<username>.github.io/CS50-web-programming-problem-sets/`
- [ ] 前端可以成功呼叫後端 API
- [ ] 登入功能正常
- [ ] 發文功能正常
- [ ] CSRF token 正常運作

### 更新 CORS 設定
確保在後端的 `settings.py` 中加入前端的 GitHub Pages URL：
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "https://<username>.github.io",  # 加入這行
]
```

---

## 常見問題

### Q1: Render.com 免費方案的限制？
- 每月 750 小時的執行時間
- 閒置 15 分鐘後會進入休眠（第一次請求會慢一點）
- 免費 PostgreSQL 資料庫有 1GB 限制

### Q2: API 請求出現 CORS 錯誤？
1. 確認後端的 `CORS_ALLOWED_ORIGINS` 包含前端 URL
2. 確認已安裝並啟用 `django-cors-headers`
3. 重新部署後端

### Q3: GitHub Pages 路由問題？
- 確保已建立 `404.html`
- 檢查 `vite.config.ts` 的 `base` 設定是否正確

### Q4: 環境變數沒有生效？
- 確認 GitHub Secrets 設定正確
- 檢查 `.env.production` 檔案
- 重新執行 GitHub Actions

---

## 維護建議

1. **定期備份資料庫**
   - Render.com 提供自動備份功能（付費方案）
   - 可以定期手動匯出資料

2. **監控服務狀態**
   - 使用 Render.com 的監控功能
   - 設定 uptime 監控服務

3. **更新部署**
   - 後端：推送到 GitHub 會自動觸發 Render 部署
   - 前端：推送到 main 分支會自動觸發 GitHub Actions

---

## 下一步

完成基本部署後，可以考慮：
- [ ] 設定自訂網域
- [ ] 加入 CI/CD 測試流程
- [ ] 設定錯誤追蹤（如 Sentry）
- [ ] 優化效能（CDN、快取等）

祝部署順利！如有問題，請參考官方文件：
- [Render.com Django 部署指南](https://render.com/docs/deploy-django)
- [GitHub Pages 文件](https://docs.github.com/en/pages)
