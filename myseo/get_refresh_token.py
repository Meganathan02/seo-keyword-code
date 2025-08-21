from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
import os

load_dotenv()
path = os.getenv("GOOGLE_ADS_CLIENT_TOKEN_PATH")
scopes = ["https://www.googleapis.com/auth/adwords"]

flow = InstalledAppFlow.from_client_secrets_file(path, scopes=scopes)
creds = flow.run_local_server(open_browser=True)
print("Refresh Token:", creds.refresh_token)
