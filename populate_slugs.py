import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vibezin_project.settings')
django.setup()

from vibezin.models import Vibe

def populate_slugs():
    vibes = Vibe.objects.all()
    print(f"Found {vibes.count()} vibes")
    
    for vibe in vibes:
        if not vibe.slug:
            print(f"Generating slug for vibe: {vibe.title}")
            # The save method will generate the slug
            vibe.save()
        else:
            print(f"Vibe already has slug: {vibe.slug}")

if __name__ == '__main__':
    populate_slugs()
    print("Done!")
