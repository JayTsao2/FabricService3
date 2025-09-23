import threading
import glob
import os
from scripts.cisco.v_12_2_2.build import FabricBuilder
from fastapi import FastAPI
from starlette.responses import FileResponse



app = FastAPI()
builder = FabricBuilder()

@app.get("/")
def root():
    return {"message": "Root"}

@app.get("/build")
def build():
    t = threading.Thread(target=builder.build)
    t.start()
    return {"response":"Build Started"}

@app.post("/gitmerge")
def gitmerge():
    def job():
        # builder.build()
        with open("./logs/pending.txt", "w", encoding="utf-8") as f:
            fp_list = glob.glob("*_pending.txt")
            for fp in fp_list:
                f.write("-" * 10)
                f.write(" {} ".format(fp))
                f.write("-" * 10)
                f.write("\n")
                with open(fp, "r", encoding="utf-8") as source_f:
                    f.write(source_f.read())
                f.write("\n")
    t = threading.Thread(target=job)
    t.start()
    return {"response":"Merge Started", "url":"/pending"}

@app.get("/pending")
def pending():
    file_path = "./logs/pending.txt"
    if not os.path.exists(file_path):
        return {"error": "File not found"}

    # Use FileResponse to send the file
    # media_type specifies the MIME type, text/plain for a .txt file
    # filename specifies the name the downloaded file will have
    return FileResponse(
        path=file_path,
        media_type="text/plain",
        filename="my_downloaded_file.txt"
    )


