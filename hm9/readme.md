## Description
One worker per one app type. Using multiprocessing. In memcache using method setting multiply keys

## Run
First step it's install requirements
```commandline
cd hm9
pip install -r requirements.txt 
```
### Run base script version
```commandline
python3 memc_load.py --pattern=*.tsv.gz
```
Some flags: <br/>
-t                  # run protobuf test <br/>
-l                  # path to log file <br/>
--dry               # debug mode <br/>
--pattern           # pattern for searching log files <br/>
--idfa              # address of idfa memcache server <br/>
--gaid              # address of idfa memcache server <br/>
--adid              # address of idfa memcache server <br/>
--dvid              # address of idfa memcache server <br/>
### Run multiprocessing script version
```commandline
python3 memc_load_multiprocessing.py --pattern=*.tsv.gz
```
#### Warning
dry flag in base script version renamed to dry_run in this version