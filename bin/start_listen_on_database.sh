LOG_FILE=/var/log/nacos-syncer/start_listen_on_database.log
true > ${LOG_FILE}
nohup /usr/local/bin/python3 /srv/nacos-jmeter/bin/listen_on_database.py >> ${LOG_FILE} 2>&1 &