from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from cluster_db import SessionLocal

app = FastAPI()

class LimitRequest(BaseModel):
    total_limit_power: int = None
    num_active_nodes: int = None
    cluster_id:str 

class LimitResponse(BaseModel):
    new_total_limit: int
    total_capacity: int

@app.post("/total_limit_power")
def receive_limit(request: LimitRequest):
    # Simulate confirming the calculated limit
    req_limit = request.total_limit_power
    req_num_nodes = request.num_active_nodes
    total_power_capacity = self.cluster_maximum_capacity()
    min_power_capacity = self.cluster_minimum_capacity()
    try:
        db = SessionLocal()
        db_row = db.query(ClusterSincDataTable).filter_by(evse_id = self.id).first()
        if db_row:
            if total_power_capacity < req_limit: #Acima do máximo
                db_row.max_cluster_power = total_power_capacity 
            elif min_power_capacity > req_limit : #Abaixo do mínimo
                db_row.max_cluster_power = min_power_capacity
            else:
                db_row.max_cluster_power = req_limit
            #Update on the class the new max_cluster_power
            self.__max_cluster_power = db_row.max_cluster_power
        else:
            raise HTTPException(status_code=404, 
                                detail="Data not found on database")

        return LimitResponse(new_total_limit=request.total_limit_power)
    except HTTPException as http_error:
        raise HTTPException(status_code=http_error.status_code,
                            detail=http_error.detail)
    except Exception as error:
        logging.error(str(error))
        HTTPException(status_code=500, detail=str(error))
    finally:
        db.commit()
        db.close()
