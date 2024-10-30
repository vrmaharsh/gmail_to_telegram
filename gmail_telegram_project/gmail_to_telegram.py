
import os
import pickle
import base64
import json
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import requests

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Telegram Bot Token and Chat ID (replace with your actual token and chat ID)
TELEGRAM_TOKEN = '8163570051:AAGhPwPp0xLhgg6XzAySq9Lg-sG7d_EepqI'
TELEGRAM_CHAT_ID = '942279686'


def authenticate_gmail():
    """Authenticate with Gmail and return the service object."""
    creds = None
    # Load credentials if they exist
    if os.path.exists('token.json'):
        with open('token.json', 'rb') as token:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If no valid credentials, initiate authentication flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save credentials for next time
        with open('token.json', 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)


def get_unread_emails(service):
    """Fetch unread emails."""
    results = service.users().messages().list(userId='me', labelIds=['UNREAD']).execute()
    messages = results.get('messages', [])
    emails = []
    for msg in messages:
        message = service.users().messages().get(userId='me', id=msg['id']).execute()
        emails.append(message)
    return emails


def send_to_telegram(subject, snippet):
    """Send message to Telegram chat."""
    text = f"*New Email*\n*Subject:* {subject}\n*Snippet:* {snippet}"
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': text,
        'parse_mode': 'Markdown'
    }
    requests.post(url, json=payload)


def main():
    service = authenticate_gmail()
    while True:
        unread_emails = get_unread_emails(service)
        for email in unread_emails:
            # Extract subject and snippet
            headers = email['payload']['headers']
            subject = next(header['value'] for header in headers if header['name'] == 'Subject')
            snippet = email['snippet']
            # Send to Telegram
            send_to_telegram(subject, snippet)
            # Mark email as read
            service.users().messages().modify(userId='me', id=email['id'], body={'removeLabelIds': ['UNREAD']}).execute()
        time.sleep(60)  # Check for new emails every 60 seconds


if __name__ == '__main__':
    main()
