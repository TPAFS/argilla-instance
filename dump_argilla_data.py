import argilla as rg

# Load annotated dataset from the argilla server
ds_name = "case-outcomes"
workspace = "case-outcomes"
local_dataset = rg.FeedbackDataset.from_argilla(name=ds_name, workspace=workspace)

# Export argilla dataset to a datasets Dataset
dataset_ds = local_dataset.format_as("datasets")
dataset_ds.to_json(f"./data/annotated/{ds_name}.jsonl")
