import agregador_api
from agregador_api import UpdateInfo
import requests
from agregator_data import SessionLocal, AgregadorTable, AgregadorInfo

# class Agregador():
#     def __init__(self, data:AgregadorInfo=None):
#         data = self.data_on_db()
#         self.leader_address = data.leader_address
#         self.num_nodes = data.num_nodes
#         self.total_nominal_power = data.total_nominal_power
#         self.total_limit_power = data.total_limit_power
#         self.cluster_id = data.cluster_id

#     def data_on_db(self):
#         db = SessionLocal()
#         data = db.query(AgregadorTable).filter(AgregadorTable.register_id.desc()).first()
#         db.commit()
#         db.close()
#         return data

#     def send_maximum_power(self, update_request:UpdateInfo):
#         port = 2000
#         str_req = "http://" + update_request.leader_address + port + "/cluster/limit_power"
#         # Simulate sending a request to update leader address
#         response = requests.post(update_request.leader_address, json={"update_request": True})

#         if response.status_code == 200:
#             # Simulate receiving updated data from followers
#             follower_data = response.json()
#             num_nodes = follower_data.get("num_nodes", num_nodes)
#             total_capacity = follower_data.get("total_capacity", total_capacity)
#         else:
#             follower_data = response.json()
#             leader_address = follower_data.get("leader_address", leader_address)

#         return UpdateInfo(
#             leader_address=update_request.leader_address,
#             num_nodes=num_nodes,
#             total_capacity=total_capacity
#         )

#     def get_cluster_data(self, leader_address):
#         port = 2000
#         str_req = "http://" + leader_address + port + "/cluster/get_data"
#         response = requests.get(str_req)

#         if response.status_code == 200:
#             data = response.json()
#             db = SessionLocal()
#             db_data = db.query(AgregadorTable).filter(AgregadorTable.register_id.desc()).first
#             db_data.num_nodes = data.get("num_nodes")
#             db_data.total_nominal_power = data.get("total_nominal_power")
#             db_data.total_limit_power = data.get("total_limit_power")
#             db.commit()
#             db.close()

#     def routine():
#         #In a loop make requests to the cluster
#         #Check if has a limit_power on the database
#         #If there is a value of limit power on the database send to the leader_address
#         #If sended to the wrong leader, resend to the correct leader
        
#         pass

from uvicorn import run

# Import the FastAPI app from aggregator_api.py
from agregador_api import app

if __name__ == "__main__":
    # Run the Uvicorn server with the FastAPI app
    run(app, host="127.0.0.1", port=9500)
