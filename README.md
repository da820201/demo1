1. 請確保運行在Python 3.11.3 up 的環境
2. 執行 pip install requirements.txt
2. 如果沒有Docker，請安裝Docker
3. 在根目錄下docker-compose up -d 讓資料庫能順利啟動
4. 檢查資料庫是否啟動成功，本 Demo 主要在 Elasticsearch 資料庫上讀寫，跑完Docker Compose後先進9200查看資料庫是否正常運作
5. 本Demo需要借助Kibana的dev tools，需要讓Kibana運行起來，因此為Kibana創建所屬帳戶，不能使用root的帳戶
6. 接著，在Terminal上執行 docker exec -it elasticsearch bin/elasticsearch-reset-password -u kibana_system 創建 kibana帳戶，先別把Terminal關閉，把密把記錄下來，返回doker-compose.yaml進行kibana密碼的修改
5. 重新執行docker-compose up -d 讓Kibana能夠使用最新的參數
6. 完成後進入127.0.0.1:5601查看Kibana是否運作成功
7. 執行python main.py的腳本
8. 完成