# Setting Up Google OAuth for Vibezin

This document explains how to set up Google OAuth authentication for the Vibezin platform.

## Automatic Setup

We've created a management command to automatically set up the Google OAuth provider. Run:

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

## Environment Variables

Make sure the following environment variables are set:

```
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

You can add these to your `.env` file for local development, or set them in your production environment.

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

Copy the Client ID and Client Secret and set them as environment variables.

## Troubleshooting

If you encounter issues with Google OAuth:

1. Check that the Site domain matches the domain you're accessing the site from
2. Verify that the Google OAuth credentials are correct
3. Make sure the redirect URI in the Google Cloud Console matches the callback URL
4. Check the Django logs for more detailed error messages

### Common Errors

#### DoesNotExist at /accounts/login/

If you see this error:

```
DoesNotExist at /accounts/login/
No exception message supplied
Exception Location: /path/to/allauth/socialaccount/adapter.py, line 303, in get_app
```

Run the setup_social_auth command to create the necessary database entries.

#### Invalid redirect_uri

If Google returns an error about an invalid redirect URI, make sure the Authorized redirect URIs in the Google Cloud Console includes:

```
https://vibezin.com/accounts/google/login/callback/
```

## Testing

To test the Google OAuth integration:

1. Go to the login page
2. Click "Sign in with Google"
3. You should be redirected to Google's authentication page
4. After authenticating, you should be redirected back to Vibezin and logged in

## Production Deployment

When deploying to production:

1. Make sure the GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables are set
2. Run the setup_social_auth command
3. Restart the Django application
