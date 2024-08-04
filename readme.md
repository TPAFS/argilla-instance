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

Dump json:

```zsh
python dump_argilla_data.py --dataset='your-dataset-name' --workspace='your-workspace-name' --outpath='./path/to/your/desired/outfile.json'
```


#### Combine Dumped Sets and Export to SQUAD format


```zsh
python extract_and_merge_annotated.py --annotated_jsonl_paths './path/to/your/first/argilla/dump.jsonl' './path/to/your/second/argilla/dump.jsonl' --outpath './path/to/your/desired/outfile.json'
```