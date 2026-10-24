# MLflow 3 validates Host headers (DNS rebinding) and CORS origins, allowing only localhost by default.
# Behind jupyter-server-proxy, requests carry the space's Studio host, e.g. <id>.studio.us-west-2.sagemaker.aws.
STUDIO_HOSTS = "*.studio.*.sagemaker.aws"

c.ServerProxy.servers = {
   "mlflow": {
        "command": [
            "/opt/venv/bin/python", "-m", "mlflow", "server", "--port", "{port}",
            "--backend-store-uri", "sqlite:////home/sagemaker-user/mlflow/mlflow.db",
            "--allowed-hosts", f"localhost,localhost:*,127.0.0.1,127.0.0.1:*,{STUDIO_HOSTS}",
            "--cors-allowed-origins", f"https://{STUDIO_HOSTS}",
        ],
        "timeout": 60,
        'launcher_entry': {
            'enabled': True,
            'title': 'mlflow',
            'icon_path': '/opt/collegium-env/mlflow.svg'
        }
   }
}
