import argparse
import os

import argilla as rg

ARGILLA_API_URL = os.environ.get("ARGILLA_API_URL", "http://localhost:6900")
ARGILLA_API_KEY = os.environ.get("ARGILLA_API_KEY", "argilla.apikey")


def main(dataset: str, workspace: str, outpath: str | None) -> None:
    rg.init(api_url=ARGILLA_API_URL, api_key=ARGILLA_API_KEY)

    # Load an annotated dataset from the argilla server
    local_dataset = rg.FeedbackDataset.from_argilla(name=dataset, workspace=workspace)

    # Export argilla dataset to a (huggingface) datasets Dataset
    dataset_ds = local_dataset.format_as("datasets")

    # Dump that to json on disk
    if outpath is None:
        outpath = f"./data/annotated/{dataset}.jsonl"

    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    dataset_ds.to_json(outpath)

    return None


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        type=str,
        default="case-summaries",
        help="Name of argilla dataset to dump.",
    )
    parser.add_argument(
        "--workspace",
        type=str,
        default="case-summaries",
        help="Name of workspace for dataset",
    )
    parser.add_argument(
        "--outpath",
        type=str,
        default=None,
        help="Optional output path.",
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    args_dict = vars(args)
    main(**args_dict)
