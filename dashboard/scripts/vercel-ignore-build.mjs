// Vercel semantics: exit 0 skips a Git build; exit 1 proceeds. Production
// releases are performed by deploy_prod.yml with `vercel deploy --prebuilt`,
// so every automatic Git deployment is intentionally ignored.
process.exit(0);
