$ErrorActionPreference = 'SilentlyContinue'
Push-Location apps\web
Write-Host "Cleaning up broken nextjs dir"
Remove-Item -Recurse -Force node_modules, package.json, pnpm-lock.yaml, components, lib, .next, components.json, tailwind.config.ts, tsconfig.json -ErrorAction SilentlyContinue
Write-Host "Moving env"
Move-Item .env.local ..\..\data\tmp\.env.local -Force

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
Write-Host "Done recovery"
