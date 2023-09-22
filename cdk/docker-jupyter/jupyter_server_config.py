c.ServerProxy.servers = {
   "mlflow": {
       "command": ["/app/conda/envs/collegium/bin/python", "-m", "mlflow", "server", "--port", "{port}", "--backend-store-uri", "file:///app/mlflow"],
        'launcher_entry': {
            'enabled': True,
            'title': 'mlflow',
            'icon_path': '/app/conda/envs/jupyter/mlflow.svg'
        }
   }
}
