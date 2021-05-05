LOG_FILE=/var/log/nacos-syncer/start_listen_on_database.log
true > ${LOG_FILE}
while
    ! systemctl is-active --quiet nacos.service
do
    echo "Service Nacos is not active now, wait for a moment" >> ${LOG_FILE}
    sleep 10
done

echo "Service Nacos is active now, begin to listen" >> ${LOG_FILE}
sleep 30
nohup /usr/local/bin/python3 /srv/nacos-jmeter/bin/listen_on_database.py >> ${LOG_FILE} 2>&1 &