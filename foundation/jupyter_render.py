#!/usr/bin/env python

import json
import logging
import os
import subprocess
import time
from typing import List, Optional, Sequence

import boto3
import clize
import nbformat
from cachetools import cached, LRUCache
from nbconvert import HTMLExporter
from nbconvert.preprocessors.execute import ExecutePreprocessor
from nbformat import NotebookNode

# Course checkout: cloned by the Studio lifecycle script, or fetched by the CI test job.
# The Studio image resolves `collegium.*` imports to this path.
COLLEGIUM_ROOT = "/home/sagemaker-user/collegium"

# Rendered notebooks are served by CloudFront from the private course bucket; written by cdk/site_stack.py
SITE_RESOURCES = "/collegium/site-resources"


def find_notebooks(prefix: str = COLLEGIUM_ROOT) -> Sequence[str]:
    reports = (
        subprocess.run(["find", prefix, "-name", "*.ipynb"], capture_output=True)
        .stdout.decode()
        .split("\n")
    )

    # Skip Jupyter checkpoints and copies that notebooks log as MLflow artifacts
    reports = [r for r in reports if "checkpoint" not in r and "/mlruns/" not in r and r != ""]

    return reports


@cached(cache=LRUCache(maxsize=1))
def get_s3():
    return boto3.client("s3")


@cached(cache=LRUCache(maxsize=1))
def get_site() -> dict:
    """Bucket, prefix, distributionId and domainName of the rendered-notebook site."""
    ssm = boto3.client("ssm", region_name="us-west-2")
    return json.loads(ssm.get_parameter(Name=SITE_RESOURCES)["Parameter"]["Value"])


def render_notebook(absolute_path: str, notebook: Optional[NotebookNode] = None, root: str = COLLEGIUM_ROOT) -> List[str]:
    """Uploads the notebook and its HTML rendering to the site; returns their URL paths.

    notebook: the executed notebook, if it was executed; otherwise the file is rendered as committed.
    """
    if notebook is None:
        notebook = nbformat.read(absolute_path, as_version=4)
    site, s3 = get_site(), get_s3()
    relative = os.path.relpath(absolute_path, root)
    pages = {relative: (nbformat.writes(notebook), "application/x-ipynb+json"),
             os.path.splitext(relative)[0] + ".html": (HTMLExporter().from_notebook_node(notebook)[0], "text/html; charset=utf-8")}
    for path, (body, content_type) in pages.items():
        key = f"{site['prefix']}/{path}"
        s3.put_object(Bucket=site["bucket"], Key=key, Body=body.encode("utf-8"), ContentType=content_type)
        logging.info(f"{absolute_path} -> https://{site['domainName']}/{path}")
    return [f"/{path}" for path in pages]


def invalidate_site(paths: Sequence[str]):
    """Makes CloudFront fetch the re-uploaded pages instead of serving cached copies."""
    if not paths:
        return
    boto3.client("cloudfront").create_invalidation(
        DistributionId=get_site()["distributionId"],
        InvalidationBatch={"Paths": {"Quantity": len(paths), "Items": list(paths)}, "CallerReference": str(time.time())},
    )
    logging.info(f"Invalidated {len(paths)} paths on https://{get_site()['domainName']}/")


def execute_notebook(path: str) -> NotebookNode:
    with open(path, "r") as f:
        notebook = nbformat.read(f, as_version=4)  # type: NotebookNode

    ep = ExecutePreprocessor(timeout=600)
    ep.preprocess(notebook, {"metadata": {"path": os.path.dirname(path)}})
    return notebook


def jupyter_process(*modules, execute: bool = False, render: bool = False, root: str = COLLEGIUM_ROOT):
    failed_notebooks = []
    rendered_paths = []

    user = subprocess.check_output('whoami').strip()
    subprocess.check_call(['sudo', 'chown', '-R', user, '/tmp'])

    for module in modules:
        notebooks = sorted(find_notebooks(prefix=os.path.join(root, module)))

        for report_path in notebooks:
            try:
                logging.info(f"Started {report_path=}")
                notebook = execute_notebook(report_path) if execute else None
                if render:
                    rendered_paths += render_notebook(report_path, notebook, root)
            except Exception as e:
                failed_notebooks.append(report_path)
                logging.exception(e)

    if render:
        invalidate_site(rendered_paths)
    logging.info(f"Finished jupyter-process {failed_notebooks=}")

    # Report the exit code correctly,
    # so that downstream tasks are stopped.
    if len(failed_notebooks) > 0:
        exit(1)
    else:
        exit(0)
