from enum import Enum


class ErrorMessages(Enum):
    ID_INVALID = "id should be in integer."
    EMBEDDING_PROCESS_FAILURE = "EMBEDDING FAILED: {reason}"