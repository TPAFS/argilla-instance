## Argilla Instance


### Quick Start


#### Set the .env file

Make a copy of the `.env_template` file in the top level of this repo, name it `.env`, and populate the `ARGILLA_AUTH_SECRET_KEY`
var with a secret key.


#### Create Custom Users Config

Create a users file in the format shown in `users_template.yaml`. Place this file in the top level of the repo, and name it `.users.yaml`.

For the pinned version of the server we use, the hashed passwords must be constructed using bcrypt,
as dictated in [this file](https://github.com/argilla-io/argilla-server/blob/6130c634506bc649a64d8461992946537ae287e1/src/argilla_server/contexts/accounts.py#L202).

Explicitly, this means do the following to construct the hashed value of the password:

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

On startup one needs to exec into argilla server container:


```zsh
docker exec -it argilla-instance-argilla-1 /bin/sh
```

and then run:

```zsh
python -m argilla_server database users migrate
```

from within the server shell. This will create the users specified in the users yaml.

Spin down:

```zsh
docker compose down
```


#### Dump Annotated Sets


```zsh
python dump_argilla_data.py --dataset='your-dataset-name' --workspace='your-workspace-name' --outpath='./path/to/your/desired/outfile.jsonl'
```


#### Combine Dumped Sets and Export to SQUAD format


```zsh
python extract_and_merge_annotated.py --annotated_jsonl_paths './path/to/your/first/argilla/dump.jsonl' './path/to/your/second/argilla/dump.jsonl' --outpath './path/to/your/desired/outfile.json'
```