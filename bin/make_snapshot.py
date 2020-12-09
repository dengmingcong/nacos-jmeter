import sys
sys.path.append("../nacos-jmeter")

from nacos import Nacos
import settings


snapshot_dir = sys.argv[1]
nacos_new = Nacos(settings.HOST, settings.PORT)
nacos_new.make_snapshot(snapshot_dir)
