## Keyword Planner Code

## To run 

create any env 

next step

check `.env.example` using that create `.env`

requirements
- google cloud api (client_secret.json / client_id and client_secret)
- google ads api 

`Note Enable ads api`

### google ads api requirements 

```
1. Customer ID is in (MCC ACCOUNT)
2. Developer Token 

Note Developer Token should be from Active Manager Account, latest Customer ID and Developer Token should have basic access from test access 
```


```bash
pip install poetry
poetry install
```

to run code 

1. Get refresh token by running 

```bash
python myseo/get_refresh_token.py
```

2. Copy paste refresh token in env `eg 1//0gKDQZt45v5G...`

```bash
python myseo/seo.py
```
3. Check the new CSV file 