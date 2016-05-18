# WEB QC Tool 

A tool to quickly quality control an arbitrary list of images using web browser for UI

## Command line arguments

* `--csv <file.csv` - provide file for storing information, existing QC information will be loaded on startup
* `--accept` - accept incoming connections from everywhere, by default only localhost connections are accepted
* `--port <n>` - specify a port to listen to, default is **8080**


## Using:
* Simplest case, load all jpeg files in the current directory, the output will be saved in qc_auto.csv file
  Use web browser at the location http://127.0.0.1:8080 and do QCing. 
  To save your results you have to press *Ctrl-C* in the terminal, the file will be saved at this stage
  ```
  wqt.py *.jpg 
  ```
* Using a csv file with list of files QC:
  ```
  wqt.py --csv list_of_files.csv
  ```
* Specify an csv file to save results and also provide list of files:
  ```
  wqt.py --csv qc.csv  *.jpg
  ```
* Use a public ip, accessible from everywhere **beware** of hackers - 
  you information will be open to anyone who have access to your machine over network:
  ```
  wqt.py --csv qc.csv --accept
  ```
* Launch qc tool on  a remote machine (where your files are actually located) and access it via SSH tunnel:
  Use web browser at the location http://127.0.0.1:8080 and do QCing 
  the qc.csv will be saved on remote machine
  ```
  ssh -t -L 8080:127.0.0.1:8080 your_compute_cluster.somewhere.com "wqt.py --csv qc.csv /your_mega_raid_disk/project/*/*/*.jpg" 
  ```
