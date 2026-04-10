import os
import base64
from openai import APIStatusError, OpenAI
from dotenv import load_dotenv
import numpy as np
import time
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

load_dotenv()

# Retrieve credentials from .env file or environment
endpoint = os.getenv("gpt_endpoint")
deployment = os.getenv("gpt_deployment")
api_version = os.getenv("gpt_api_version")

if not endpoint:
    raise ValueError("gpt_endpoint is required")
if not deployment:
    raise ValueError("gpt_deployment is required")


def _normalize_openai_base_url(raw_endpoint: str) -> str:
    normalized = raw_endpoint.rstrip("/")
    if normalized.endswith("/responses"):
        normalized = normalized[: -len("/responses")]
    if normalized.endswith("/chat/completions"):
        normalized = normalized[: -len("/chat/completions")]
    if "/openai/v1" in normalized:
        return normalized.split("/openai/v1", 1)[0] + "/openai/v1"
    return f"{normalized}/openai/v1"

# Initialize Azure OpenAI client for GPT model using managed identity
credential = DefaultAzureCredential()
token_provider = get_bearer_token_provider(
    credential,
    "https://ai.azure.com/.default",
)
base_url = _normalize_openai_base_url(endpoint)

client = OpenAI(
    base_url=base_url,
    api_key=token_provider,
)

SYSTEM_PROMPT = (
    "You are a helpful assistant working for Zava, a company that specializes in "
    "offering products to assist homeowners with do-it-yourself projects. "
    "Respond to customer inquiries with relevant product recommendations and DIY tips. "
    "If a customer asks for paint, suggest one of the following three colors: blue, green, and white. "
    "If a customer asks for something not related to a DIY project, politely inform them "
    "that you can only assist with DIY-related inquiries. "
    "Zava has a variety of store locations across the country. "
    "If a customer asks about store availability, direct the customer to the Miami store."
)

def generate_response(text_input):
    start_time = time.time()
    """
    Input:
        text_input (str): The user's chat input.

    Output:
        response (str): A Markdown-formatted response from the agent.
    """

    if not text_input or not text_input.strip():
        return "Please enter a message."

    try:
        # Use the OpenAI Responses API against the Foundry/OpenAI v1 endpoint.
        completion = client.responses.create(
            model=deployment,
            instructions=SYSTEM_PROMPT,
            input=text_input.strip(),
        )
        end_sum = time.time()
        print(f"generate_response Execution Time: {end_sum - start_time} seconds")
        # Return response content
        return completion.output_text
    except APIStatusError as e:
        response_body = ""
        if e.response is not None:
            try:
                response_body = e.response.text
            except Exception:
                response_body = "<unable to read response body>"
        raise RuntimeError(
            f"OpenAI request failed status={e.status_code}; base_url={base_url}; "
            f"model={deployment}; response={response_body}"
        ) from e
