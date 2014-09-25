
1. Config Client ID and Client Secret on cleaner.py

  # Copy your credentials from the APIs Console
  CLIENT_ID = 'YOUR_CLIENT_ID'
  CLIENT_SECRET = 'YOUR_CLIENT_SECRET'


2. Config python environment

source bin/activate


3. Usage:

Search zombie files on qblinks.com GDrive:
python cleaner.py -d qblinks.com

Search files shared to xxxx@gmail.com:
python cleaner.py -s xxxx@gmail.com

