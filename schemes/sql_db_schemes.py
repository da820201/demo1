from sqlalchemy import Column, String, Integer, Float, JSON, DateTime, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()


class GeneralSchemes(Base):
    __tablename__ = "general_schemes"

    id = Column(Integer, primary_key=True, autoincrement=True)  # 自增主鍵
    sid = Column(String(512), nullable=True, unique=True)  # 設置唯一，防止重複
    account = Column(String(512), nullable=True, index=True)
    post_url = Column(String(512), nullable=True)
    videos = Column(JSON, default=[])
    images = Column(JSON, default=[])
    reel = Column(JSON, default=[])
    describe = Column(String(5000), default="")
    user_mood = Column(JSON, default=[])
    tags = Column(JSON, default=[])
    get_time = Column(Float, default=datetime.datetime.utcnow().timestamp())

    __table_args__ = (
        UniqueConstraint("sid", name="uq_general_schemes_sid"),  # 這是額外的安全措施
    )


from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from functions.config_manager import ConfigManager


def mount_config(conf_path: str = None):
    ConfigManager.add_positional_args(posi_args)
    ns = ConfigManager.parse_cli_args()
    file = ns.config_path if ns.config_path else conf_path
    config = ConfigManager.read_config(file)
    return config


# 創建資料庫連線
ConfigManager.read_yaml(rf"C:\Users\da820\PycharmProjects\pythonProject3\cofigs\config.yaml")
user = ConfigManager.sql.user
password = ConfigManager.sql.password
host = ConfigManager.sql.host
port = ConfigManager.sql.port
db = ConfigManager.sql.db
engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}")  # 可換成 MySQL / PostgreSQL
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()
Base.metadata.create_all(engine)

# 嘗試插入重複的 SID
try:
    post1 = GeneralSchemes(sid="12345", account="user1")
    post2 = GeneralSchemes(sid="12345", account="user2")  # 這會觸發 UNIQUE 錯誤

    session.add(post1)
    session.commit()

    session.add(post2)  # 嘗試插入重複的 SID
    session.commit()
except Exception as e:
    session.rollback()  # 回滾，防止數據庫錯誤
    print("錯誤：", e)  # 顯示唯一性違反的錯誤