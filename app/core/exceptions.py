from fastapi import HTTPException, status


class DocumentProcessingError(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class UnsupportedFileTypeError(HTTPException):
    def __init__(self, file_type: str) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_type}. Supported: pdf, txt, md",
        )


class FileTooLargeError(HTTPException):
    def __init__(self, max_mb: int) -> None:
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {max_mb}MB",
        )
