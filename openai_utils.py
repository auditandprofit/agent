import os
import sys
import json
import logging
import pprint
from openai import OpenAI

client = None  # Will be configured later via openai_configure_api
from typing import Optional, Tuple, Dict, Any, List

# Configure logging for clarity
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Define the function schema for flagged_methods.
FLAGGED_METHODS_FUNCTION_SCHEMA = [
    {
        "name": "flagged_methods",
        "description": "Returns the list of flagged methods from the response. Each entry in the list should be a dictionary with keys: 'method', 'params' (an array of strings), and 'primitive'.",
        "parameters": {
            "type": "object",
            "properties": {
                "flagged_methods": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "method": {"type": "string"},
                            "params": {"type": "array", "items": {"type": "string"}},
                            "primitive": {"type": "string"},
                            "description": {"type": "string"},
                            "chain": {"type": "string"},
                            "severity": {"type": "string"}
                        },
                        "required": ["method", "params", "primitive", "description", "chain", "severity"]
                    }
                }
            },
            "required": ["flagged_methods"]
        }
    }
]

FLAG_USAGE_FUNCTION_SCHEMA = [
    {
        "name": "flag_usage",
        "description": "Processes flag usage details and returns a dictionary with keys: 'method', 'confidence', and 'files'.",
        "parameters": {
            "type": "object",
            "properties": {
                "method": {"type": "string"},
                "confidence": {"type": "number"},
                "files": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["method", "confidence", "files"]
        }
    }
]

LOG_DATA_FUNCTION_SCHEMA = [
    {
        "name": "log_data",
        "description": (
            "Returns an array of arbitrary JSON objects supplied by the model. "
            "The caller’s system prompt defines the expected object structure."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "records": {
                    "type": "array",
                    "items": {}
                }
            },
            "required": ["records"]
        }
    }
]

def openai_configure_api(api_key: Optional[str] = None) -> None:
    """
    Configures the OpenAI API key.
    """
    global client
    if api_key is None:
        api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("An API key must be provided either as an argument or via the OPENAI_API_KEY environment variable.")
    client = OpenAI(api_key=api_key)  # Configure the OpenAI client using the provided API key
    logging.info("OpenAI API configured successfully.")


def openai_generate_response(
    messages: List[Dict[str, Any]],
    functions: Optional[List[Dict[str, Any]]] = None,
    model: str = "o3-mini",  # Change to your desired model
    function_call: Optional[Any] = "auto"
) -> Any:
    """
    Sends a chat message with an optional function schema and returns the API response.
    """
    if functions is None:
        functions = FLAGGED_METHODS_FUNCTION_SCHEMA
    logging.info("Sending messages:\n%s", pprint.pformat(messages))
    response = client.chat.completions.create(model=model,
    reasoning_effort="high",
    service_tier="flex",
    messages=messages,
    functions=functions,
    function_call=function_call)
    logging.info("Received response:\n%s", pprint.pformat(response))
    return response

def openai_parse_function_call(response: Any) -> Tuple[Optional[str], Optional[Any]]:
    """
    Parses the function call details from the API response.
    Supports both 'flag_usage' and 'flagged_methods' function calls.
    """
    try:
        message = response.choices[0].message
    except (KeyError, IndexError):
        logging.info("Unexpected response format:\n%s", pprint.pformat(response))
        return None, None

    function_call = message.function_call
    if function_call and getattr(function_call, 'name', None) == "flag_usage":
        args_str = getattr(function_call, 'arguments', "")
        usage = {}
        try:
            parsed_args = json.loads(args_str) if isinstance(args_str, str) else args_str
            if isinstance(parsed_args, dict):
                usage = parsed_args
        except (json.JSONDecodeError, AttributeError):
            usage = {}
        logging.info("Extracted flag_usage: %s", pprint.pformat(usage))
        return "flag_usage", usage
    elif function_call and getattr(function_call, 'name', None) == "flagged_methods":
        args_str = getattr(function_call, 'arguments', "")
        flagged = []
        try:
            parsed_args = json.loads(args_str) if isinstance(args_str, str) else args_str
            if isinstance(parsed_args, list):
                flagged = parsed_args
            elif isinstance(parsed_args, dict) and "flagged_methods" in parsed_args:
                flagged = parsed_args["flagged_methods"]
        except (json.JSONDecodeError, AttributeError):
            flagged = []
        # Validate that each flagged method dictionary has keys with correct types.
        for method in flagged:
            if not isinstance(method.get("params"), list):
                logging.error("flagged method entry missing or has invalid 'params': %s", method)
            if not isinstance(method.get("description"), str):
                logging.error("flagged method entry missing or has invalid 'description': %s", method)
            if not isinstance(method.get("chain"), str):
                logging.error("flagged method entry missing or has invalid 'chain': %s", method)
            if not isinstance(method.get("severity"), str):
                logging.error("flagged method entry missing or has invalid 'severity': %s", method)
        logging.info("Extracted flagged_methods: %s", pprint.pformat(flagged))
        return "flagged_methods", flagged

    elif function_call and getattr(function_call, 'name', None) == "log_data":
        args_str = function_call.arguments or ""
        try:
            parsed = json.loads(args_str) if isinstance(args_str, str) else args_str
        except json.JSONDecodeError:
            parsed = {}
        logging.info("Extracted log_data: %s", pprint.pformat(parsed))
        return "log_data", parsed.get("records", parsed)

    logging.info("No supported function call found in the response.")
    return None, None
