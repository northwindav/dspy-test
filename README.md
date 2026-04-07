# Minimal DSPy Starter (Ollama first, Azure second)

This project gives you a minimal DSPy setup for tutorials and examples.

## 1) Use your existing conda environment (PowerShell)

```powershell
conda activate dspy
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If needed, install dependencies directly into the env without activating it:

```powershell
conda run -n dspy pip install -r requirements.txt
```

## 2) Configure environment variables

Copy the template and edit values:

```powershell
Copy-Item .env.example .env
```

## 3) Fast path: run locally with Ollama

Install Ollama, then pull/start a model:

```powershell
ollama pull llama3.2:3b
```

Run the DSPy smoke example:

```powershell
python examples/hello_dspy.py --term "few-shot learning"
```

## 4) Switch to Azure OpenAI

Edit `.env`:

- Set `DSPY_PROVIDER=azure`
- Set `AZURE_OPENAI_API_KEY`
- Set `AZURE_OPENAI_ENDPOINT`
- Set `AZURE_OPENAI_DEPLOYMENT` to your deployment name
- Keep/update `AZURE_OPENAI_API_VERSION`

Then rerun:

```powershell
python examples/hello_dspy.py --term "program synthesis"
```

## Troubleshooting

- `Connection error` with Ollama:
  - Ensure Ollama is installed and running locally.
  - Confirm `DSPY_OLLAMA_API_BASE=http://localhost:11434`.
- Azure errors about model/deployment:
  - `AZURE_OPENAI_DEPLOYMENT` must be your Azure deployment name, not model family text.
- Azure auth or endpoint issues:
  - Verify endpoint shape: `https://<resource>.openai.azure.com`.
  - Verify API version supported by your deployment.
- DSPy import issues:
  - Confirm the `dspy` conda environment is active and packages were installed there.
