import sys
import time
import urllib.request

deadline = time.monotonic() + 40
while time.monotonic() < deadline:
    try:
        with urllib.request.urlopen(sys.argv[1], timeout=2) as result:
            if result.status == 200:
                print("Servicio listo")
                break
    except OSError:
        pass
    time.sleep(0.5)
else:
    raise SystemExit("Servicio no disponible tras 40 segundos")
