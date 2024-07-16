from kfp.dsl import component, Output, Dataset


@component()
def download_data(
    url: str,
    dataset: Output[Dataset]
):
    import urllib.request
    import zipfile
    import os
    from pathlib import Path
    dataset_path = Path(dataset.path)
    dataset_path.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, f"{dataset_path}/data.zip")
    with zipfile.ZipFile(dataset_path / "data.zip", 'r') as zip_ref:
        zip_ref.extractall(dataset_path)
    os.remove(dataset_path / "data.zip")

