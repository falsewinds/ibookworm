import boto3
import os

class Repository:
    def __init__(self, id : str):
        # use boto3 to get data from DynamoDB repositories
        self.filepath = ""

    def is_available_by(self, member):
        return True
