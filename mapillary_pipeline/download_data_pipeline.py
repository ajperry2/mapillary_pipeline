from kfp import dsl, kubernetes

from .download_data_components import download_data


@dsl.pipeline
def pipeline_func(url: str) -> None:

    task = download_data(url=url).set_caching_options(enable_caching=False).ignore_upstream_failure()