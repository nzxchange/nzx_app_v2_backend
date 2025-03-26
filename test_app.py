from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/test")
async def test():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("test_app:app", host="0.0.0.0", port=8001, reload=True) 