#!/usr/bin/env python
import pathlib
import shutil
import sys
from typing import Optional

import typer
from perfcapture.dataset import create_datasets_if_necessary
from perfcapture.workload import discover_workloads, run_workloads
from typing_extensions import Annotated

app = typer.Typer()


@app.command()
def bench(
    data_path: Annotated[
        pathlib.Path,
        typer.Option(help="The path for storing the data which the benchmarks read from.")
    ],
    recipe_path: Annotated[
        pathlib.Path,
        typer.Option(help=(
            "The path containing the code which defines the Workloads and Datasets."))
    ] = pathlib.Path("."),
    selected_workloads: Annotated[
        Optional[str], 
        typer.Option(help=(
            "Space-separated list of workloads to run. If not set, all workloads found in"
            " recipe_path will be run. Use the `name` of each workload."))
        ] = None,
    keep_cache: Annotated[
        bool, 
        typer.Option(
            help="Set this flag to prevent `vmtouch -e` being called before each benchmark.",
            )
        ] = False,
    ) -> None:
    """Run workload(s) and measure performance.
    
    If any of the workloads require datasets to be pre-prepared then this script will first generate
    all datasets required by the workload(s). Those datasets will be stored at the `data_path`.
    The time spent creating the datasets will not be recorded. The contents of `data_path` will not
    be removed after running this script. So if you run this script multiple times then subsequent
    runs can make use of the already existing datasets.
    
    If you update the recipe which specifies the dataset creation then it is up to you to manually
    delete the old dataset on disk.
    
    vmtouch must be installed if you wish to clear the page cache after each iteration.
    """
    # Sanity checks
    if not data_path.exists():
        sys.exit(f"ERROR! {data_path} does not exist! Please create the directory!")
    if not recipe_path.exists():
        sys.exit(f"ERROR! {recipe_path} does not exist!")
    if shutil.which("vmtouch") is None:  # Check if vmtouch has been installed.
        sys.exit(
            "If you want to flush the page cache before each iteration, then please install"
            " vmtouch. Or run with the --keep-cache option, which does not call vmtouch.")
    
    workloads = discover_workloads(recipe_path)
    print(f"Found {len(workloads)} Workload class(es) in {recipe_path}")

    # Filter workloads (if necessary).
    if selected_workloads:
        selected_workloads: list[str] = selected_workloads.split(" ")
        workloads = filter(lambda workload: workload.name in selected_workloads, workloads)

    create_datasets_if_necessary(workloads, data_path)
    run_workloads(workloads, keep_cache)


if __name__ == "__main__":
    app()
