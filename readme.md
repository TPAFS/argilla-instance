## Argilla Instance


### Quick Start

#### Spin Up/Down

```zsh
docker compose up
```

Spin down:

```zsh
docker compose down
```


#### Dump Annotated Sets


```zsh
python dump_argilla_data.py --dataset='your-dataset-name' --workspace='your-workspace-name' --outpath='./path/to/your/desired/outfile.json'
```


#### Combine Dumped Sets and Export to SQUAD format


```zsh
python extract_and_merge_annotated.py --annotated_jsonl_paths './path/to/your/first/argilla/dump.jsonl' './path/to/your/second/argilla/dump.jsonl' --outpath './path/to/your/desired/outfile.json'
```


<!-- TODO: Re-define dataset (with existing annotations), by splitting "Physician1 :", "Physician2" subsets from CA DMHC data.


TODO: Add question for physician users:

What is the correct outcome, assuming the facts presented in the background are accurate?
Uphold, Overturn, Too little info.
 -->