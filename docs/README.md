# Fake News API Docs

- Deployment and CI/CD guide: [DEPLOY.md](./DEPLOY.md)
- Contribution workflow: [CONTRIBUTION.md](./CONTRIBUTION.md)

## Build Locally

### Runtime setup

```bash
make install-runtime
```

Run the API locally:

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### Development setup

```bash
make install-dev
```

Fast checks without runtime ML dependencies:

```bash
make install-dev-lite
make quality-lite
```

Full local quality checks (includes tests):

```bash
make quality
```

## Build With Docker

Build image:

```bash
docker build -t fake-news-api:local .
```

Run container:

```bash
docker run --rm -p 8080:8080 --env-file .env fake-news-api:local
```

Health check:

```bash
curl http://localhost:8080/health
```

The Docker image uses a multi-stage build:
- `builder` installs Python dependencies from `requirements.txt`.
- `runtime` copies only the virtual environment and application files.
- No `dev` extras are installed in the final image.
