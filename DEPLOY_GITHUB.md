# 🚀 Déploiement PlanHub sur GitHub — Guide complet

## Étape 1 — Créer un compte et dépôt GitHub

1. Aller sur **https://github.com** → Se connecter (ou créer un compte)
2. Cliquer **"New repository"** (bouton vert)
3. Remplir :
   - **Repository name** : `PlanHub`
   - **Description** : `Du DQE à Primavera P6 en quelques clics`
   - Choisir **Private** (code confidentiel) ou **Public**
   - ❌ Ne pas cocher "Add README" (on a déjà le nôtre)
4. Cliquer **"Create repository"**

---

## Étape 2 — Installer Git sur Windows

Télécharger depuis : **https://git-scm.com/download/win**

Vérifier l'installation :
```cmd
git --version
```

---

## Étape 3 — Pousser le code sur GitHub

Ouvrir un **CMD** ou **PowerShell** dans le dossier `PlanHub` :

```cmd
cd C:\chemin\vers\PlanHub

git init
git add .
git commit -m "Initial commit — PlanHub v1.0"
git branch -M main
git remote add origin https://github.com/VOTRE_USERNAME/PlanHub.git
git push -u origin main
```

> Remplacez `VOTRE_USERNAME` par votre nom d'utilisateur GitHub.

---

## Étape 4 — Vérifier la compilation automatique

Après le `git push`, GitHub Actions démarre automatiquement :

1. Aller sur votre dépôt GitHub
2. Cliquer sur l'onglet **"Actions"**
3. Vous verrez le workflow **"Build PlanHub.exe (Windows)"** en cours
4. ⏱️ La compilation prend **environ 5–8 minutes**
5. Quand c'est vert ✅ → cliquer sur le workflow → **"Artifacts"** → télécharger **PlanHub-Windows-exe.zip**

---

## Étape 5 — Créer une Release officielle (optionnel)

Pour publier une version téléchargeable avec numéro de version :

```cmd
git tag v1.0.0
git push origin v1.0.0
```

GitHub crée automatiquement une **Release** avec `PlanHub.exe` en téléchargement direct !

Accessible à : `https://github.com/VOTRE_USERNAME/PlanHub/releases`

---

## Mises à jour futures

Après chaque modification du code :

```cmd
git add .
git commit -m "Description de la modification"
git push
```

GitHub recompile automatiquement un nouvel exe. ✅

---

## 📋 Structure du workflow GitHub Actions

```
.github/
└── workflows/
    └── build.yml    ← Se déclenche à chaque push sur main
                        Compile sur Windows Server 2022
                        Python 3.11 + PyInstaller 6.x
                        Produit : dist/PlanHub.exe (~50-80 Mo)
```

---

## ❓ Problèmes fréquents

| Problème | Solution |
|----------|----------|
| `git push` demande mot de passe | Utiliser un Token GitHub (Settings → Developer settings → Personal access tokens) |
| L'exe plante au démarrage | Vérifier les `hidden-imports` dans `PlanHub.spec` |
| Taille exe trop grande | Activer UPX dans le `.spec` (déjà activé) |
| customtkinter introuvable | Les `collect_data_files` dans le `.spec` s'en chargent |
