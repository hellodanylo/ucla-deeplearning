c.ServerProxy.servers = {
   "mlflow": {
       "command": ["/app/miniconda/envs/collegium/bin/python", "-m", "mlflow", "server", "--port", "{port}", "--backend-store-uri", "file:///app/storage/ucla/mlflow"]
   }
}
