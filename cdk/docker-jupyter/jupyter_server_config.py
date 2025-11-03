from amazon_sagemaker_jupyter_scheduler.scheduler import SageMakerStudioLabScheduler
from amazon_sagemaker_jupyter_scheduler.environments import SagemakerEnvironmentManager
from amazon_sagemaker_jupyter_scheduler.file_download_manager import SageMakerJobFilesManager

c.SchedulerApp.scheduler_class = SageMakerStudioLabScheduler
c.SchedulerApp.environment_manager_class = SagemakerEnvironmentManager
c.SchedulerApp.job_files_manager_class = SageMakerJobFilesManager

c.ServerProxy.servers = {
   "mlflow": {
        "command": ["/opt/conda/bin/python", "-m", "mlflow", "server", "--port", "{port}", "--backend-store-uri", "file:///home/sagemaker-user/mlflow"],
        "timeout": 60,
        'launcher_entry': {
            'enabled': True,
            'title': 'mlflow',
            'icon_path': '/app/collegium/cdk/docker-jupyter/mlflow.svg'
        }
   }
}
