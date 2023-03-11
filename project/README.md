# Usage (README was part of original project)

## Front-end setup

`cd frontend`

`yarn add --dev yarn-upgrade-all`

`yarn yarn-upgrade-all`

`yarn install`

`yarn start`

## Back-end setup

Requires-Python `>=3.7`, `<3,11`

`cd backend`

`pip install -r requirements.txt`

`python app.py` or `python3 app.py`

## API document

`http://localhost:5000/`

## Unit Testing

Start backend first, then in another terminal run either of the following:

### - to test regular functions

`python3 ./tests/unit/test_backend.py`

### - to test recommender system

`python3 ./tests/unit/test_recommender.py`
