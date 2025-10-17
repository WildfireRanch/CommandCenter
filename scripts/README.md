# Utility Scripts

This directory contains utility scripts for CommandCenter development and operations.

## Available Scripts

### Deployment & Health Checks
- **[check-deployment.sh](check-deployment.sh)** - Verify deployment status across all services
- **[health-check.sh](health-check.sh)** - Run health checks on production services
- **[test-integration.sh](test-integration.sh)** - Integration testing script

### Setup & Configuration
- **[setup.sh](setup.sh)** - Initial project setup script
- **[organize-repo.sh](organize-repo.sh)** - Repository organization utility

### Testing & Development
- **[test_kb_preview.sh](test_kb_preview.sh)** - Test Knowledge Base preview functionality
- **[TEST_V16.sh](TEST_V16.sh)** - V1.6 testing script
- **[debug_dockerfile.sh](debug_dockerfile.sh)** - Docker debugging utility

## Usage

Make scripts executable before running:
```bash
chmod +x scripts/script-name.sh
./scripts/script-name.sh
```

## Related Documentation

- **[DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)** - Full deployment guide
- **[docs/guides/](../docs/guides/)** - Step-by-step guides
- **[docs/deployment/](../docs/deployment/)** - Deployment documentation
