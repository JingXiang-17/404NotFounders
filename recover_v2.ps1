$ErrorActionPreference = 'SilentlyContinue'
Push-Location apps
Write-Host "Renaming broken dir"
Rename-Item -Path web -NewName web-broken-$(Get-Random) -Force
Write-Host "Creating fresh dir"
New-Item -ItemType Directory -Force -Path web | Out-Null
Push-Location web

$ErrorActionPreference = 'Stop'
Write-Host "Creating next app"
pnpm create next-app . --ts --tailwind --eslint --app --src-dir --import-alias "@/*" --yes --use-pnpm
Move-Item ..\..\data\tmp\.env.local .env.local -Force

Write-Host "Adding dependencies"
pnpm add recharts motion lucide-react zod react-hook-form @hookform/resolvers @tanstack/react-query
Write-Host "Init shadcn"
npx --yes shadcn@canary init -d
Write-Host "Adding shadcn components"
npx --yes shadcn@canary add button card dialog tabs tooltip badge skeleton slider accordion select input form separator table -y
Pop-Location
Pop-Location
Write-Host "Done recovery"
