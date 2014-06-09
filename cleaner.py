import httplib2
import pprint
import sys

from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow, OAuth2Credentials


class DriveUtility():

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

  # List and prompt if want to move orphaned files to a new directory
  def moveOrphanedFiles(self):

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

  # find directories which is not in domain
  def findNotInDomain(self, domain):

    keep_going = True
    next_token = None
    users = []

    while keep_going:

      self.requests += 1
      print ('Making request ' + str(self.requests))

      #f = self.drive.files().list(maxResults = 1000, pageToken = next_token).execute()
      f = self.drive.files().list(maxResults = 1000, pageToken = next_token, q = "mimeType = 'application/vnd.google-apps.folder'").execute()
      try:
        next_token = f['nextPageToken']
      except KeyError:
        next_token = None
        keep_going = False

      self.total += len(f['items'])
      for item in f['items']:
        try:
          permission = self.drive.permissions().list(fileId = item['id']).execute()['items']
          for p in permission:
            user = {'id': p['id'], 'name': None}
            if 'name' in p:
              user['name'] = p['name']
            if 'domain' in p and p['domain'] != domain and user not in users:
              users.append(user)
            if 'domain' not in p and user not in users:
              users.append(user)
        except:
          print "Error processing file '" + item['title'] + "', will pass it."

      pprint.pprint(users)
      print(str(len(users)) + " users.")

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
            print (item['title'] + ', id: ' + item['id'])
            try:
              self.orphaned.append({'id': item['id'], 'title': item['title']})
            except:
              print ('\t\t>>> ERROR TRASHING THIS FILE <<<')
              self.errors += 1

  # List folers/files which are share to an specified Email address.
  def searchShareTo(self, email):

    keep_going = True
    next_token = None

    while keep_going:

      self.requests += 1
      print ('Making request ' + str(self.requests))

      f = self.drive.files().list(maxResults = 1000, pageToken = next_token, q = "'" + email + "' in writers or '" + email + "' in readers").execute()
      try:
        next_token = f['nextPageToken']
      except KeyError:
        next_token = None
        keep_going = False

      self.total += len(f['items'])
      self.processItems(f['items'])

      for item in f['items']:
        title = "\t" + item['title']
        if(item['mimeType'] == 'application/vnd.google-apps.folder'):
          title = '[DIR]' + title
        title = title + ', id: ' + item['id']
        print(title)

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

  # get argv
  if len(sys.argv) == 1:
    print('Usage: ' + sys.argv[0] + ' [options...]')
    print('Options:')
    print(' -o, --orphane \t\tList orphaned files and prompt if want to move them to a new directory.')
    print(' -s, --shareto EMAIL \tList files which are shared to an Email address.')
    print(' -d, --domain DOMAIN \tList users which are not in domain.')
    return
  else:
    if sys.argv[1] not in ['-o', '--orphane', '-s', '--shareto', '-d', '--domain']:
      print('Error: no such option.')
      return
    else:
      if sys.argv[1] in ['-s', '--shareto'] and len(sys.argv) == 2:
        print('Error: Missing EMAIL parameter.')
        return
      else:
        if sys.argv[1] in ['-d', '--domain'] and len(sys.argv) == 2:
          print('Error: Missing DOMAIN parameter.')
          return

  # Copy your credentials from the APIs Console
  CLIENT_ID = 'YOUR_CLIENT_ID'
  CLIENT_SECRET = 'YOUR_CLIENT_SECRET'

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

  # Create driveutility and run it
  du = DriveUtility(drive_service)
  if sys.argv[1] == '-o':
    du.findNewDir()
    du.getNewDir()
    du.moveOrphanedFiles()

  if sys.argv[1] in ['-s', '--shareto']:
    if sys.argv[2]:
      du.searchShareTo(email = sys.argv[2])
    else:
      print('Error: Missing EMAIL parameter.')

  if sys.argv[1] in ['-d', '--domain']:
    if sys.argv[2]:
      du.findNotInDomain(domain = sys.argv[2])
    else:
      print('Error: Missing DOMAIN parameter.')

# intialize global utiltiy classes and call main
pp = pprint.PrettyPrinter()
main()
