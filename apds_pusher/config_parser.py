"""Parser for APDS pusher configuration files."""
from dataclasses import dataclass, fields
from typing import Any, Dict, List


class ParserException(Exception):
    """Base exception for the APDS pusher."""


class ExtraFieldError(ParserException):
    """Exception raised when an additional (unexpected) field is given."""


class MissingFieldError(ParserException):
    """Exception raised when missing a required field."""


class BlankValueError(ParserException):
    """Exception raised when the value for a field is blank."""


@dataclass
class Configuration:
    """Dataclass to hold configuration."""

    auth0_tenant: str
    client_id: str
    bodc_archive_url: str
    file_formats: List[str]
    archive_checker_frequency: int

    @classmethod
    def from_dict_validated(cls, data_dict: Dict[str, Any]) -> "Configuration":
        """Instantiate the class from a dictionary."""
        class_fields = {field.name for field in fields(cls)}
        data_fields = set(data_dict.keys())

        # check no additional fields
        extra_keys = data_fields - class_fields
        if extra_keys:
            raise ExtraFieldError(f"Unexpected fields given: {extra_keys}")

        # check no missing fields
        missing_keys = class_fields - data_fields
        if missing_keys:
            raise MissingFieldError(f"Missing expected fields: {missing_keys}")

        # check no blank values
        blank_fields = {key for key, value in data_dict.items() if not value}
        if blank_fields:
            raise BlankValueError(f"Blank values found for fields: {blank_fields}")

        return cls(**data_dict)
