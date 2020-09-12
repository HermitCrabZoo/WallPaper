# AwesomeWallpaper
To download wallpaper automatically

## How to use:
  
  1. Download the AwesomeWallpaper.py script.
  2. run script with -d opt and take a param, which you want wallpapers to download.
```
$ python3 AwesomeWallpaper.py -d /yourDir
```
  3. run script with -h opt to show help info.
```
  usage: AwesomeWallpaper.py [-h] -d <dir> [-m {search,random,toplist,latest}]
                           [-q <query>] [-c {000,001,010,011,100,101,110,111}]
                           [-p {000,001,010,011,100,101,110,111}]
                           [-s {random,relevance,date_added,views,favorites,toplist}]
                           [-o {desc,asc}]
                           [-r [<resolution> [<resolution> ...]]] [-f <from>]
                           [-t <to>] [--timeout <timeout>] [--times <times>]
                           [--parallel {1,2,...,7,8}] [--limit <limit>]
                           [--user <user>] [--pwd <pwd>]
```

## Dependencies:
  
  This project depends on requests You can install the dependencies using the requirements.txt file and running
  ```
  $ pip3 install -r requirements.txt
  ```
