from enum import Enum
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader


class FileEnums(Enum):
    PDF  = (".pdf",  PyPDFLoader)
    DOCX = (".docx", Docx2txtLoader)
    DOC  = (".doc",  Docx2txtLoader)
    TXT  = (".txt",  TextLoader)

    def __init__(self, extension: str, loader_class):
        self.extension = extension
        self.loader_class = loader_class

    @classmethod
    def from_extension(cls, ext: str):
        for member in cls:
            if member.extension == ext:
                return member
        return None