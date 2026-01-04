# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-04

### Added
- Initial release of Railway integration for Home Assistant
- Support for personal and team API tokens
- Credit balance, current usage, and remaining credits sensors
- Projects and workspaces count sensors
- Per-workspace usage sensors with billing details
- Template earnings sensors (30-day and total)
- Referral statistics sensors (credited and pending)
- API connectivity binary sensor
- Per-project health binary sensors based on deployment status
- Configurable update interval (5, 10, 15, 30, or 60 minutes)
- Re-authentication flow for expired tokens
- HACS compatibility

### Technical
- Async-first design using aiohttp
- DataUpdateCoordinator pattern for efficient polling
- GraphQL API client with comprehensive error handling
- PEP 561 type hints support
- GitHub Actions CI/CD pipeline
