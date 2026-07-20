# Setup Guide: Doppler mTLS Server

See README.md for overview.

## Prerequisites
- AWS Account (configured: `aws sts get-caller-identity`)
- GitHub account: juanucilla
- Git + GitHub CLI

## Step 1: Generate Certificates

```bash
mkdir -p /tmp/doppler_certs && cd /tmp/doppler_certs

# CA
openssl genrsa -out ca.key 4096
openssl req -new -x509 -days 3650 -key ca.key -out ca.crt \
  -subj "/CN=Doppler-CA/O=Internal/C=US"

# Server
openssl genrsa -out server.key 4096
openssl req -new -key server.key -out server.csr \
  -subj "/CN=doppler.internal/O=Internal/C=US"
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out server.crt -days 365 \
  -extfile <(printf "subjectAltName=IP:172.31.23.121")

# Client EC2
openssl genrsa -out client-ec2.key 4096
openssl req -new -key client-ec2.key -out client-ec2.csr \
  -subj "/CN=ec2-instances/O=Internal/C=US"
openssl x509 -req -in client-ec2.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out client-ec2.crt -days 365

# Client Lambda
openssl genrsa -out client-lambda.key 4096
openssl req -new -key client-lambda.key -out client-lambda.csr \
  -subj "/CN=lambda-updater/O=Internal/C=US"
openssl x509 -req -in client-lambda.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out client-lambda.crt -days 365
```

## Step 2: Store in AWS Secrets Manager

```bash
REGION="eu-west-1"

aws secretsmanager create-secret --name doppler/ca-cert --secret-string file:///tmp/doppler_certs/ca.crt --region $REGION
aws secretsmanager create-secret --name doppler/server-cert --secret-string file:///tmp/doppler_certs/server.crt --region $REGION
aws secretsmanager create-secret --name doppler/server-key --secret-string file:///tmp/doppler_certs/server.key --region $REGION
aws secretsmanager create-secret --name doppler/client-lambda-cert --secret-string file:///tmp/doppler_certs/client-lambda.crt --region $REGION
aws secretsmanager create-secret --name doppler/client-lambda-key --secret-string file:///tmp/doppler_certs/client-lambda.key --region $REGION
aws secretsmanager create-secret --name doppler/hmac-secret --secret-string "8d98a4cb78d8a9537213183fa2f105d8720d028ec2f47da7a4aeb2b26f5c47fa" --region $REGION
```

## Step 3: Set GitHub Secrets

```bash
gh secret set DOPPLER_HMAC_SECRET --body "8d98a4cb78d8a9537213183fa2f105d8720d028ec2f47da7a4aeb2b26f5c47fa" --repo juanucilla/doppler-secrets-hub
gh secret set EC2_INSTANCE_ID --body "i-01ada4e0854942c06" --repo juanucilla/doppler-secrets-hub
gh secret set EC2_REGION --body "eu-west-1" --repo juanucilla/doppler-secrets-hub
gh secret set EC2_PRIVATE_IP --body "172.31.23.121" --repo juanucilla/doppler-secrets-hub
gh secret set AWS_ACCESS_KEY_ID --body "$(aws configure get aws_access_key_id)" --repo juanucilla/doppler-secrets-hub
gh secret set AWS_SECRET_ACCESS_KEY --body "$(aws configure get aws_secret_access_key)" --repo juanucilla/doppler-secrets-hub
```

## Step 4: Deploy

```bash
git add .
git commit -m "Initial commit: Doppler mTLS server"
git push origin main
```

GitHub Actions will automatically deploy to EC2.

Check deployment:
```bash
ssh ubuntu@52.16.52.252
sudo systemctl status doppler
curl -k https://localhost:8443/health
```
