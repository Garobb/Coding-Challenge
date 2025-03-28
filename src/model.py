import os
from abc import abstractmethod
from dyntastic import Dyntastic
from pydantic import BaseModel, Field, validator
from typing import Optional
from decimal import Decimal
from enum import Enum
import boto3


class DynamoDbModelBase(Dyntastic):
    __table_region__ = os.environ.get("AWS_REGION")
    __table_host__ = os.environ.get("DYNAMO_ENDPOINT")
    __hash_key__ = "hash_key"
    __range_key__ = "range_key"

    @property
    @abstractmethod
    def __table_name__(self):  # over-ride this on each implementing class
        pass

    hash_key: str = Field(default=None, title="DynamoDB Partition Key")
    range_key: str = Field(default=None, title="DynamoDB Sort Key")


"""TODO
Architect a data structure for storing user's recurring orders. Two tables have already been setup for you,
User and RecurringOrder. It is up to you how you want to structure the data, so feel free to use both tables
or only one based on your strategy.

Don't forget to checkout the full requirements in the README or in api.py as those will pertain relevant information that
will apply to this file.
"""


class UserInfo(BaseModel):
    first_name: str
    last_name: str

class User(DynamoDbModelBase):
    __table_name__ = "User"
    hash_key = str
    info: Optional[UserInfo]


# Relevant

class AssetType(str, Enum):
    BTC = "BTC"
    ETH = "ETH"

class Frequency(str, Enum):
    DAILY = "DAILY"
    BIMONTHLY = "BIMONTHLY"

class Currency(str, Enum):
    USD = "USD"
    
class RecurringOrder(DynamoDbModelBase):
    __table_name__ = "RecurringOrder"
    __dynamodb__ = boto3.resource("dynamodb", 
        region_name=os.environ.get("AWS_REGION"),
        endpoint_url=os.environ.get("DYNAMO_ENDPOINT"),  
        aws_access_key_id="dummy",
        aws_secret_access_key="dummy",
    )
    __boto_table__ = __dynamodb__.Table(__table_name__)

    hash_key: str # user_id
    range_key: str # Frequency:AssetType
    currency: Currency
    currency_amount: Decimal

    @validator("currency_amount")
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Currency amount must be greater than 0")
        return v

    @validator("range_key")
    def validate_range_key(cls, v):
        freq, asset = v.split(":")
        if freq not in Frequency.__members__:
            raise ValueError(f"Frequency must be one of {','.join(e.value for e in Frequency)}")
        if asset not in AssetType.__members__:
            raise ValueError(f"Asset must be one of {','.join(e.value for e in AssetType)}")
        return v

    def save(self): # Overriding the default save
        item = self.dict()
        try:
            self.__boto_table__.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(hash_key) AND attribute_not_exists(range_key)",
            )
        except Exception as e:
            # This could be made better
            raise ValueError("Recurring order already exists") from e