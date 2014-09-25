
1. Config Client ID and Client Secret on cleaner.py

  # Copy your credentials from the APIs Console
  CLIENT_ID = 'YOUR_CLIENT_ID'
  CLIENT_SECRET = 'YOUR_CLIENT_SECRET'


2. Config python environment

source bin/activate


3. Usage:

Search orphane files:
python cleaner.py -o

Search shared to users who are not from non-internal domain:
python cleaner.py -d qblinks.com

Search files shared to xxxx@gmail.com:
python cleaner.py -s xxxx@gmail.com

