#coding:utf8
from kafka import KafkaConsumer

consumer = KafkaConsumer(
    '$topic_name',
    group_id = "$group_id",
    bootstrap_servers = ['$ip:$port'],
    security_protocol = "SASL_PLAINTEXT",
    sasl_mechanism = 'PLAIN',
    sasl_plain_username = "$instance_id#$username",
    sasl_plain_password = "$password",
    api_version = (0, 10, 0))

for message in consumer:
    print ("Topic:[%s] Partition:[%d] Offset:[%d] Value:[%s]" %
    (message.topic, message.partition, message.offset, message.value))
