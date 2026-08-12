# Déploiement de l'application Windows et macOS

## Périmètre

**EVE-NG est déjà déployé et opérationnel.** Ce projet ne déploie pas EVE-NG.

Les packages Windows et macOS servent uniquement à installer **CCNA EVE Lab Builder sur le poste client**. L'application se connecte ensuite au serveur EVE-NG existant avec l'API EVE-NG et SSH.

Le déploiement ne contient pas :

- EVE-NG Community ou Pro;
- une VM, OVA ou ISO EVE-NG;
- VMware, ESXi, Proxmox, Hyper-V ou un autre hyperviseur;
- la configuration de virtualisation imbriquée;
- les images Cisco IOSv/IOSvL2.

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

## Fonctionnement après installation

```text
PC Windows / Mac
      |
      | CCNA EVE Lab Builder
      | API + SSH
      v
Serveur EVE-NG existant
```

Une fois l'application installée, tu renseignes simplement l'adresse IP/FQDN, le compte EVE-NG/SSH et le port SSH du serveur déjà en place.

## Windows local

Pour construire l'installateur de l'application :

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\deploy\windows\build-all.ps1
```

Inno Setup 6 et Python sont nécessaires sur la machine de **build**, pas sur le poste utilisateur après installation du package.

## macOS local

```bash
./deploy/macos/build-all.sh
```

Pour une distribution publique sans avertissement Gatekeeper, utilise un certificat Apple Developer ID et la notarisation Apple.

## Images Cisco

Les images Cisco IOSv/IOSvL2 ne sont jamais intégrées dans l'application ni dans les installateurs. Si nécessaire, l'utilisateur les sélectionne dans la GUI et l'application les importe vers **le serveur EVE-NG existant**.
