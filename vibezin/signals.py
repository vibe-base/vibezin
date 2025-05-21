"""
Signal handlers for the vibezin app.
"""
import logging
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import Vibe
from .vibe_utils import create_vibe_directory, delete_vibe_directory

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Vibe)
def create_vibe_directory_handler(sender, instance, created, **kwargs):
    """
    Create a directory for a vibe when it is created.
    
    Args:
        sender: The model class
        instance: The Vibe instance
        created: Whether the instance was created
        **kwargs: Additional keyword arguments
    """
    try:
        # Only create the directory if the vibe has a slug
        if instance.slug:
            # If the vibe was just created, create a new directory
            if created:
                logger.info(f"Creating directory for new vibe: {instance.slug}")
                result = create_vibe_directory(instance)
                if not result["success"]:
                    logger.error(f"Failed to create vibe directory: {result['message']}")
            # Otherwise, update the metadata file
            else:
                from .vibe_utils import create_vibe_metadata_file
                logger.info(f"Updating metadata for vibe: {instance.slug}")
                result = create_vibe_metadata_file(instance)
                if not result["success"]:
                    logger.error(f"Failed to update vibe metadata: {result['message']}")
    except Exception as e:
        logger.exception(f"Error in create_vibe_directory_handler: {str(e)}")


@receiver(post_delete, sender=Vibe)
def delete_vibe_directory_handler(sender, instance, **kwargs):
    """
    Delete the directory for a vibe when it is deleted.
    
    Args:
        sender: The model class
        instance: The Vibe instance
        **kwargs: Additional keyword arguments
    """
    try:
        # Only delete the directory if the vibe has a slug
        if instance.slug:
            logger.info(f"Deleting directory for vibe: {instance.slug}")
            result = delete_vibe_directory(instance)
            if not result["success"]:
                logger.error(f"Failed to delete vibe directory: {result['message']}")
    except Exception as e:
        logger.exception(f"Error in delete_vibe_directory_handler: {str(e)}")


@receiver(pre_save, sender=Vibe)
def handle_slug_change(sender, instance, **kwargs):
    """
    Handle slug changes for vibes.
    
    If the slug changes, we need to rename the directory.
    
    Args:
        sender: The model class
        instance: The Vibe instance
        **kwargs: Additional keyword arguments
    """
    try:
        # Check if this is an existing vibe
        if instance.pk:
            # Get the old instance from the database
            old_instance = Vibe.objects.get(pk=instance.pk)
            
            # If the slug has changed, handle the directory rename
            if old_instance.slug != instance.slug and old_instance.slug and instance.slug:
                from .vibe_utils import get_vibe_directory
                import shutil
                
                old_dir = get_vibe_directory(old_instance.slug)
                new_dir = get_vibe_directory(instance.slug)
                
                # Only rename if the old directory exists
                if old_dir.exists():
                    logger.info(f"Renaming vibe directory from {old_instance.slug} to {instance.slug}")
                    
                    # Make sure the parent directory exists
                    new_dir.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Rename the directory
                    shutil.move(str(old_dir), str(new_dir))
    except Exception as e:
        logger.exception(f"Error in handle_slug_change: {str(e)}")
