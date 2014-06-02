import httplib2
import pprint
import sys

from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow, OAuth2Credentials


class DriveCleaner():

  def __init__(self, drive_service):
    self.drive = drive_service
    self.requests = 0
    self.total = 0
    self.trashed = 0
    self.orphaned = []
    self.new_dir = None
    self.errors = 0
    self.NEW_DIR_NAME = "Orphaned" # put orphaned files into this directory

  def __str__(self):
    return str(self.total) + ' processed so far, ' + str(len(self.orphaned)) + ' orphaned, ' + str(self.errors) + ' errors'


  def cleanFiles(self):

    keep_going = True
    next_token = None

    while keep_going:

      self.requests += 1
      print ('Making request ' + str(self.requests))

      f = self.drive.files().list(maxResults = 1000, pageToken = next_token).execute()
      try:
        next_token = f['nextPageToken']
      except KeyError:
        next_token = None
        keep_going = False

      self.total += len(f['items'])
      self.processItems(f['items'])

    print (str(self))
    if len(self.orphaned) > 0 and self.new_dir:
      do = raw_input('Move ' + str(len(self.orphaned)) + ' files to ' + self.NEW_DIR_NAME + ' (y/N)?: ').strip().upper()
      if do == "Y":
        for orphaned_file in self.orphaned:
          self.drive.files().update(fileId = orphaned_file['id'], body = {'parents': [ {'id': self.new_dir['id']} ]}).execute()


  def processItems(self, responseItemDict):

    for item in responseItemDict:

      # find items with no parents
      if len(item['parents']) == 0:

        # that belong only to the user
        if len(item['owners']) == 1 and item['owners'][0]['isAuthenticatedUser']:

          # ... check to see if already trashed
          if item['labels'] and item['labels']['trashed']:
            self.trashed += 1
            pass

          else:
            print (item['title'])
            try:
              self.orphaned.append({'id': item['id'], 'title': item['title']})
            except:
              print ('\t\t>>> ERROR TRASHING THIS FILE <<<')
              self.errors += 1

  def findNewDir(self):
    f = self.drive.files().list(q = "title = '" + self.NEW_DIR_NAME + "'").execute()
    if len(f['items']) > 0:
      self.new_dir = f['items'][0]

  def getNewDir(self):
    if self.new_dir:
      print("[ \033[1;32mOK\033[0m ] " + self.NEW_DIR_NAME + " dir found.")
    else:
      print("[ \033[1;31mFAIL\033[0m ] New dir NOT FOUND! You must create a folder named \033[1;31m" + self.NEW_DIR_NAME + "\033[0m.")

def main():

  # Copy your credentials from the APIs Console
  CLIENT_ID = '183836539565-8qsra0qme8o5okdmlm1ukb4vlg2fscai.apps.googleusercontent.com'
  CLIENT_SECRET = 'p83uoyTtiR0XmO_I6oCqrliY'

  # Check https://developers.google.com/drive/scopes for all available scopes
  OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'

  # Redirect URI for installed apps
  REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

  # Run through the OAuth flow and retrieve credentials
  flow = OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET, OAUTH_SCOPE, REDIRECT_URI)
  authorize_url = flow.step1_get_authorize_url()
  print ('Go to the following link in your browser: ' + authorize_url)
  code = raw_input('Enter verification code: ').strip()
  credentials = flow.step2_exchange(code)

  # Create an httplib2.Http object and authorize it with our credentials
  http = httplib2.Http()
  http = credentials.authorize(http)
  drive_service = build('drive', 'v2', http=http)

  # Create drivecleaner and run it
  dc = DriveCleaner(drive_service)
  dc.findNewDir()
  dc.getNewDir()
  dc.cleanFiles()


# intialize global utiltiy classes and call main
pp = pprint.PrettyPrinter()
main()
