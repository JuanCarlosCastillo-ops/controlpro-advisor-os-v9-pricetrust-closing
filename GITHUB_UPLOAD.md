# Subir ControlPro V9 a GitHub

```powershell
cd C:\AGENTES\controlpro_advisor_os_v9_pricetrust_closing

git init
git branch -M main
git config --global user.name "JuanCarlosCastillo-ops"
git config --global user.email "JuanCarlosCastillo-ops@users.noreply.github.com"

git add .
git commit -m "Publicar ControlPro Advisor OS V9 PriceTrust Closing"

gh repo create controlpro-advisor-os-v9-pricetrust-closing --public --source=. --remote=origin --push
```

No subir `.env`. El repositorio incluye `.env.example`.
