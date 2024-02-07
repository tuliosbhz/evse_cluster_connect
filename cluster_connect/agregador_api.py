from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from agregator_data import AgregadorTable, SessionLocal
import logging

app = FastAPI()

class UpdateInfo(BaseModel):
    leader_address: str
    num_nodes: int
    total_capacity: int
    cluster_id:str

class LimitRequest(BaseModel):
    current_limit: int = None
    num_active_nodes: int = None
    cluster_id:str 

class LimitResponse(BaseModel):
    new_total_limit: int
    total_capacity: int

class ClusterRegistration(BaseModel):
    leader_address:str
    cluster_id:str
    

@app.post("/cluster_registration", tags=["cluster_comm"])
def update_leader(cluster_info: ClusterRegistration):
    #Search on database for the cluster_id
    #   If already exists, update the last_leader_address received and return
    #   If cluster_id do not exist, add on database the new cluster_id and leader_address
    try:
        db = SessionLocal()
        query_rows = (db.query(AgregadorTable)
                    .filter(AgregadorTable.cluster_id == cluster_info.cluster_id)
                                        .order_by(AgregadorTable.register_id.desc())
                                        .all())
        #Verifica se já não está registado
        if query_rows:
            #Verifica multiplos registos
            if len(query_rows) > 1:
                #TODO: Delete the old ones and keep only the last registration based on register_id column
                raise HTTPException(status_code=403, detail="Multiple cluster_id registered")
            else:#Cluster já registado
                #Atualiza endereço do lider
                query_rows[0].leader_address = cluster_info.leader_address
                raise HTTPException(status_code=226, detail=f"Cluster {cluster_info.cluster_id} registered, leader_address updated")
        else:
            #Não registado, realizar registo
            new_cluster = AgregadorTable()
            new_cluster.cluster_id = cluster_info.cluster_id
            new_cluster.leader_address = cluster_info.leader_address
            db.add(new_cluster)
            return {"detail": f"Success {cluster_info.cluster_id} added to client"}
    except Exception as error:
        logging.error(str(error))
        raise HTTPException(status_code=500, detail=str(error))
    finally:
        db.commit()
        db.close()

@app.post("/update_cluster_info", tags=["cluster_comm"])
def update_leader(request: UpdateInfo):
    # Simulate initializing and fetching data from the database
    try:
        db = SessionLocal()
        c_info_db = (db.query(AgregadorTable)
                    .filter_by(cluster_id = request.cluster_id).first())
        if c_info_db:
            if request.leader_address == c_info_db.leader_address:
                #Somente atualiza se vier do endereço do lider
                c_info_db.leader_address = request.leader_address
                c_info_db.num_nodes = request.num_nodes
                c_info_db.total_nominal_power = request.total_capacity  # Assuming total capacity in watts
            else:
                raise HTTPException(status_code=403,
                                    detail=f"Only update data from the current leader address")
        else:
            raise HTTPException(status_code=404, 
                                detail=f"Cluster {request.cluster_id} not found, register your cluster first")
    except HTTPException as http_error:
        logging.error(str(http_error))
        raise HTTPException(status_code=http_error.status_code, detail=str(http_error.detail))
    except Exception as error:
        logging.error(str(error))
        raise HTTPException(status_code=500, detail=str(error))
    finally:
        db.commit()
        db.close()

@app.get("/request_calculate_limit", tags=["cluster_comm"])
def calculate_limit(request: LimitRequest):
    # Simulate calculating the limit based on received data
    try: 
        calculated_limit = request.current_limit
        num_active_nodes = request.num_active_nodes
        cluster_id = request.cluster_id
        db = SessionLocal()
        c_info_db = db.query(AgregadorTable).filter_by(cluster_id = cluster_id).first()

        if c_info_db:
            if c_info_db.total_limit_power: #TODO: Create some logic of calculation of the maximum power here
                response = LimitResponse()
                response.new_total_limit = c_info_db.total_limit_power
                response.total_capacity = c_info_db.total_nominal_power
                return response
        else: 
            raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
    finally:
        db.close()

@app.post("/request_calculate_limit", tags=["External"])
def calculate_limit(request: LimitRequest):
    # Simulate calculating the limit based on received data
    try: 
        calculated_limit = request.current_limit
        num_active_nodes = request.num_active_nodes
        cluster_id = request.cluster_id
        db = SessionLocal()
        c_info_db = db.query(AgregadorTable).filter_by(cluster_id = cluster_id).first()
        req_str = "http://" + c_info_db.leader_address + "/total_limit_power"
        print(req_str)
        response = requests.post(req_str, json=request.model_dump_json())
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.json())
        else:
            return response
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
        

