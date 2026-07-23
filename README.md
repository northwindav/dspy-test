# Minimal DSPy Starter (Azure-only)

This project gives you a minimal DSPy setup for Azure-backed experiments and for the future fire-weather sounding workflow.

## 1) Install a supported Python version

Use a standard CPython installation from python.org, not a Conda-managed interpreter.
This project is currently validated for Python 3.11 or 3.12. The current DSPy dependency stack does not install cleanly on Python 3.13 in this workspace.
If `python` still resolves to Conda on your machine, invoke the CPython 3.12 executable explicitly when creating the environment.

## 2) Create a native virtual environment (PowerShell)

```powershell
$env:LocalAppData\Programs\Python\Python312\python.exe -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, allow local scripts for the current user and retry:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## 3) Configure environment variables

Copy the template and edit values:

```powershell
Copy-Item .env.example .env
```

## 4) Run the DSPy smoke example

Run the Azure-backed smoke example:

```powershell
python examples/hello_dspy.py --term "few-shot learning"
```

Edit `.env`:

- Set `AZURE_OPENAI_API_KEY`
- Set `AZURE_OPENAI_ENDPOINT`
- Set `AZURE_OPENAI_DEPLOYMENT` to your deployment name
- Keep/update `AZURE_OPENAI_API_VERSION`

This repo is intentionally Azure-only so the setup matches the larger sounding-interpretation project.

Then rerun:

```powershell
python examples/hello_dspy.py --term "program synthesis"
```

## Troubleshooting

- Azure errors about model/deployment:
  - `AZURE_OPENAI_DEPLOYMENT` must be your Azure deployment name, not model family text.
- Azure auth or endpoint issues:
  - Verify endpoint shape: `https://<resource>.openai.azure.com`.
  - Verify API version supported by your deployment.
- DSPy import issues:
  - Confirm the `.venv` environment is active and packages were installed there.
  - Confirm `python --version` reports Python 3.11 or 3.12.
