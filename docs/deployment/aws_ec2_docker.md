# AWS EC2 Docker Deployment

This is the current MVP deployment path for StudyPilot: one EC2 instance runs the FastAPI backend in Docker Compose. SQLite data and uploaded files live in Docker volumes on the instance.

The mobile app still runs through Expo Go during this stage. In the mobile Settings screen, point the app to the EC2 backend URL and enter the backend access token.

## What This Deploys

- FastAPI backend
- SQLite database on an EC2-attached volume
- local uploaded-document storage on the same EC2 instance
- backend-only OpenAI API access
- write/generation protection with `BACKEND_ACCESS_TOKEN`
- in-memory rate limits for write and AI-generation requests
- optional Amazon Textract OCR for scanned PDFs

It does not deploy the mobile app to the App Store, set up a managed database, or move files to S3.

## EC2 Setup

Recommended starter instance:

- Ubuntu LTS
- `t3.small` or larger for PDF extraction and LLM request handling
- at least 20 GB disk
- Elastic IP associated to the instance so the mobile app does not break after stop/start

Security group for a first private demo:

- SSH: TCP 22 from your IP only
- Backend: TCP 8000 from your IP or testing device network only

For a public demo, put HTTPS and a reverse proxy in front before widening access.

## Elastic IP

Allocate and associate an Elastic IP before sharing the backend URL:

1. Open EC2 -> Network & Security -> Elastic IPs.
2. Choose `Allocate Elastic IP address`.
3. Select the new address, then choose Actions -> Associate Elastic IP address.
4. Associate it with the `studypilot-backend` instance.
5. Use `http://<elastic-ip>:8000` as the mobile API base URL.

If the instance is in `us-east-2`, set `AWS_REGION=us-east-2` in `backend/.env` so Textract calls use the same region.

## Install Docker

SSH into the instance, then install Docker:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
```

Log out and back in so the Docker group applies.

## Clone And Configure

```bash
git clone https://github.com/TaegonAndreaSehoKim/StudyPilot.git
cd StudyPilot
cp backend/.env.production.example backend/.env
```

Edit `backend/.env`:

```text
ENVIRONMENT=production
DATABASE_URL=sqlite:////app/data/studypilot.db
STORAGE_DIR=app/storage
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-5.5
USE_FAKE_AI=false
BACKEND_ACCESS_TOKEN=replace-with-a-long-random-token
CORS_ORIGINS=*
RATE_LIMIT_ENABLED=true
MUTATION_RATE_LIMIT_PER_MINUTE=60
AI_RATE_LIMIT_PER_MINUTE=12
OCR_PROVIDER=textract
AWS_REGION=us-east-1
MAX_UPLOAD_MB=10
```

Generate a token with:

```bash
python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
```

Never put `OPENAI_API_KEY` in the mobile app. Only the backend reads it.

For `OCR_PROVIDER=textract`, attach an IAM role or credentials that allow `textract:DetectDocumentText`. Use `OCR_PROVIDER=fake` if you want to test the UI flow without external OCR calls.

## Textract OCR Validation

After deployment, validate the OCR path with an image-only or scanned PDF:

1. Upload the scanned PDF from the mobile document picker or API.
2. Confirm the document returns `status=needs_ocr` and `ocr_status=available`.
3. Run OCR from the document screen.
4. Confirm the OCR job reaches `completed` and the document changes to `ocr_status=completed`.

If the job fails with `SubscriptionRequiredException` or `The AWS Access Key Id needs a subscription for the service`, IAM is not the only issue. AWS account access to Textract must be activated for the account/region, or the account sign-up/billing process must be completed. In the AWS console, open Amazon Textract in the deployment region and follow any activation or get-started prompt. If the account still cannot call Textract, use AWS account/billing support. For demos while this is unresolved, set:

```text
OCR_PROVIDER=fake
```

Then restart:

```bash
docker compose restart backend
```

## Run

```bash
docker compose up -d --build
docker compose logs -f backend
```

Health check:

```bash
curl http://<ec2-public-ip>:8000/health
```

From Windows PowerShell:

```powershell
Invoke-RestMethod -Uri "http://<elastic-ip>:8000/health"
```

Write requests require the access token:

```bash
curl -X POST http://<ec2-public-ip>:8000/courses \
  -H "Content-Type: application/json" \
  -H "X-StudyPilot-Key: <BACKEND_ACCESS_TOKEN>" \
  -d '{"title":"OMSCS AI"}'
```

From Windows PowerShell:

```powershell
$headers = @{
  "Content-Type" = "application/json"
  "X-StudyPilot-Key" = "<BACKEND_ACCESS_TOKEN>"
}
$body = @{ title = "AWS Test Course" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://<elastic-ip>:8000/courses" -Headers $headers -Body $body
```

## Mobile Settings

In Expo Go:

1. Open Settings.
2. Set API Base URL to `http://<elastic-ip>:8000`.
3. Set Backend Access Token to the same `BACKEND_ACCESS_TOKEN` from `backend/.env`.
4. Test connection.

The health check is public, but course creation, upload, generation, quiz attempts, and schedule writes require the token.
Write requests are rate-limited. OCR and AI-generation endpoints use the stricter `AI_RATE_LIMIT_PER_MINUTE` setting to reduce accidental Textract/OpenAI spend from repeated taps or scripts.

If Expo Go opens a stale local bundle, restart the mobile dev server with:

```powershell
cd mobile
npx expo start -c
```

## Data And Backups

Docker volumes:

- `studypilot_data`: SQLite database
- `studypilot_storage`: uploaded documents

List volumes:

```bash
docker volume ls | grep studypilot
```

For a quick SQLite backup:

```bash
docker compose exec backend python - <<'PY'
import shutil
from pathlib import Path
src = Path("/app/data/studypilot.db")
dst = Path("/app/data/studypilot-backup.db")
shutil.copy2(src, dst)
print(dst)
PY
```

For production, move the database to a managed service and uploaded files to S3.

## Update Deployment

```bash
git pull
docker compose up -d --build
docker compose logs -f backend
```

Useful operations:

```bash
docker compose ps
docker compose logs --tail=100 backend
docker compose restart backend
```

## Current Limitations

- No authentication or user isolation.
- Backend access token is a simple shared secret, not a user auth system.
- Rate limits are in-memory per backend process. Use Redis or an API gateway for multi-instance production.
- SQLite and local EC2 file storage are not high-availability.
- No HTTPS is configured by this Compose file.
- Textract OCR starts a FastAPI background task in this MVP. Large documents and multi-instance deployments should move to a durable queue such as SQS plus a worker.
