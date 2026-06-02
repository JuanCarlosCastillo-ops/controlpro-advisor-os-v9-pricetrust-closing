# Subir ControlPro Advisor OS V10 a GitHub

## Recomendación para este proyecto

No elimines el repositorio V9 que ya está conectado a Render. Lo correcto es actualizar el mismo repo con un commit V10, para conservar el link público y el historial.

Repo actual recomendado:

```text
controlpro-advisor-os-v9-pricetrust-closing
```

La carpeta local puede llamarse `controlpro_advisor_os_v10_architecture_lock`, pero el repo de Render puede seguir siendo el mismo.

## Si vas a actualizar el repo existente

Copia el contenido de esta versión dentro de:

```text
C:\AGENTES\controlpro_advisor_os_v9_pricetrust_closing
```

Luego:

```powershell
cd C:\AGENTES\controlpro_advisor_os_v9_pricetrust_closing

git status
git add .
git commit -m "Actualizar a ControlPro V10 Architecture Lock"
git push
```

Render desplegará automáticamente el nuevo commit si el auto-deploy está activo.

## Si quieres crear repo nuevo

```powershell
cd C:\AGENTES\controlpro_advisor_os_v10_architecture_lock

git init
git branch -M main
git add .
git commit -m "Publicar ControlPro Advisor OS V10 Architecture Lock"

gh repo create controlpro-advisor-os-v10-architecture-lock --public --source=. --remote=origin --push
```
