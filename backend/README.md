# Backend — Java API

This backend exposes a simple HTTP endpoint for `combined_data.json`.

## Run local backend API

From the repository root:

```bash
javac -d backend/classes backend/controllers/GetApiData.java
java -cp backend/classes GetApiData
```

Then access:

- `http://localhost:2026/api/data`

This endpoint includes CORS headers for `http://localhost:3000` so the React app can call it from `localhost:3000`.
