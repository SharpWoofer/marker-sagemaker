import base64
import io
from io import BytesIO
import httpx
import json
import logging
from typing import Optional, List, Annotated
import PIL
import boto3
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from marker.services import BaseService
from marker.schema.blocks import Block

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # This will reset any existing logging configuration
)

import base64
import json
import time
import requests
from io import BytesIO
from typing import List, Annotated, Union, T

import PIL
from PIL import Image
from pydantic import BaseModel

from marker.schema.blocks import Block
from marker.services import BaseService

class OpenRouterService(BaseService):
    # openrouter_api_key: Annotated[
    #     str,
    #     "The OpenRouter API key to use for the service."
    # ] = None
    # site_url: Annotated[
    #     str,
    #     "The site URL for rankings on openrouter.ai."
    # ] = "https://yoursite.com"
    # site_name: Annotated[
    #     str,
    #     "The site name for rankings on openrouter.ai."
    # ] = "Your Application"
    # model_name: Annotated[
    #     str,
    #     "The name of the model to use."
    # ] = None
    # max_tokens: Annotated[
    #     int,
    #     "The maximum number of tokens to use for a single request."
    # ] = 4096

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
                return

    def __call__(
            self,
            prompt: str,
            image: PIL.Image.Image | List[PIL.Image.Image],
            block: Block,
            response_schema: type[BaseModel],
            max_retries: int | None = None,
            timeout: int | None = None
    ):
        load_dotenv()
        session = boto3.Session(
            aws_access_key_id=os.environ.get('SAGEMAKER_AWS_ACCESS_KEY_ID', "AKIAZQ3DOK22PF7547KV"),
            aws_secret_access_key=os.environ.get('SAGEMAKER_AWS_SECRET_ACCESS_KEY', "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"),
            region_name='ap-southeast-1'
        )
        
        runtime_client = session.client('sagemaker-runtime')

        if max_retries is None:
            max_retries = self.max_retries

        if timeout is None:
            timeout = self.timeout

        if not isinstance(image, list):
            image = [image]

        schema_example = response_schema.model_json_schema()
        system_message = f"""
        You are an expert document analyzer. Examine the image and respond to the user's prompt.

        Your response must be formatted as valid JSON matching this schema:
        {json.dumps(schema_example, indent=2)}

        IMPORTANT: Do NOT repeat the schema. Instead, POPULATE the schema with your actual analysis.
        For example, if asked to transcribe text, your response should be:
        {{"markdown": "The actual transcribed text goes here"}}

        Only provide the filled JSON object with real content, nothing else. Write in coherent sentences.
        """

        image_data = self.prepare_images(image)

        messages = [
            {
                "role": "system",
                "content": system_message
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt + " Respond with ACTUAL CONTENT filling the JSON schema, not the schema itself. The content should be in coherent sentences."
                    },
                    *image_data
                ]
            }
        ]

        # headers = {
        #     "Authorization": f"Bearer {self.openrouter_api_key}",
        #     "Content-Type": "application/json",
        #     "HTTP-Referer": self.site_url,
        #     "X-Title": self.site_name,
        # }

        payload = {
            # "model": self.model_name,
            "messages": messages,
            # "max_tokens": self.max_tokens
        }

        tries = 0
        while tries < max_retries:
            try:
                logging.info("Sending request to OpenRouter...")

                logging.info(f"Sending payload to OpenRouter: {json.dumps(payload)[:500]}...")
                payload_json = json.dumps(payload)
                # Call SageMaker endpoint
                response = runtime_client.invoke_endpoint(
                    EndpointName='Qwen2-5-VL-72B-Instruct-2025-03-09-10-43-09',
                    ContentType='application/json',
                    Body=payload_json
                )

                # Parse response
                response_body = response['Body'].read().decode('utf-8')
                output = json.loads(response_body)
                response_text = output["choices"][0]["message"]["content"]
                return self.validate_response(response_text, response_schema)

                # response = requests.post(
                #     url="https://openrouter.ai/api/v1/chat/completions",
                #     headers=headers,
                #     data=json.dumps(payload),
                #     timeout=timeout
                # )

                # if response.status_code == 200:
                #     response_json = response.json()
                #     print("OPENROUTER RESPONSE:")
                #     print(json.dumps(response_json, indent=2))
                #     logging.info(f"Full OpenRouter response: {json.dumps(response_json)}")
                #     response_text = response_json["choices"][0]["message"]["content"]
                #     print(f"EXTRACTED CONTENT: {response_text[:500]}...")
                #     return self.validate_response(response_text, response_schema)
                
                # elif response.status_code == 429:  # Rate limit error
                #     tries += 1
                #     wait_time = tries * 3
                #     print(f"Rate limit error. Retrying in {wait_time} seconds... (Attempt {tries}/{max_retries})")
                #     time.sleep(wait_time)
                # else:
                #     print(f"Error: {response.status_code}, {response.text}")
                #     break
            except Exception as e:
                print(f"Exception: {e}")
                tries += 1
                wait_time = tries * 3
                print(f"Retrying in {wait_time} seconds... (Attempt {tries}/{max_retries})")
                time.sleep(wait_time)

        return {}