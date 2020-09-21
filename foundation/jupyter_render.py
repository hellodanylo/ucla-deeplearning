import os
import subprocess

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from nbformat import NotebookNode


def find_notebooks():
    reports = (
        subprocess.run(
            ["find", "/app/ucla_deeplearning", "-name", "*.ipynb"], capture_output=True
        )
        .stdout.decode()
        .split("\n")
    )

    reports = [
        r
        for r in reports
        if "checkpoint" not in r and "Template" not in r and r != ""
    ]

    return reports


def render_notebook(path):
    with open(path, "r") as f:
        notebook = nbformat.read(f, as_version=4)  # type: NotebookNode

    ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
    ep.preprocess(notebook, {"metadata": {"path": os.path.dirname(path)}})


notebooks = sorted(find_notebooks())
# notebooks = ['/app/ucla_deeplearning/01_dnn/UndercompleteAutoencoder.ipynb']

failed_notebooks = []
for report_path in notebooks:
    try:
        print(report_path)
        render_notebook(report_path)
    except Exception as e:
        failed_notebooks.append(report_path)
        print(e)

print("Failed notebooks:")
print("\n".join(failed_notebooks))
