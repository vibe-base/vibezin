import os
import requests
import json
import uuid
import re
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO

def validate_image(image_file):
    """
    Validate image file size and type
    Returns (is_valid, error_message)
    """
    # Check file size
    if image_file.size > settings.MAX_PROFILE_IMAGE_SIZE:
        max_size_mb = settings.MAX_PROFILE_IMAGE_SIZE / (1024 * 1024)
        return False, f"Image size exceeds the maximum allowed size of {max_size_mb}MB"

    # Check file type
    if image_file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        allowed_types = ', '.join([t.split('/')[-1] for t in settings.ALLOWED_IMAGE_TYPES])
        return False, f"Image type not supported. Please upload {allowed_types}"

    return True, None

def optimize_image(image_file, max_size=(800, 800), quality=85):
    """
    Optimize image by resizing and compressing it
    Returns the optimized image as BytesIO
    """
    img = Image.open(image_file)

    # Convert to RGB if image is in RGBA mode (e.g., PNG with transparency)
    if img.mode == 'RGBA':
        # Create a white background
        background = Image.new('RGB', img.size, (255, 255, 255))
        # Paste the image on the background
        background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # Resize if larger than max_size
    if img.width > max_size[0] or img.height > max_size[1]:
        img.thumbnail(max_size, Image.LANCZOS)

    # Save to BytesIO
    output = BytesIO()
    img.save(output, format='JPEG', quality=quality, optimize=True)
    output.seek(0)

    return output

def upload_to_ipfs(image_file, filename=None):
    """
    Upload an image to IPFS via Pinata
    Returns (success, ipfs_url or error_message)
    """
    if not filename:
        # Generate a unique filename
        ext = os.path.splitext(image_file.name)[1] if hasattr(image_file, 'name') else '.jpg'
        filename = f"{uuid.uuid4()}{ext}"

    print(f"Preparing to upload file to IPFS: {filename}")

    # Save file temporarily
    temp_path = default_storage.save(f"temp/{filename}", ContentFile(image_file.read()))
    temp_file_path = default_storage.path(temp_path)

    try:
        # Prepare the multipart/form-data
        url = "https://api.pinata.cloud/pinning/pinFileToIPFS"

        # Try with JWT first
        headers = {
            "Authorization": f"Bearer {settings.PINATA_JWT_API_KEY}"
        }

        print(f"Uploading file to Pinata using JWT authentication")

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
                print(f"JWT authentication failed with status {response.status_code}. Trying API key authentication.")

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

            print(f"Pinata API response status: {response.status_code}")

            # Check if the request was successful
            if response.status_code == 200:
                json_response = response.json()
                print(f"Pinata API response: {json.dumps(json_response, indent=2)}")

                ipfs_hash = json_response.get('IpfsHash')
                if ipfs_hash:
                    ipfs_url = f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}"
                    print(f"Successfully uploaded to IPFS: {ipfs_url}")
                    return True, ipfs_url
                else:
                    print("Failed to get IPFS hash from Pinata response")
                    return False, "Failed to get IPFS hash from Pinata response"
            else:
                print(f"Pinata API error: {response.text}")
                return False, f"Pinata API error: {response.text}"

    except Exception as e:
        print(f"Exception while uploading to IPFS: {str(e)}")
        return False, f"Error uploading to IPFS: {str(e)}"

    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            print(f"Cleaning up temporary file: {temp_file_path}")
            os.remove(temp_file_path)

def extract_ipfs_hash(ipfs_url):
    """
    Extract the IPFS hash from a URL
    Returns the hash or None if not found
    """
    if not ipfs_url:
        return None

    print(f"Extracting IPFS hash from URL: {ipfs_url}")

    # Match pattern like https://gateway.pinata.cloud/ipfs/QmXyZ123...
    pattern = r'ipfs/([a-zA-Z0-9]+)'
    match = re.search(pattern, ipfs_url)

    if match:
        hash_value = match.group(1)
        print(f"Extracted IPFS hash: {hash_value}")
        return hash_value

    # Try alternative pattern for other IPFS gateways
    pattern = r'/([a-zA-Z0-9]{46})'  # Most IPFS hashes are 46 characters
    match = re.search(pattern, ipfs_url)

    if match:
        hash_value = match.group(1)
        print(f"Extracted IPFS hash (alternative pattern): {hash_value}")
        return hash_value

    print("No IPFS hash found in URL")
    return None

def delete_from_ipfs(ipfs_url):
    """
    Delete an image from IPFS via Pinata
    Returns (success, message)
    """
    ipfs_hash = extract_ipfs_hash(ipfs_url)
    if not ipfs_hash:
        return False, "Invalid IPFS URL or could not extract hash"

    try:
        url = "https://api.pinata.cloud/pinning/unpin/" + ipfs_hash

        # Try with JWT first
        headers = {
            "Authorization": f"Bearer {settings.PINATA_JWT_API_KEY}"
        }

        print(f"Sending DELETE request to Pinata API: {url}")
        response = requests.delete(url, headers=headers)

        # If JWT fails, try with API key and secret
        if response.status_code != 200:
            print(f"JWT authentication failed with status {response.status_code}. Trying API key authentication.")
            headers = {
                "pinata_api_key": settings.PINATA_API_KEY,
                "pinata_secret_api_key": settings.PINATA_SECRET_API_KEY
            }
            response = requests.delete(url, headers=headers)

        print(f"Pinata API response status: {response.status_code}")
        print(f"Pinata API response body: {response.text}")

        if response.status_code == 200:
            return True, "Successfully deleted from IPFS"
        else:
            return False, f"Failed to delete from IPFS: {response.text}"

    except Exception as e:
        print(f"Exception while deleting from IPFS: {str(e)}")
        return False, f"Error deleting from IPFS: {str(e)}"
