import argilla as rg

# load your annotated dataset from the Argilla web app
ds_name = "adjudication-spans"
dataset_rg = rg.load(ds_name)
local_dataset = dataset_rg.pull(max_records=100)

# export your Argilla Dataset to a datasets Dataset
dataset_ds = dataset_rg.format_as("datasets")
dataset_ds.to_json(f"{ds_name}.jsonl")
