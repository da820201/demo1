from elasticsearch import Elasticsearch
from functions.config_manager import ConfigManager


ConfigManager.read_yaml(rf"C:\Users\da820\PycharmProjects\pythonProject3\cofigs\config.yaml")
index_name = "fb_posts"
es = Elasticsearch(
    [f"{ConfigManager.es.protocol}://{ConfigManager.es.host}:{ConfigManager.es.port}"],  # Elasticsearch 服務的 URL
    basic_auth=("elastic", "changeme")  # 用戶名與密碼
)
# 設定索引 Mapping
if not es.indices.exists(index=index_name):
    es.indices.create(
        index=index_name,
        body={
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1
            },
            "mappings": {
                "properties": {
                    "sid": {"type": "keyword"},
                    "account": {"type": "keyword"},
                    "post_url": {"type": "text"},
                    "videos": {"type": "keyword"},
                    "images": {"type": "keyword"},
                    "reel": {"type": "keyword"},
                    "describe": {"type": "text"},
                    "user_mood": {"type": "keyword"},
                    "tags": {"type": "keyword"},
                    "get_time": {"type": "date", "format": "epoch_second"}
                }
            }
        }
    )
    print(f"索引 `{index_name}` 已建立！")
else:
    print(f"索引 `{index_name}` 已存在，跳過建立步驟。")