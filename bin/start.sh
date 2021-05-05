true > /var/log/nacos-syncer/start.log
while
    ! systemctl is-active --quiet nacos.service
do
    echo "Service Nacos is not active now, wait for a moment" >> /var/log/nacos-syncer/start.log
    sleep 10
done

echo "Service Nacos is active now, begin to listen" >> /var/log/nacos-syncer/start.log
sleep 30
nohup /usr/local/bin/python3 /srv/nacos-jmeter/bin/listen_nacos.py >> /var/log/nacos-syncer/start.log 2>&1 &