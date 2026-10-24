c.ServerProxy.servers = {
   "mlflow": {
        "command": ["/opt/venv/bin/python", "-m", "mlflow", "server", "--port", "{port}", "--backend-store-uri", "sqlite:////home/sagemaker-user/mlflow/mlflow.db"],
        "timeout": 60,
        'launcher_entry': {
            'enabled': True,
            'title': 'mlflow',
            'icon_path': '/app/collegium/cdk/docker-studio/mlflow.svg'
        }
   }
}
