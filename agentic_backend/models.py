from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union, Literal

# Input/Output models for tools

class AddInput(BaseModel):
    a: int
    b: int

class AddOutput(BaseModel):
    result: int

class SqrtInput(BaseModel):
    a: int

class SqrtOutput(BaseModel):
    result: float

class StringsToIntsInput(BaseModel):
    string: str

class StringsToIntsOutput(BaseModel):
    ascii_values: List[int]

class ExpSumInput(BaseModel):
    int_list: List[int] = Field(alias="numbers")

class ExpSumOutput(BaseModel):
    result: float

class PythonCodeInput(BaseModel):
    code: str

class PythonCodeOutput(BaseModel):
    result: str

class UrlInput(BaseModel):
    url: str

class FilePathInput(BaseModel):
    file_path: str

class MarkdownInput(BaseModel):
    text: str

class MarkdownOutput(BaseModel):
    markdown: str

class ChunkListOutput(BaseModel):
    chunks: List[str]

class ShellCommandInput(BaseModel):
    command: str

class SendEmailInput(BaseModel):
    """Input model for send_email tool"""
    to: str
    subject: str
    message: str

class SendEmailOutput(BaseModel):
    """Output model for send_email tool"""
    message_id: str

class ErrorResponse(BaseModel):
    """Model for error responses"""
    error_type: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)

# Google Sheets Models
class CreateSheetInput(BaseModel):
    """Input model for create_spreadsheet tool"""
    title: str

class SpreadsheetOutput(BaseModel):
    """Output model for spreadsheet operations"""
    spreadsheet_id: str
    title: str
    sheets: List[str]
    url: str

class ShareSheetInput(BaseModel):
    """Input model for share_spreadsheet tool"""
    spreadsheet_id: str
    email: str
    role: Literal["reader", "writer", "commenter"] = "reader"
    send_notification: bool = True


