from enum import Enum


class ResponseEnums(str, Enum):
    # General
    SUCCESS = "Success"
    ERROR = "Something went wrong"

    # File
    FILE_UPLOAD_SUCCESS = "File uploaded successfully"
    FILE_TYPE_NOT_SUPPORTED = "File type not supported"
    FILE_SIZE_TOO_LARGE = "File size too large"
    FILE_NOT_FOUND = "File not found"

    # Contract
    CONTRACT_PROCESSED = "Contract processed successfully"
    CONTRACT_NOT_FOUND = "Contract not found"
    CONTRACT_DELETED = "Contract deleted successfully"
    CONTRACT_LIST_EMPTY = "No contracts found"

    # Processing
    PROCESSING_STARTED = "Contract processing started"
    PROCESSING_FAILED = "Contract processing failed"

    # Query
    QUERY_SUCCESS = "Query answered successfully"

    # Report
    REPORT_GENERATED = "Report generated successfully"