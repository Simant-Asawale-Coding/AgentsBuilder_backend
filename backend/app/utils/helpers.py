import json
import os
import traceback
from fastapi.responses import JSONResponse
 
 
def format_to_snake_case(text: str) -> str:
    """Converts a string to snake case
    Args:
        text (str): Text to convert to snake case
    Returns:
        str: Text in snake case
    """
    for char in [
        "\\",
        "-",
        "/",
        " ",
    ]:
        if char in text:
            text = text.replace(char, "_")
    return text.lower()
 
 
def remove_file_extension(file_name: str) -> str:
    """Removes the file extension from a file name
 
    Args:
        file_name (str): Name of the file
 
    Returns:
        str: File name without the extension
    """
    return os.path.splitext(file_name)[0]
 
 
def format_file_name(file_name: str, extension: str, suffix: str = "") -> str:
    """
    Formats a file name by removing path directories, converting the base file name and suffix to snake case,
    and appending the provided extension.
    Args:
        file_name (str): The original file name.
        extension (str): The file extension to be appended.
        suffix (str, optional): The suffix to be added to the file name. Defaults to "".
    Returns:
        str: The formatted file name.
    """  
    base_name_snake = remove_file_extension(os.path.basename(file_name))
    suffix_snake = format_to_snake_case(suffix)
 
    return base_name_snake + "-" + suffix_snake + extension
 
 
def json_message_response(code: int, data: str):
    """
    Returns a JSON response with a message and status code.
    Args:
        code (int): The status code of the response.
        data (str): The message to include in the response.
    Returns:
        JSONResponse: The JSON response with the message and status code.
    """
    try:
        return JSONResponse(content=json.dumps({"message": data}), status_code=code)
    except Exception as e:
        traceback.print_exc()
        raise
 
 
def json_response(code: int, data: str):
    """
    Returns a JSON response with the provided data and status code.    
    Args:
        code (int): The status code of the response.
        data (str): The data to include in the response.    
    Returns:
        JSONResponse: The JSON response with the data and status code.
    """
    try:
        return JSONResponse(
            content=json.dumps({"output_response": data}), statuscode=code
        )
    except Exception as e:
        traceback.print_exc()
        raise
 
 
def argument_helper(type: type, *args, **kwargs):
    """
    Helper function to retrieve the first argument of a specified type from a list of positional and keyword arguments.    
    Args:
        type (type): The type of argument to be retrieved.
        *args: A variable-length list of positional arguments.
        **kwargs: A variable-length dictionary of keyword arguments.    
    Returns:
        The first argument of the specified type, or raises an exception if no such argument is found.
    """
    requests = [value for key, value in kwargs.items() if isinstance(value, type)]
    if not requests:
        requests = [value for value in args if isinstance(value, type)]
    if requests:
        return requests[0]
    raise Exception(f"{type} parameter is missing.")
 