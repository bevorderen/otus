## Run
First step it's install requirements
```commandline
cd hm14
pip install -r requirements.txt 
```
Run crawler
```commandline
python3 main.py
```
Some flags: <br/>
-l                  # path to log file <br/>
--dry_run               # debug mode <br/>
--download_interval # interval for request main page
--save_dir # place for storing results
--top_posts_limit # limit links from main page for download (can't be more than 30)
