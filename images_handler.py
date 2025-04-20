import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

class CloudflareR2Handler:
    def __init__(self, access_key, secret_key, bucket_name, endpoint_url):
        """
        Initialize the Cloudflare R2 handler.

        :param access_key: Your R2 access key
        :param secret_key: Your R2 secret key
        :param bucket_name: The name of your R2 bucket
        :param endpoint_url: The endpoint URL for your R2 storage
        """
        self.bucket_name = bucket_name
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint_url
        )

    def upload_image(self, file_obj, object_name):
        """
        Upload an image to Cloudflare R2.

        :param file_path: Path to the image file on the local system
        :param object_name: The name of the object in the R2 bucket
        :return: URL of the uploaded image or None if upload fails
        """
        try:
            self.s3_client.upload_fileobj(file_obj, self.bucket_name, object_name)
            return f"{self.s3_client.meta.endpoint_url}/{self.bucket_name}/{object_name}"
        except FileNotFoundError:
            print("The file was not found.")
        except NoCredentialsError:
            print("Credentials not available.")
        except PartialCredentialsError:
            print("Incomplete credentials provided.")
        except Exception as e:
            print(f"An error occurred: {e}")
        return None

    def retrieve_image(self, object_name, download_path):
        """
        Retrieve an image from Cloudflare R2.

        :param object_name: The name of the object in the R2 bucket
        :param download_path: Path to save the downloaded image locally
        :return: True if download succeeds, False otherwise
        """
        try:
            self.s3_client.download_file(self.bucket_name, object_name, download_path)
            return True
        except FileNotFoundError:
            print("The specified download path is invalid.")
        except NoCredentialsError:
            print("Credentials not available.")
        except PartialCredentialsError:
            print("Incomplete credentials provided.")
        except Exception as e:
            print(f"An error occurred: {e}")
        return False
    
    def generate_presigned_url(self, object_name, expiration=3600):
        """
        Generate a pre-signed URL for an object in Cloudflare R2.

        :param object_name: The name of the object in the R2 bucket
        :param expiration: Time in seconds for the URL to remain valid (default: 1 hour)
        :return: Pre-signed URL or None if generation fails
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_name},
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            print(f"An error occurred while generating pre-signed URL: {e}")
            return None