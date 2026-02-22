# Expose local backend (port 8000) via ngrok for ElevenLabs post-call webhook.
# Prereqs: ngrok installed (https://ngrok.com/download), backend running: uvicorn app.main:app --reload
# Then set ElevenLabs webhook URL to: https://<ngrok-host>/webhooks/elevenlabs/post-call

$port = 8000
Write-Host "Starting ngrok tunnel to http://localhost:$port"
Write-Host "Backend must be running (e.g. uvicorn app.main:app --reload)."
Write-Host "Set ElevenLabs post-call webhook to: https://<ngrok-url>/webhooks/elevenlabs/post-call"
Write-Host ""
& ngrok http $port
