from enum import Enum


class ContractEnums(str, Enum):
    EMPLOYMENT = "employment"
    RENTAL = "rental"
    FREELANCE = "freelance"
    NDA = "nda"
    OTHER = "other"