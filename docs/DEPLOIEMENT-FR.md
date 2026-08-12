# Déploiement Windows et macOS

La version 4.1 fournit tout le nécessaire pour distribuer l'application sans demander aux utilisateurs d'installer Python.

## Packages générés

```text
Windows x64
  CCNA-EVE-Lab-Builder-Windows-x64-4.1.0-Setup.exe
  CCNA-EVE-Lab-Builder-Windows-x64-4.1.0-Portable.zip

macOS Apple Silicon
  CCNA-EVE-Lab-Builder-macOS-arm64-4.1.0.dmg

macOS Intel
  CCNA-EVE-Lab-Builder-macOS-x86_64-4.1.0.dmg
```

## Méthode recommandée : GitHub Actions

Une fois le projet envoyé sur GitHub :

```bash
git tag v4.1.0
git push origin v4.1.0
```

Le workflow **Build Installers** compile les versions Windows, Mac Apple Silicon et Mac Intel, calcule les SHA-256 et crée automatiquement la GitHub Release.

## Windows local

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\deploy\windows\build-all.ps1
```

Inno Setup 6 doit être installé pour générer le Setup `.exe`.

## macOS local

```bash
./deploy/macos/build-all.sh
```

Pour une distribution publique sans avertissement Gatekeeper, utilise un certificat Apple Developer ID et la notarisation Apple. Le projet contient les scripts pour le faire.

## Important

Les images Cisco IOSv/IOSvL2 ne sont jamais intégrées dans l'application ni dans les installateurs. L'utilisateur les importe lui-même depuis l'interface graphique.
