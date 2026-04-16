import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as Oauth2Credentials
from google.auth.external_account_authorized_user import Credentials as AuthorizedUserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send"
]
CREDENTIALS = None


def _start_api() -> AuthorizedUserCredentials | Oauth2Credentials | None:
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("/app/token.json"):
        creds = Oauth2Credentials.from_authorized_user_file("/app/token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("/app/credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("/app/token.json", "w") as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)
        results = service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])

        if not labels:
            print("No labels found.")
            return None
        
        print("Labels:")
        
        for label in labels:
            print(label["name"])

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(error)

    return creds

def send_message(from_addr:str, to_addr:str|list[str], cc_addr:str|list[str], bcc_addr:str|list[str], subject:str, body:str):
    while not CREDENTIALS:
        _start_api()

    try:
        service = build("gmail", "v1", credentials=CREDENTIALS)
        message = MIMEMultipart()
        message.attach(MIMEText(body, 'plain'))

        message["To"] = to_addr if isinstance(to_addr, (str, type(None))) else ','.join(to_addr)
        message["Cc"] = cc_addr if isinstance(cc_addr, (str, type(None))) else ','.join(cc_addr)
        message["Bcc"] = bcc_addr if isinstance(bcc_addr, (str, type(None))) else ','.join(bcc_addr)
        message["From"] = from_addr
        message["Subject"] = subject

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {"raw": encoded_message}
        # pylint: disable=E1101
        send_message = (
            service.users()
                .messages()
                .send(userId="me", body=create_message)
                .execute()
        )
    except HttpError as error:
        send_message = None
    return send_message