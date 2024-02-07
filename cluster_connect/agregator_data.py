import sqlalchemy 
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from pydantic import BaseModel

class AgregadorInfo(BaseModel):
    leader_address: str
    num_nodes: int
    total_nominal_power: int
    total_limit_power: int
    cluster_id: str

    class Config:
        from_attributes=True

SQLALCHEMY_DATABASE_URL = "mysql+pymysql://raft_user:pass@localhost:3306/agregator_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class AgregadorTable(Base):
    __tablename__ = "clusterdataonclient"
    register_id = sqlalchemy.Column(sqlalchemy.INT, primary_key=True, nullable=False)
    timestamp =  sqlalchemy.Column(sqlalchemy.INT, nullable=False, 
                                   server_default=sqlalchemy.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
                                   server_onupdate=sqlalchemy.FetchedValue())
    leader_address = sqlalchemy.Column(sqlalchemy.String(100), nullable=False)
    num_nodes = sqlalchemy.Column(sqlalchemy.INT)
    total_nominal_power= sqlalchemy.Column(sqlalchemy.BIGINT)
    total_limit_power= sqlalchemy.Column(sqlalchemy.BIGINT)   
    cluster_id = sqlalchemy.Column(sqlalchemy.String(100), nullable=False)
