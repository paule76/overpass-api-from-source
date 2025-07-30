# Contributing Guide

Vielen Dank für Ihr Interesse an diesem Projekt!

## Bug Reports

Wenn Sie einen Bug finden, erstellen Sie bitte ein Issue mit:
- Beschreibung des Problems
- Schritte zur Reproduktion
- Erwartetes Verhalten
- Tatsächliches Verhalten
- Logs (docker logs overpass_custom)

## Pull Requests

1. Forken Sie das Repository
2. Erstellen Sie einen Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Committen Sie Ihre Änderungen (`git commit -m 'Add some AmazingFeature'`)
4. Pushen Sie zum Branch (`git push origin feature/AmazingFeature`)
5. Öffnen Sie einen Pull Request

## Code Style

- Bash Scripts: Verwenden Sie ShellCheck
- Docker: Folgen Sie den Docker Best Practices
- Dokumentation: Klar und präzise

## Testing

Testen Sie Ihre Änderungen lokal:
```bash
./build.sh
docker compose up -d
curl http://localhost:8090/api/status
```