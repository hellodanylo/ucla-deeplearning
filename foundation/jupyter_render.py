import os
import subprocess

import nbformat

reports = subprocess.run(
    ["find", "/app/ucla_deeplearning", "-name", "*.ipynb"], capture_output=True
).stdout.decode().split('\n')

reports = [r for r in reports if 'checkpoint' not in r]

for report_path in reports:
    basename = os.path.basename(report_path).split(".")[0]

    with open(report_path, "r") as f:
        notebook = nbformat.read(f, as_version=4)

    ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
    ep.preprocess(notebook, {"metadata": {"path": "."}})
    del os.environ["MLQ_DATABASE_NAME"]

    html = nbconvert.exporters.export(nbconvert.exporters.HTMLExporter(), notebook)[0]

    with open(f"{output_dir}/{basename}.html", "w") as f:
        f.write(html)
