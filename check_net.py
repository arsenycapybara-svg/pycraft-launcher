import requests

URLS = [
    "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json",
    "https://piston-data.mojang.com/",
    "https://libraries.minecraft.net/",
    "https://resources.download.minecraft.net/",
    "https://launcher.mojang.com/",
    "https://meta.fabricmc.net/v2/versions/loader",
    "https://maven.fabricmc.net/",
    "https://maven.minecraftforge.net/",
]

for url in URLS:
    try:
        r = requests.get(url, timeout=15)
        print(f"OK   {r.status_code}  {url}")
    except Exception as e:
        print(f"FAIL {type(e).__name__}: {e}\n     {url}")