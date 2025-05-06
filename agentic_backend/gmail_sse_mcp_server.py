from mcp.server import FastMCP
from mcp.types import TextContent
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import base64
from email.mime.text import MIMEText
import argparse
import json
from models import SendEmailInput, SendEmailOutput, ErrorResponse

FETCH_CREDS = False

def get_gmail_service(creds_file_path: str = "credentials/credentials.json", token_path: str = "credentials/token.json"):
    """Get Gmail service instance"""
    creds = None
    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    SCOPES += ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not FETCH_CREDS:
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    creds_file_path, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
    else:
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                raise RuntimeError("Gmail token not found or expired. Run setup manually.")
    

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as e:
        print(f'An error occurred: {e}')
        return None

# Initialize the MCP server
mcp = FastMCP("Gmail")
mcp.state = {}  # Initialize the state dictionary


@mcp.tool()
def send_email(input: SendEmailInput) -> dict:
    """Send an email using Gmail API.
    
    Usage JSON format:
    {"function": "send_email", "parameters": {"input": {"to": "recipient@example.com", "subject": "Subject", "message": "Message"}}}
    """
    try:
        service = mcp.state.get('gmail_service')
        if not service:
            error = ErrorResponse(
                error_type="ServiceError",
                message="Gmail service not initialized",
                details={"service_available": False}
            )
            error_json = error.model_dump_json()
            return {
                "content": [
                    {
                        "type": "text",
                        "text": error_json
                    }
                ]
            }

        # Create message
        message = MIMEText(input.message, 'html')  # Set type to HTML
        message['to'] = input.to
        message['subject'] = input.subject

        # Encode the message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Send the email
        send_message = (service.users().messages().send(
            userId="me",
            body={'raw': encoded_message})
        ).execute()

        print(f"Email sent successfully. Message Id: {send_message['id']}")

        # Create and validate output model
        output = SendEmailOutput(message_id=send_message['id'])
        json_response = output.model_dump_json()
        
        # Return in MCP format with validated model data as JSON string
        return {
            "content": [
                {
                    "type": "text",
                    "text": json_response
                }
            ]
        }

    except Exception as e:
        print(f"Error sending email: {str(e)}")
        error = ErrorResponse(
            error_type="EmailError",
            message=f"Failed to send email: {str(e)}",
            details={
                "service_available": bool(mcp.state.get('gmail_service')),
                "to": input.to,
                "subject": input.subject
            }
        )
        error_json = error.model_dump_json()
        return {
            "content": [
                {
                    "type": "text",
                    "text": error_json
                }
            ]
        }


if __name__ == "__main__":
    print("Starting Gmail service...")
    # Initialize Gmail service
    service = get_gmail_service()
    if service:
        mcp.state['gmail_service'] = service
        print("Gmail service initialized successfully")
    else:
        print("Failed to initialize Gmail service")

    # Run with explicit stdio transport
    mcp.run(transport="stdio")