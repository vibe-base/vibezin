import os
import requests
import json
import uuid
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
    
    # Save file temporarily
    temp_path = default_storage.save(f"temp/{filename}", ContentFile(image_file.read()))
    temp_file_path = default_storage.path(temp_path)
    
    try:
        # Prepare the multipart/form-data
        url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
        
        headers = {
            "Authorization": f"Bearer {settings.PINATA_JWT_API_KEY}"
        }
        
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
            
            # Check if the request was successful
            if response.status_code == 200:
                json_response = response.json()
                ipfs_hash = json_response.get('IpfsHash')
                if ipfs_hash:
                    ipfs_url = f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}"
                    return True, ipfs_url
                else:
                    return False, "Failed to get IPFS hash from Pinata response"
            else:
                return False, f"Pinata API error: {response.text}"
    
    except Exception as e:
        return False, f"Error uploading to IPFS: {str(e)}"
    
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
