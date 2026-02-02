$env:PYTHONPATH = (Get-Location).Path
pytest @args
