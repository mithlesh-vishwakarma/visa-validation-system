import os
import uuid
import logging
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

logger = logging.getLogger(__name__)

def upload_file(file_obj, folder="uploads"):
    """
    Uploads a file. If Supabase is configured, uploads to Supabase.
    Otherwise, saves to Django local media storage.
    Returns the file URL.
    """
    ext = os.path.splitext(file_obj.name)[1]
    filename = f"{uuid.uuid4()}{ext}"
    relative_path = f"{folder}/{filename}"

    # Check for Supabase settings
    supabase_url = getattr(settings, 'SUPABASE_URL', None)
    supabase_key = getattr(settings, 'SUPABASE_KEY', None)
    supabase_bucket = getattr(settings, 'SUPABASE_BUCKET', 'visa-documents')

    if supabase_url and supabase_key:
        try:
            import requests
            url = f"{supabase_url.rstrip('/')}/storage/v1/object/{supabase_bucket}/{relative_path}"
            headers = {
                "Authorization": f"Bearer {supabase_key}",
                "ApiKey": supabase_key,
                "Content-Type": file_obj.content_type or "application/octet-stream"
            }
            # Seek to start
            file_obj.seek(0)
            response = requests.post(url, data=file_obj.read(), headers=headers)
            if response.status_code == 200 or response.status_code == 201:
                # Return public URL (requires bucket to be public)
                # Format: https://{project_ref}.supabase.co/storage/v1/object/public/{bucket}/{path}
                public_url = f"{supabase_url.rstrip('/')}/storage/v1/object/public/{supabase_bucket}/{relative_path}"
                logger.info(f"Uploaded to Supabase: {public_url}")
                return public_url
            else:
                logger.error(f"Supabase upload failed: {response.text}. Falling back to local storage.")
        except Exception as e:
            logger.error(f"Error uploading to Supabase: {e}. Falling back to local storage.")

    # Local fallback
    file_obj.seek(0)
    saved_path = default_storage.save(relative_path, ContentFile(file_obj.read()))
    # Build complete local URL
    local_url = f"{settings.MEDIA_URL.rstrip('/')}/{saved_path}"
    logger.info(f"Uploaded to local storage: {local_url}")
    return local_url
