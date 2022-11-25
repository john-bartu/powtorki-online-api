import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", port=5000, log_level="info", host="0.0.0.0", workers=4)
