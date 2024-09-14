## Argilla Instance


### Quick Start


#### Set the .env file


#### Create Custom Users Config

Create a users file in the format shown in `users_template.yaml`.

For the pinned version of the server we use, the hashed passwords must be constructed using bcrypt,
as dictated in [this file](https://github.com/argilla-io/argilla-server/blob/6130c634506bc649a64d8461992946537ae287e1/src/argilla_server/contexts/accounts.py#L202).

Explicitly, this means do this:

```python
from passlib.context import CryptContext
_CRYPT_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")
pw = "my-password"
hashed = _CRYPT_CONTEXT.hash(pw)
```



#### Spin Up/Down

```zsh
docker compose up
```

On startup need to run:

```zsh
python -m argilla_server database users migrate
```

in the server shell.

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

