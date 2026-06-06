import sys
from types import TracebackType
from typing import Optional


class CustomException(Exception):
    """
    Custom exception class for the Medical RAG Application to capture detailed error messages including file name and line number.
    """

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        _, _, exc_tb = sys.exc_info()

        self.error_message = self.error_message_detail(message, original_error, exc_tb)
        super().__init__(self.error_message)

    @staticmethod
    def error_message_detail(
        message: str,
        original_error: Optional[Exception],
        exc_tb: Optional[TracebackType],
    ) -> str:
        """
        Formats a detailed error string containing the context, raw error, file, and line number.
        """
        file_name = "Unknown file"
        line_number = "Unknown line"

        if exc_tb:
            file_name = exc_tb.tb_frame.f_code.co_filename
            line_number = str(exc_tb.tb_lineno)

        error_details = f" | Error: {original_error}" if original_error else ""

        return f"{message}{error_details} | File: {file_name} | Line: {line_number}"

    def __str__(self) -> str:
        return self.error_message
