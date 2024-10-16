#!/usr/bin/env python

import logging
import os
import subprocess
from typing import Sequence, List

import boto3
import clize
import nbformat
from cachetools import cached, LRUCache
from nbconvert import HTMLExporter
from nbconvert.preprocessors.execute import ExecutePreprocessor
from nbformat import NotebookNode


def find_notebooks(prefix: str = "/app/collegium") -> Sequence[str]:
    reports = (
        subprocess.run(["find", prefix, "-name", "*.ipynb"], capture_output=True)
        .stdout.decode()
        .split("\n")
    )

    reports = [r for r in reports if "checkpoint" not in r and r != ""]

    return reports


@cached(cache=LRUCache(maxsize=1))
def get_s3():
    return boto3.client("s3")


def render_notebook(absolute_path: str):
    with open(absolute_path, "r") as f:
        notebook_str = f.read()

    s3 = get_s3()
    ipynb_s3_path = absolute_path[1:]
    s3.put_object(
        Bucket="danylo-ucla",
        ACL="public-read",
        Key=ipynb_s3_path,
        Body=notebook_str.encode("utf-8"),
    )
    logging.info(f"{absolute_path} -> {ipynb_s3_path}")

    notebook = nbformat.reads(notebook_str, as_version=4)  # type: NotebookNode
    exporter = HTMLExporter()
    html = exporter.from_notebook_node(notebook)[0]

    html_s3_path = absolute_path[1:].split(".")[0] + ".html"
    s3.put_object(
        Bucket="danylo-ucla",
        Key=html_s3_path,
        ACL="public-read",
        ContentType="text/html",
        Body=html.encode("utf-8"),
    )
    logging.info(f"{absolute_path} -> {html_s3_path}")


def execute_notebook(path: str):
    with open(path, "r") as f:
        notebook = nbformat.read(f, as_version=4)  # type: NotebookNode

    ep = ExecutePreprocessor(timeout=600)
    ep.preprocess(notebook, {"metadata": {"path": os.path.dirname(path)}})


def jupyter_process(*modules, execute: bool = False, render: bool = False):
    failed_notebooks = []

    user = subprocess.check_output('whoami').strip()
    subprocess.check_call(['sudo', 'chown', '-R', user, '/tmp'])

    for module in modules:
        notebooks = sorted(find_notebooks(prefix=f"/app/collegium/{module}"))

        for report_path in notebooks:
            try:
                logging.info(f"Started {report_path=}")
                if execute:
                    execute_notebook(report_path)
                if render:
                    render_notebook(report_path)
            except Exception as e:
                failed_notebooks.append(report_path)
                logging.exception(e)

    logging.info(f"Finished jupyter-process {failed_notebooks=}")

    # Report the exit code correctly,
    # so that downstream tasks are stopped.
    if len(failed_notebooks) > 0:
        exit(1)
    else:
        exit(0)
