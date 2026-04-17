from contextlib import asynccontextmanager
from typing import AsyncGenerator

from aiobotocore.session import get_session
from aiobotocore.client import AioBaseClient
from app.core.config import settings

S3_CONFIG = {
    "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
    "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
    "endpoint_url": settings.ENDPOINT_URL,
    "region_name": settings.REGION_NAME
}

class S3Client:
    def __init__(self, aws_access_key_id: str, aws_secret_access_key: str, endpoint_url: str, region_name: str):
        self.session = get_session()
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.endpoint_url = endpoint_url
        self.region_name = region_name
        
    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[AioBaseClient, None]:
        async with self.session.create_client(
            service_name="s3",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            endpoint_url=self.endpoint_url,
            region_name = self.region_name,
            verify=False, # TODO: поменять в проде
        ) as client:
            yield client
            
    async def put_data(self, bucket: str, key: str, data: bytes):
        async with self.get_client() as client:
            resp = await client.put_object(
                Bucket=bucket,
                Key=key,
                Body=data
            )
            print(resp)
            
    async def generate_presigned_url_put(self, bucket: str, key: str, expires: int):
        async with self.get_client() as client:
            url = await client.generate_presigned_url(
                'put_object',
                Params={"Bucket": bucket, 'Key': key},
                ExpiresIn=expires
            )
            return url
        
    
    async def check_exists_obj(self, bucket: str, key: str):
        async with self.get_client() as client:
            try:
                response = await client.head_object(
                    Bucket=bucket,
                    Key=key
                )
                return response
            except Exception as e:
                if hasattr(e, "response") and e.response['Error']['Code'] == "404":
                    return None
                else:
                    # Handle other potential errors (e.g., 403 Forbidden)
                    raise e