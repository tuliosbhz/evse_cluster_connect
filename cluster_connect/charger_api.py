
from cluster_db import SessionLocal, ClusterStatsTable
from fastapi import FastAPI, HTTPException
from uvicorn import run
from pydantic import BaseModel
import logging
import sys

class LimitRequest(BaseModel):
    total_limit_power: int = None
    num_active_nodes: int = None
    cluster_id:str 

class LimitResponse(BaseModel):
    new_total_limit: int
    total_capacity: int

api_app = FastAPI()

@api_app.post("/total_limit_power")
def receive_limit(request: LimitRequest):
    # Simulate confirming the calculated limit
    req_limit = request.total_limit_power
    req_num_nodes = request.num_active_nodes

    try:
        db = SessionLocal()
        db_row = db.query(ClusterStatsTable).filter_by(cluster_id = request.cluster_id).first()
        if db_row:
            total_power_capacity = db_row.total_power_capacity
            min_power_capacity = db_row.min_power_capacity
            if total_power_capacity < req_limit: #Acima do máximo
                db_row.total_limit_power = total_power_capacity 
            elif min_power_capacity > req_limit : #Abaixo do mínimo
                db_row.total_limit_power = min_power_capacity
            else:
                db_row.total_limit_power = req_limit
        else:
            raise HTTPException(status_code=404, 
                                detail="Data not found on database")

        return LimitResponse(new_total_limit=db_row.total_limit_power,
                                total_capacity=total_power_capacity)
    except HTTPException as http_error:
        raise HTTPException(status_code=http_error.status_code,
                            detail=http_error.detail)
    except Exception as error:
        logging.error(str(error))
        HTTPException(status_code=500, detail=str(error))
    finally:
        db.commit()
        db.close()

if __name__ == '__main__':
    if len(sys.argv) < 1:
        print('Usage: %s port of the uvicorn server ...' % sys.argv[0])
        sys.exit(-1)
    port = int(sys.argv[1])
    #GET the address from the db
    run(app=api_app,
        host="127.0.0.1",
        port=port)