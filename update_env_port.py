
import os

env_path = r"backend\.env"

with open(env_path, "r") as f:
    lines = f.readlines()

with open(env_path, "w") as f:
    for line in lines:
        if "WHATSAPP_API_URL=" in line:
            f.write("WHATSAPP_API_URL=http://localhost:3001/send\n")
        else:
            f.write(line)
            
print("ENV ATUALIZADO")
