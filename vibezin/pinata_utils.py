"""
Utilities for interacting with Pinata IPFS service.
"""
import logging
import requests
import json
from typing import Dict, Any
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

def upload_to_pinata(file_content, filename=None) -> Dict[str, Any]:
    """
    Upload a file to IPFS via Pinata.

    Args:
        file_content: The content of the file to upload
        filename: Optional filename to use

    Returns:
        Dictionary with the result of the upload
    """
    try:
        if not filename:
            import uuid
            filename = f"image_{uuid.uuid4()}.png"

        logger.info(f"Preparing to upload file to Pinata: {filename}")

        # Save file temporarily
        temp_path = default_storage.save(f"temp/{filename}", ContentFile(file_content))
        temp_file_path = default_storage.path(temp_path)

        # Prepare the multipart/form-data
        url = "https://api.pinata.cloud/pinning/pinFileToIPFS"

        # Try with JWT first
        headers = {
            "Authorization": f"Bearer {settings.PINATA_JWT_API_KEY}"
        }

        logger.info(f"Uploading file to Pinata using JWT authentication")

        # Open the file in binary mode
        with open(temp_file_path, 'rb') as file_data:
            files = {
                'file': (filename, file_data, 'application/octet-stream')
            }

            # Make the request to Pinata
            response = requests.post(
                url,
                headers=headers,
                files=files
            )

            # If JWT fails, try with API key and secret
            if response.status_code != 200:
                logger.info(f"JWT authentication failed with status {response.status_code}. Trying API key authentication.")

                # Reopen the file since it was consumed in the previous request
                with open(temp_file_path, 'rb') as file_data:
                    files = {
                        'file': (filename, file_data, 'application/octet-stream')
                    }

                    headers = {
                        "pinata_api_key": settings.PINATA_API_KEY,
                        "pinata_secret_api_key": settings.PINATA_SECRET_API_KEY
                    }

                    response = requests.post(
                        url,
                        headers=headers,
                        files=files
                    )

            logger.info(f"Pinata API response status: {response.status_code}")

            # Check if the request was successful
            if response.status_code == 200:
                json_response = response.json()
                logger.info(f"Pinata API response: {json.dumps(json_response, indent=2)}")

                ipfs_hash = json_response.get('IpfsHash')
                if ipfs_hash:
                    ipfs_url = f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}"
                    logger.info(f"Successfully uploaded to IPFS: {ipfs_url}")
                    return {
                        "success": True,
                        "ipfs_url": ipfs_url,
                        "ipfs_hash": ipfs_hash
                    }
                else:
                    logger.error("Failed to get IPFS hash from Pinata response")
                    return {
                        "success": False,
                        "error": "Failed to get IPFS hash from Pinata response"
                    }
            else:
                logger.error(f"Pinata API error: {response.text}")
                return {
                    "success": False,
                    "error": f"Pinata API error: {response.status_code} - {response.text}"
                }

    except Exception as e:
        logger.exception(f"Exception while uploading to IPFS: {str(e)}")
        return {
            "success": False,
            "error": f"Error uploading to IPFS: {str(e)}"
        }

    finally:
        # Clean up the temporary file
        import os
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            logger.info(f"Cleaning up temporary file: {temp_file_path}")
            os.remove(temp_file_path)

def delete_from_pinata(ipfs_hash) -> Dict[str, Any]:
    """
    Delete a file from Pinata.

    Args:
        ipfs_hash: The IPFS hash of the file to delete

    Returns:
        Dictionary with the result of the deletion
    """
    try:
        url = f"https://api.pinata.cloud/pinning/unpin/{ipfs_hash}"

        # Try with JWT first
        headers = {
            "Authorization": f"Bearer {settings.PINATA_JWT_API_KEY}"
        }

        logger.info(f"Sending DELETE request to Pinata API: {url}")
        response = requests.delete(url, headers=headers)

        # If JWT fails, try with API key and secret
        if response.status_code != 200:
            logger.info(f"JWT authentication failed with status {response.status_code}. Trying API key authentication.")
            headers = {
                "pinata_api_key": settings.PINATA_API_KEY,
                "pinata_secret_api_key": settings.PINATA_SECRET_API_KEY
            }
            response = requests.delete(url, headers=headers)

        logger.info(f"Pinata API response status: {response.status_code}")
        logger.info(f"Pinata API response body: {response.text}")

        if response.status_code == 200:
            return {
                "success": True,
                "message": "Successfully deleted from IPFS"
            }
        else:
            return {
                "success": False,
                "error": f"Failed to delete from IPFS: {response.status_code} - {response.text}"
            }

    except Exception as e:
        logger.exception(f"Exception while deleting from IPFS: {str(e)}")
        return {
            "success": False,
            "error": f"Error deleting from IPFS: {str(e)}"
        }
