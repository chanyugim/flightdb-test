from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import Depends

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    # 인증 조회 시점의 과거 포인트 이력을 잠금 이후에도 사용하지 않도록 함.
    isolation_level="READ COMMITTED",
    connect_args={
        "init_command": f"SET time_zone = '+09:00', max_execution_time = {settings.db_statement_timeout_ms}",
        "connect_timeout": 5,
        "read_timeout": 10,
        "write_timeout": 10,
    },
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_chat_db(db=Depends(get_db)):
    db.info["chat_read_only"] = True
    try:
        yield db
    finally:
        db.rollback()
        db.info.pop("chat_transaction_started", None)


def start_chat_read_only(db):
    if (
        db.info.get("chat_read_only")
        and not db.info.get("chat_transaction_started")
        and db.get_bind().dialect.name == "mysql"
    ):
        db.connection().exec_driver_sql("START TRANSACTION READ ONLY")
        db.info["chat_transaction_started"] = True
