from uvicorn import run

# Import the FastAPI app from aggregator_api.py
from agregador_api import app

if __name__ == "__main__":
    # Run the Uvicorn server with the FastAPI app
    run(app, host="127.0.0.1", port=9500)
