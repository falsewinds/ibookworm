### I, Bookworm

## 目的
I, Bookworm 是一個編輯與分享文檔的會員制網站，目的為在好友間分享自己創作或喜歡的故事。

## 技術
I, Bookworm 使用 Python flask 作為網站後端，計畫利用 Amazon EC2 服務建置。
會員資料與文檔目錄會採用 Amazon 的 DynamoDB 儲存，文檔內容則合併成一個 SQLite 檔案，供會員下載後離線使用。

## 當前目標
 - 建立簡單的介面與 SQLite 檔案溝通。
 - 建立會員介面測試 Amazon Congito 功能。
 - 建立目錄介面測試 DynamoDB。

## 未來目標
 - 建立方便擴充的爬蟲，目前考慮使用 requests + BeautifulSoup4。
 - 整合進小說寫作功能，包含地圖 (map)、詞彙 (glossary) 與年表 (chronicle) 文檔類別。
 - 整合 GPT 功能，協助翻譯、提供寫作靈感。
 - 整合 Stable Diffusion + ComfyUI，嘗試利用 Python 開關 Amazon EC2 (G4) 以減少花費。