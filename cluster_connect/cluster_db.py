import sqlalchemy 
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "mysql+pymysql://raft_user:pass@localhost:3306/cluster_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

"""
Tabela de configuração inicial dos parâmetros do carregador e endereço dos carregadores
"""
class Configuration(Base):
    __tablename__ = "Configuration"
    register_id = sqlalchemy.Column(sqlalchemy.INT, primary_key=True)
    timestamp =  sqlalchemy.Column(sqlalchemy.INT, nullable=False, 
                                   server_default=sqlalchemy.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
                                   server_onupdate=sqlalchemy.FetchedValue())
    address = sqlalchemy.Column(sqlalchemy.String(100), nullable=False)
    nominal_power = sqlalchemy.Column(sqlalchemy.INT, nullable=False)
    evse_id = sqlalchemy.Column(sqlalchemy.String(100), nullable=False)

"""
Resultado do calculo do sistema distritibuido do selected_max_power para cada carregador
"""
class ClusterStatsTable(Base):
    __tablename__ = "clusterStats"
    register_id = sqlalchemy.Column(sqlalchemy.INT, primary_key=True)
    timestamp =  sqlalchemy.Column(sqlalchemy.TIMESTAMP, nullable=False, 
                                   server_default=sqlalchemy.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
                                   server_onupdate=sqlalchemy.FetchedValue())
    cluster_id = sqlalchemy.Column(sqlalchemy.String(100), nullable=False)
    num_nodes = sqlalchemy.Column(sqlalchemy.INT, nullable=False)
    total_limit_power = sqlalchemy.Column(sqlalchemy.INT)
    total_power_capacity = sqlalchemy.Column(sqlalchemy.INT)
    min_power_capacity = sqlalchemy.Column(sqlalchemy.INT)
    num_active_nodes = sqlalchemy.Column(sqlalchemy.INT)

"""
Tabela que será substituida por acesso a tabelas da base de dados evsedb_local para atualizar os dados da aplicação
Para interagir com a aplicação essa vai ser a tabela em que os dados serão alterados enquanto corre a aplicação
"""
class EvseDataSimTable(Base):
    __tablename__ = "evseDataSim"
    register_id = sqlalchemy.Column(sqlalchemy.INT, primary_key=True)
    timestamp =  sqlalchemy.Column(sqlalchemy.INT, nullable=False, 
                                   server_default=sqlalchemy.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
                                   server_onupdate=sqlalchemy.FetchedValue())
    plug_status = sqlalchemy.Column(sqlalchemy.String(100), nullable=False)
    authenticated = sqlalchemy.Column(sqlalchemy.BOOLEAN, nullable=False)
    user_id = sqlalchemy.Column(sqlalchemy.INT, nullable=False)
    session_id = sqlalchemy.Column(sqlalchemy.String(20))
    evse_id = sqlalchemy.Column(sqlalchemy.String(100), nullable=False)
    cluster_id = sqlalchemy.Column(sqlalchemy.String(100))
    min_power_capacity = sqlalchemy.Column(sqlalchemy.INT)
    power_capacity = sqlalchemy.Column(sqlalchemy.INT)
    measured_power = sqlalchemy.Column(sqlalchemy.INT)
    selected_max_power = sqlalchemy.Column(sqlalchemy.INT)

Base.metadata.create_all(bind=engine)