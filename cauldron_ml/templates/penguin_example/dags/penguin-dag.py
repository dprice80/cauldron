from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from kubernetes.client import models as k8s
from datetime import datetime, timedelta

# NOTE: In this file you need to change the following:
# Email addresses in the default_args. Failures and warnings will be sent here
# Cron schedule and any other applicable fields
# In the image tab, change MY-PROJECT:TAG to your deployed image tag
# Resources, increase of decrease RAM, CPUs as necessary.

# Do not change
KUBERNETES_NAMESPACE = "data-science-workloads"

# These args will get passed on to each operator
# you can override them on a per-task basis during operator initialization
default_args = {
    "depends_on_past": False,
    "retries": 0,
    "email": [
        "darren.price@moneysupermarket.com",
        "daniel.bluff@moneysupermarket.com"
    ],
    "email_on_failure": True,
    "email_on_retry": False,
}

dag = DAG(
    default_args=default_args,
    dag_id="prod_data_science_penguin_train",
    description="Train pipeline for penguin data running once a month on the 1st of every month",
    schedule_interval="0 0 1 * *",  # 00:00 on day 1 of month, i.e. once a month. Use http://https://crontab.guru/ for advanced scheduling
    max_active_runs=1,
    catchup=False,
    start_date=datetime(2023, 1, 1),
    tags=[
        "AREA_DATA_SCIENCE",
        "SEVERITY_NOTICE", # SEVERITY_CRITICAL/SEVERITY_WARNING/SEVERITY_NOTICE
        "MONITORING_UNMONITORED", # MONITORING_UNMONITORED, MONITORING_ALWAYS_ON, MONITORING_ONE_PER_DAY, MONITORING_MOST_RECENT_RUN_MUST_SUCCEED, MONITORING_ALL_RUNS_MUST_SUCCEED
    ],
)
with dag:

    predict = KubernetesPodOperator(
        dag=dag,
        # The ID specified for the task.
        task_id="train",
        # Name of task you want to run, used to generate Pod ID.
        name="train",
        # Entrypoint of the container, if not specified the Docker container's
        # entrypoint is used. The cmds parameter is templated.
        cmds=["python", "run.py",],
        # The namespace to run within Kubernetes
        namespace=KUBERNETES_NAMESPACE,
        # location of the docker image on google container repository
        image="europe-west2-docker.pkg.dev/msm-groupdata-sharedresources/data-science-ml-pipelines/penguin_component:prod_ci",
        # Always pulls the image before running it.
        image_pull_policy="Always",
        # request_memory, request_cpu, limit_memory, limit_cpu
        container_resources=k8s.V1ResourceRequirements(
            requests={"cpu": "8", "memory": "32Gi"},
            limits={"cpu": "16", "memory": "64Gi"},
        ),
        config_file="{{ conf.get('core', 'kube_config') }}",
        # increase timeout from default of 120 to 360, to give time to k8 to scale up if needs be
        startup_timeout_seconds=360,
        # Service account to use (do not change)
        service_account_name="robot-scientist",
        # Labels to apply to the Pod
        labels={"asset": "datascience"},
    )

DummyOperator(task_id="start") >> predict >> DummyOperator(task_id="finish")

