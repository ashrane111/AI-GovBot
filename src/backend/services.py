import subprocess
import uvicorn
import atexit

mlflow_process = None

def start_mlflow():
    global mlflow_process
    mlflow_process = subprocess.Popen(["mlflow", "server", "--host", "0.0.0.0", "--port", "5000"])

def stop_mlflow():
    global mlflow_process
    if mlflow_process:
        mlflow_process.terminate()
        mlflow_process.wait()

def start_fastapi():
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    start_mlflow()
    atexit.register(stop_mlflow)
    start_fastapi()