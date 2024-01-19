import sqlalchemy 
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "mysql+pymysql://raft_user:pass@localhost:3306/cluster_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class TestTable(Base):
    __tablename__ = "TestTable"
    register_id = sqlalchemy.Column(sqlalchemy.INT, primary_key=True)
    timestamp =  sqlalchemy.Column(sqlalchemy.INT, nullable=False, default="CURRENT_TIMESTAMP")
    address = sqlalchemy.Column(sqlalchemy.String(100), nullable=False)
    plug_status = sqlalchemy.Column(sqlalchemy.String(100), nullable=False)
    authenticated = sqlalchemy.Column(sqlalchemy.BOOLEAN, nullable=False)
    nominal_power = sqlalchemy.Column(sqlalchemy.INT, nullable=False)
    selected_max_power = sqlalchemy.Column(sqlalchemy.INT, nullable=False)
    planned_departure = sqlalchemy.Column(sqlalchemy.DATETIME, nullable=True)
    user_id = sqlalchemy.Column(sqlalchemy.INT, nullable=False)
    session_id = sqlalchemy.Column(sqlalchemy.String(20))
    evse_id = sqlalchemy.Column(sqlalchemy.String(100), nullable=False)
    max_cluster_power = sqlalchemy.Column(sqlalchemy.BIGINT, nullable=False)

"""
Tabela de configuração inicial dos parâmetros do carregador e endereço dos carregadores
"""
class Configuration(Base):
    __tablename__ = "Configuration"
    register_id = sqlalchemy.Column(sqlalchemy.INT, primary_key=True)
    timestamp =  sqlalchemy.Column(sqlalchemy.INT, nullable=False, default="CURRENT_TIMESTAMP")
    address = sqlalchemy.Column(sqlalchemy.String(100), nullable=False)
    nominal_power = sqlalchemy.Column(sqlalchemy.INT, nullable=False)
    evse_id = sqlalchemy.Column(sqlalchemy.String(100), nullable=False)

"""
Resultado do calculo do sistema distritibuido do selected_max_power para cada carregador
"""
class ScheduleTable(Base):
    __tablename__ = "Schedule"
    register_id = sqlalchemy.Column(sqlalchemy.INT, primary_key=True)
    timestamp =  sqlalchemy.Column(sqlalchemy.INT, nullable=False, default="CURRENT_TIMESTAMP")
    selected_max_power = sqlalchemy.Column(sqlalchemy.INT, nullable=False)
    planned_departure = sqlalchemy.Column(sqlalchemy.DATETIME, nullable=True)
    user_id = sqlalchemy.Column(sqlalchemy.INT, nullable=False)
    session_id = sqlalchemy.Column(sqlalchemy.String(20))
    evse_id = sqlalchemy.Column(sqlalchemy.String(100), nullable=False)
    max_cluster_power = sqlalchemy.Column(sqlalchemy.BIGINT, nullable=False)

"""
Tabela que será substituida por acesso a tabelas da base de dados evsedb_local para atualizar os dados da aplicação
Para interagir com a aplicação essa vai ser a tabela em que os dados serão alterados enquanto corre a aplicação
"""
class Simulation(Base):
    __tablename__ = "Simulation"
    register_id = sqlalchemy.Column(sqlalchemy.INT, primary_key=True)
    timestamp =  sqlalchemy.Column(sqlalchemy.INT, nullable=False, default="CURRENT_TIMESTAMP")
    plug_status = sqlalchemy.Column(sqlalchemy.String(100), nullable=False)
    authenticated = sqlalchemy.Column(sqlalchemy.BOOLEAN, nullable=False)
    user_id = sqlalchemy.Column(sqlalchemy.INT, nullable=False)
    session_id = sqlalchemy.Column(sqlalchemy.String(20))
    evse_id = sqlalchemy.Column(sqlalchemy.String(100), nullable=False)
    max_cluster_power = sqlalchemy.Column(sqlalchemy.BIGINT, nullable=False)