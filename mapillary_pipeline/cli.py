"""CLI interface for template_pipeline project.

Be creative! do whatever you want!

- Install click or typer and create a CLI app
- Use builtin argparse
- Start a web application
- Import things from your .base module
"""

import os
import sys
import importlib
from pathlib import Path

import kfp
from kfp_server_api import exceptions
from dotenv import load_dotenv

from .kfp_auth import DeployKFCredentialsOutOfBand, KFPClientManager


def main():  # pragma: no cover
    """
    The main function executes on commands:
    `python -m mapillary_pipeline pipeline_name ...args...` and
    `$ mapillary_pipeline pipeline_name ...args...`.

    This is your program's entry point.

    You can change this function to do whatever you want.
    """
    if len(sys.argv) < 2:
        raise ValueError("""Ran Improperly, make launch should be ran like:

make pipeline=download_data optional_args="first_arg=f,second_arg=b" launch
        """)
    assert "DEPLOYKF_HOST" in os.environ, "Host of deploykf instance required"
    assert "DEPLOYKF_NS" in os.environ, "Deploykf namespace required"
    print(sys.argv)
    pipeline_name = sys.argv[1]
    pipeline_args_list = sys.argv[2].split(",") if len(sys.argv) > 2 else []
    print(pipeline_args_list)
    pipeline_args_dict = {
        pipeline_arg.split("=")[0]: "=".join(pipeline_arg.split("=")[1:])
        for pipeline_arg in pipeline_args_list
    }
    print(pipeline_args_dict)
    deploykf_host = os.environ["DEPLOYKF_HOST"]
    deploykf_namespace = os.environ["DEPLOYKF_NS"]
    deploykf_username = os.environ.get("DEPLOYKF_USER", "")
    deploykf_password = os.environ.get("DEPLOYKF_PW", "")
    use_out_of_band = deploykf_username == "" or deploykf_password == ""

    # Import requested pipeline code
    package_name = Path.cwd().name
    module_name = f"{pipeline_name}_pipeline"
    from mapillary_pipeline import  download_data_pipeline 
    pipeline_module = importlib.import_module(f"{package_name}.{module_name}", package=package_name)
    # initialize a credentials instance and client

    # Security Note: As all deployments are routed through my routers iptable,
    # I am not too concerned about MITM attacks (so lack of ssl encryption is
    # fine for now). If others are connecting over the internet, be sure to
    # Setup https and set "skip_tls_verify" to False
    if use_out_of_band:
        credentials = DeployKFCredentialsOutOfBand(
            issuer_url=deploykf_host + "/dex",
            skip_tls_verify=True,
        )
        kfp_client = kfp.Client(
            host=deploykf_host + "/pipeline",
            verify_ssl=not credentials.skip_tls_verify,
            credentials=credentials,
        )
    else:
        kfp_client_manager = KFPClientManager(
            api_url=deploykf_host,
            skip_tls_verify=True,
            dex_username=deploykf_username,
            dex_password=deploykf_password,
            dex_auth_type="local",
        )
        kfp_client = kfp_client_manager.create_kfp_client()
    load_dotenv()
    # Get definition of experiment/run
    assert "EXPERIMENT" in os.environ, "Name of Experiment required"
    assert "RUN" in os.environ, "Name of run required"
    experiment_name = os.environ["EXPERIMENT"]
    run_name = os.environ["RUN"]
    # Make experiment if it does not exist
    try:
        kfp_client.get_experiment(experiment_name=experiment_name)
    except exceptions.ApiException:
        kfp_client.create_experiment(
            name=experiment_name, namespace=deploykf_namespace
        )
    kfp_client.create_run_from_pipeline_func(
        pipeline_func=pipeline_module.pipeline_func,
        arguments=pipeline_args_dict,
        experiment_name=experiment_name,
        run_name=run_name,
        namespace=deploykf_namespace,
    )