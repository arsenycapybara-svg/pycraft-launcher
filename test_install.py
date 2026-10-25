import traceback
import minecraft_launcher_lib as mll

try:
    mll.install.install_minecraft_version(
        "1.20.1",
        "/tmp/mc-test",
        callback={
            "setStatus": print,
            "setProgress": lambda v: None,
            "setMax": lambda v: None,
        },
    )
    print("УСПЕХ")
except Exception:
    traceback.print_exc()