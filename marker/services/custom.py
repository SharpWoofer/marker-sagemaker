import base64
import json
import time
from io import BytesIO
from typing import List, Annotated, Union, T

import PIL
from PIL import Image
from pydantic import BaseModel
import boto3
from dotenv import load_dotenv
import os
import logging

from marker.schema.blocks import Block
from marker.services import BaseService

class SagemakerService(BaseService):
    load_dotenv()
    # aws_access_key_id: Annotated[
    #     str,
    #     "The AWS access key ID."
    # ] = os.environ.get("SAGEMAKER_AWS_ACCESS_KEY_ID")
    # aws_secret_access_key: Annotated[
    #     str,
    #     "The AWS secret access key."
    # ] = os.environ.get("SAGEMAKER_AWS_SECRET_ACCESS_KEY")
    region_name: Annotated[
        str,
        "The AWS region name."
    ] = "ap-southeast-1"
    endpoint_name: Annotated[
        str,
        "The SageMaker endpoint name to use."
    ] = "Qwen2-5-VL-72B-Instruct-2025-03-09-10-43-09"
    max_tokens: Annotated[
        int,
        "The maximum number of tokens to use for a single request."
    ] = 4096

    _client = None

    def img_to_base64(self, img: PIL.Image.Image):
        image_bytes = BytesIO()
        img.save(image_bytes, format="JPEG")
        return base64.b64encode(image_bytes.getvalue()).decode('utf-8')

    def prepare_images(self, images: Union[Image.Image, List[Image.Image]]) -> List[dict]:
        if isinstance(images, Image.Image):
            images = [images]

        return [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{self.img_to_base64(img)}"
                }
            }
            for img in images
        ]

    def validate_response(self, response_text: str, schema: type[T]) -> T:
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        try:
            # Try to parse as JSON first
            out_schema = schema.model_validate_json(response_text)
            out_json = out_schema.model_dump()
            return out_json
        except Exception as e:
            try:
                # Re-parse with fixed escapes
                escaped_str = response_text.replace('\\', '\\\\')
                out_schema = schema.model_validate_json(escaped_str)
                return out_schema.model_dump()
            except Exception as e:
                logging.error(f"JSON validation error: {e}")
                return None

    def get_client(self):
        if self._client is None:
            logging.info(f"Initializing Boto3 SageMaker runtime client for region {self.region_name}...")
            # When running in SageMaker, boto3 will automatically use the endpoint's IAM execution role for credentials.
            # No keys are needed.
            session = boto3.Session(region_name=self.region_name)
            self._client = session.client('sagemaker-runtime')
            logging.info("Boto3 client initialized.")
        return self._client

    def __call__(
            self,
            prompt: str,
            image: PIL.Image.Image | List[PIL.Image.Image],
            block: Block,
            response_schema: type[BaseModel],
            max_retries: int | None = None,
            timeout: int | None = None
    ):
        if max_retries is None:
            max_retries = self.max_retries

        if timeout is None:
            timeout = self.timeout

        if not isinstance(image, list):
            image = [image]

        schema_example = response_schema.model_json_schema()
        system_prompt = f"""
Follow the instructions given by the user prompt. You must provide your response in JSON format matching this schema:

{json.dumps(schema_example, indent=2)}

Respond only with the JSON schema, nothing else. Do not include ```json, ```, or any other formatting.
""".strip()

        client = self.get_client()
        image_data = self.prepare_images(image)

        messages = [
            {
                "role": "system", 
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    *image_data
                ]
            }
        ]

        payload = {
            "messages": messages,
            "max_tokens": self.max_tokens
        }

        tries = 0
        while tries < max_retries:
            try:
                logging.info("Sending request to Sagemaker endpoint...")
                payload_json = json.dumps(payload)
                
                response = client.invoke_endpoint(
                    EndpointName=self.endpoint_name,
                    ContentType='application/json',
                    Body=payload_json
                )

                # Parse response
                response_body = response['Body'].read().decode('utf-8')
                logging.info("I am using custom.py file")
                output = json.loads(response_body)
                response_text = output["choices"][0]["message"]["content"]
                
                validated_response = self.validate_response(response_text, response_schema)
                if validated_response:
                    return validated_response
                else:
                    logging.warning("Failed to validate response, retrying...")
                    tries += 1
                    time.sleep(tries * 2)
            except Exception as e:
                logging.error(f"Error calling SageMaker endpoint: {e}")
                tries += 1
                wait_time = tries * 3
                logging.info(f"Retrying in {wait_time} seconds... (Attempt {tries}/{max_retries})")
                time.sleep(wait_time)

        return {}