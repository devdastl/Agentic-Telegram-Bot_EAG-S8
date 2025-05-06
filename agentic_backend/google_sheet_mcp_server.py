#!/usr/bin/env python
"""
Google Spreadsheet MCP Server
A Model Context Protocol (MCP) server built with FastMCP for interacting with Google Sheets.
"""

import base64
import os
from typing import List, Dict, Any, Optional
import json
from mcp.server import FastMCP
from mcp.types import TextContent

# Google API imports
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from models import ShareSheetInput, CreateSheetInput, SpreadsheetOutput, ErrorResponse

# Constants
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
FETCH_CREDS = False

def get_gsheet_service(creds_file_path: str = "credentials/credentials.json", token_path: str = "credentials/token.json"):
    """Get Google Sheets and Drive service instances using the same credentials as Gmail"""
    creds = None
    
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
                raise RuntimeError("Google API token not found or expired. Run setup manually.")
    
    try:
        # Build the services
        sheets_service = build('sheets', 'v4', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)
        return sheets_service, drive_service
    except Exception as e:
        print(f'An error occurred: {e}')
        return None, None

# Initialize the MCP server
mcp = FastMCP("Google Sheets")
mcp.state = {}  # Initialize the state dictionary

@mcp.tool()
def create_blank_spreadsheet(input: CreateSheetInput) -> dict:
    """
    Create a new blank Google Spreadsheet with the specified title. This tools does not enter any data into the spreadsheet. Use the write_data_to_spreadsheet tool to enter data into the spreadsheet.
    
    Usage JSON format:
    {"function": "create_spreadsheet", "parameters": {"input": {"title": "My Spreadsheet"}}}
    """
    try:
        sheets_service = mcp.state.get('sheets_service')
        drive_service = mcp.state.get('drive_service')
        
        if not sheets_service or not drive_service:
            error = ErrorResponse(
                error_type="ServiceError",
                message="Google Sheets service not initialized",
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
        
        # Create the spreadsheet
        spreadsheet_body = {
            'properties': {
                'title': input.title
            }
        }
        
        spreadsheet = sheets_service.spreadsheets().create(
            body=spreadsheet_body, 
            fields='spreadsheetId,properties,sheets'
        ).execute()
        
        spreadsheet_id = spreadsheet.get('spreadsheetId')
        
        # Create and validate output model
        output = SpreadsheetOutput(
            spreadsheet_id=spreadsheet_id,
            title=spreadsheet.get('properties', {}).get('title', input.title),
            sheets=[sheet.get('properties', {}).get('title', 'Sheet1') for sheet in spreadsheet.get('sheets', [])],
            url=f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
        )
        
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
        print(f"Error creating spreadsheet: {str(e)}")
        error = ErrorResponse(
            error_type="SpreadsheetError",
            message=f"Failed to create spreadsheet: {str(e)}",
            details={
                "service_available": bool(mcp.state.get('sheets_service')),
                "title": input.title
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

@mcp.tool()
def write_data_to_spreadsheet(input: Dict[str, Any]) -> dict:
    """
    Enters the data into cells in a Google Spreadsheet with the provided data.
    
    Usage JSON format:
    {"function": "update_sheet_data", "parameters": {"input": {"spreadsheet_id": "1ABC...", "sheet": "Sheet1", "data": [["Header1", "Header2"], ["Value1", "Value2"]]}}}
    """
    try:
        sheets_service = mcp.state.get('sheets_service')
        
        if not sheets_service:
            error = ErrorResponse(
                error_type="ServiceError",
                message="Google Sheets service not initialized",
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
        
        spreadsheet_id = input.get("spreadsheet_id")
        sheet = input.get("sheet", "Sheet1")
        data = input.get("data", [])
        
        if not spreadsheet_id:
            raise ValueError("spreadsheet_id is required")
        
        if not data:
            raise ValueError("data cannot be empty")
        
        # Determine the range based on data dimensions
        rows = len(data)
        cols = max(len(row) for row in data) if rows > 0 else 0
        end_col = chr(ord('A') + cols - 1) if cols > 0 else 'A'
        range_str = f"{sheet}!A1:{end_col}{rows}"
        
        # Prepare the value range body
        value_range_body = {
            'values': data
        }
        
        # Update the values
        result = sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_str,
            valueInputOption='USER_ENTERED',
            body=value_range_body
        ).execute()
        
        # Create output with the result
        output = {
            "spreadsheet_id": spreadsheet_id,
            "sheet": sheet,
            "updated_range": result.get("updatedRange", ""),
            "updated_rows": result.get("updatedRows", 0),
            "updated_columns": result.get("updatedColumns", 0),
            "updated_cells": result.get("updatedCells", 0),
            "url": f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
        }
        
        json_response = json.dumps(output)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json_response
                }
            ]
        }
        
    except Exception as e:
        print(f"Error updating spreadsheet: {str(e)}")
        error = ErrorResponse(
            error_type="SpreadsheetError",
            message=f"Failed to update spreadsheet: {str(e)}",
            details={
                "service_available": bool(mcp.state.get('sheets_service')),
                "spreadsheet_id": input.get("spreadsheet_id", "Unknown")
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

# @mcp.tool()
# def share_spreadsheet(input: ShareSheetInput) -> dict:
#     """
#     Share a Google Spreadsheet with multiple users via email.
    
#     Usage JSON format:
#     {"function": "share_spreadsheet", "parameters": {"input": {"spreadsheet_id": "1ABC...", "email": "user@example.com", "role": "reader"}}}
#     """
#     try:
#         drive_service = mcp.state.get('drive_service')
        
#         if not drive_service:
#             error = ErrorResponse(
#                 error_type="ServiceError",
#                 message="Google Drive service not initialized",
#                 details={"service_available": False}
#             )
#             error_json = error.model_dump_json()
#             return {
#                 "content": [
#                     {
#                         "type": "text",
#                         "text": error_json
#                     }
#                 ]
#             }
        
#         # Create the permission
#         permission = {
#             'type': 'user',
#             'role': input.role,
#             'emailAddress': input.email
#         }
        
#         # Share the spreadsheet
#         result = drive_service.permissions().create(
#             fileId=input.spreadsheet_id,
#             body=permission,
#             sendNotificationEmail=input.send_notification,
#             fields='id'
#         ).execute()
        
#         # Create output with the result
#         output = {
#             "spreadsheet_id": input.spreadsheet_id,
#             "email": input.email,
#             "role": input.role,
#             "success": True,
#             "permission_id": result.get('id'),
#             "url": f"https://docs.google.com/spreadsheets/d/{input.spreadsheet_id}/edit"
#         }
        
#         json_response = json.dumps(output)
        
#         return {
#             "content": [
#                 {
#                     "type": "text",
#                     "text": json_response
#                 }
#             ]
#         }
        
#     except Exception as e:
#         print(f"Error sharing spreadsheet: {str(e)}")
#         error = ErrorResponse(
#             error_type="SharingError",
#             message=f"Failed to share spreadsheet: {str(e)}",
#             details={
#                 "service_available": bool(mcp.state.get('drive_service')),
#                 "spreadsheet_id": input.spreadsheet_id,
#                 "email": input.email
#             }
#         )
#         error_json = error.model_dump_json()
#         return {
#             "content": [
#                 {
#                     "type": "text",
#                     "text": error_json
#                 }
#             ]
#         }

@mcp.tool()
def get_spreadsheet_link(input: Dict[str, Any]) -> dict:
    """
    Get a shareable link for a Google Spreadsheet.
    
    Usage JSON format:
    {"function": "get_spreadsheet_link", "parameters": {"input": {"spreadsheet_id": "1ABC..."}}}
    """
    try:
        drive_service = mcp.state.get('drive_service')
        
        if not drive_service:
            error = ErrorResponse(
                error_type="ServiceError",
                message="Google Drive service not initialized",
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
        
        spreadsheet_id = input.get("spreadsheet_id")
        
        if not spreadsheet_id:
            raise ValueError("spreadsheet_id is required")
        
        # Get the file metadata
        file = drive_service.files().get(
            fileId=spreadsheet_id,
            fields='name,webViewLink'
        ).execute()
        
        # Create output with the result
        output = {
            "spreadsheet_id": spreadsheet_id,
            "title": file.get('name', 'Unknown'),
            "url": file.get('webViewLink', f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
        }
        
        json_response = json.dumps(output)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json_response
                }
            ]
        }
        
    except Exception as e:
        print(f"Error getting spreadsheet link: {str(e)}")
        error = ErrorResponse(
            error_type="LinkError",
            message=f"Failed to get spreadsheet link: {str(e)}",
            details={
                "service_available": bool(mcp.state.get('drive_service')),
                "spreadsheet_id": input.get("spreadsheet_id", "Unknown")
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
    print("Starting Google Sheets service...")
    # Initialize Google Sheets and Drive services
    sheets_service, drive_service = get_gsheet_service()
    if sheets_service and drive_service:
        mcp.state['sheets_service'] = sheets_service
        mcp.state['drive_service'] = drive_service
        print("Google Sheets and Drive services initialized successfully")
    else:
        print("Failed to initialize Google Sheets and Drive services")

    # Run with explicit stdio transport
    mcp.run(transport="stdio") 