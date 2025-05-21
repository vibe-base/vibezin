# Setting Up Social Authentication for Vibezin

This document explains how to set up social authentication (Google login) for the Vibezin platform.

## Error: DoesNotExist at /accounts/login/

If you encounter this error:

```
DoesNotExist at /accounts/login/
No exception message supplied
Exception Location: /path/to/allauth/socialaccount/adapter.py, line 303, in get_app
```

This means that the social application configuration is missing in the database. Follow the steps below to fix it.

## Automatic Setup

We've created a management command to automatically set up the social authentication providers. Run:

```bash
# On development
python manage.py setup_social_auth

# On production
./scripts/setup_social_auth.sh
```

This will:
1. Create or update the Site object with domain 'vibezin.com'
2. Create or update the Google social application with the credentials from environment variables
3. Associate the social application with the site

## Manual Setup

If you prefer to set up social authentication manually:

1. Log in to the Django admin interface
2. Go to Sites > Add Site
   - Domain name: vibezin.com
   - Display name: Vibezin
3. Go to Social Applications > Add Social Application
   - Provider: Google
   - Name: Google
   - Client ID: Your Google OAuth client ID
   - Secret key: Your Google OAuth secret key
   - Sites: Add vibezin.com

## Google OAuth Credentials

To obtain Google OAuth credentials:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Go to APIs & Services > Credentials
4. Click "Create Credentials" > "OAuth client ID"
5. Application type: Web application
6. Name: Vibezin
7. Authorized JavaScript origins: https://vibezin.com
8. Authorized redirect URIs: https://vibezin.com/accounts/google/login/callback/
9. Click "Create"

Copy the Client ID and Client Secret and set them as environment variables:

```bash
export GOOGLE_CLIENT_ID=your-client-id
export GOOGLE_SECRET_KEY=your-client-secret
```

Or add them to your .env file:

```
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_SECRET_KEY=your-client-secret
```

## Troubleshooting

If you still encounter issues:

1. Check that the Site domain matches the domain you're accessing the site from
2. Verify that the Google OAuth credentials are correct
3. Make sure the redirect URI in the Google Cloud Console matches the callback URL
4. Check the Django logs for more detailed error messages

For more information, refer to the [django-allauth documentation](https://django-allauth.readthedocs.io/en/latest/installation.html).
