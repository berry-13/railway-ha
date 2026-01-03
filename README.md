# Railway Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A Home Assistant integration to monitor your [Railway](https://railway.com) projects, deployments, and usage.

## Features

- **Credit Balance**: Monitor your account credit balance
- **Usage Tracking**: View current and estimated usage costs
- **Projects Overview**: Count of active projects
- **Teams Count**: Number of teams you belong to
- **Per-Project Usage**: Individual usage sensors for each project
- **Deployment Health**: Binary sensors indicating deployment status
- **API Connection Status**: Monitor connectivity to Railway API

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add `https://github.com/berry-13/railway-ha` as a custom repository with category "Integration"
6. Click "Add"
7. Search for "Railway" and install it
8. Restart Home Assistant

### Manual Installation

1. Download the latest release
2. Copy the `custom_components/railway` folder to your `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings** > **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Railway"
4. Enter your Railway API token

### Getting an API Token

1. Go to [Railway Account Tokens](https://railway.com/account/tokens)
2. Click "Create Token"
3. Choose the appropriate scope:
   - **Personal Token**: Access to your personal projects and teams
   - **Team Token**: Access to a specific team's resources only
4. Copy the token and paste it in the Home Assistant configuration

## Entities

### Sensors

| Entity | Description | Unit |
|--------|-------------|------|
| Credit Balance | Account credit balance | USD |
| Current Usage | Current billing period usage | USD |
| Estimated Usage | Estimated usage for the period | USD |
| Projects | Number of active projects | count |
| Teams | Number of teams | count |
| {Project} Usage | Per-project usage | USD |

### Binary Sensors

| Entity | Description |
|--------|-------------|
| API Connected | Connection status to Railway API |
| {Project} Health | Deployment health status per project |

## Rate Limits

Railway API has rate limits based on your plan:

- **Free**: 100 requests per hour
- **Hobby**: 1,000 requests per hour
- **Pro**: 10,000 requests per hour

This integration polls every 15 minutes by default (96 requests/day), well within all plan limits.

## Troubleshooting

### Invalid API Token

If you see authentication errors, your token may have expired or been revoked. Generate a new token and reconfigure the integration.

### Missing Data

Some fields like `creditBalance` and detailed usage may not be available depending on your Railway plan and API permissions. The integration gracefully handles missing data.

## License

MIT License - see [LICENSE](LICENSE) for details.
