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


<!-- Examples to split (multiple physicians):

92f69b41-d229-4c45-b9f7-3c08b7e9c5b7
 -->