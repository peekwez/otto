app:
	uvicorn main:api --host 0.0.0.0 --port 8000 --reload

inspect:
	npx @modelcontextprotocol/inspector \
		node build/index.js