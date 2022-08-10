Necessary run redis on localhost:6379 and install package:
```
pip3 install redis
pip 3 install mock
```
## run server: 
```
cd hm2
python api.py
```
## run test directory
```
export host="{host with redis}"
export host="{port with redis}"
python -m unittest discover tests.integration
python -m unittest discover tests.unit
```

## run tests ony by one: 
```
python tests/integration/test.py
python tests/unit/unit.py
python tests/integration/test_store.py
```