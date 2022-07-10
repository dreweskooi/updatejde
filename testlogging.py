import logging

log = logging.getLogger("application")
sh = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "", "%")
sh.setFormatter(formatter)
log.addHandler(sh)
txt = logging.FileHandler('logging.txt')
txt.setFormatter(formatter)

log.addHandler(txt)
log.setLevel(logging.DEBUG)
log.info("Starting application")