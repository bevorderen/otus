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
## run tests: 
```
python tests/integration/test.py
python tests/unit/unit.py
python tests/integration/test_store.py
```