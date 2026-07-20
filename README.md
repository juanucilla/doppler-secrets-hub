# Doppler mTLS Secrets Hub

Secure secrets management server for distributed applications using **mTLS + HMAC-SHA256**.

## Quick Start

1. **Generate certificates** (see SETUP.md)
2. **Store in AWS Secrets Manager**
3. **Set GitHub Secrets** (DOPPLER_HMAC_SECRET, AWS credentials)
4. **Push to main** → Auto-deployed via GitHub Actions

## Endpoints

- `GET /health` — Health check
- `GET /secrets` — Fetch secrets (mTLS)
- `POST /secrets/update` — Update secrets (mTLS + HMAC)

## Server

- **Location**: polytubot-clock-witness (eu-west-1a)
- **IP**: 172.31.23.121:8443
- **Auth**: mTLS + HMAC-SHA256
- **Apps**: artusi-habibot, polytubot, casa

See SETUP.md for complete documentation.
