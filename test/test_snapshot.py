import os
import settings
import snapshot

if __name__ == "__main__":
    n = snapshot.Nacos(settings.HOST_CI, settings.PORT)
    n.make_snapshot(os.path.join(os.path.dirname(os.path.dirname(__file__)), "snapshot"))