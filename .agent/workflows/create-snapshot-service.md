---
description: Create a new ingestion service for a dataset
---
1. Read the Architecture v2.1 document for the snapshot ingestion pattern
2. Create a provider adapter in apps/api/app/providers/
3. Create a service in apps/api/app/services/
4. Create a route in apps/api/app/api/routes/
5. Create a schema in apps/api/app/schemas/
6. All snapshots must use the common envelope format from the PRD
7. Write a pytest test
8. Test the endpoint with curl
