# 默认接入点收发消息

本文介绍如何在VPC环境下使用Java SDK接入消息队列CKafka版的默认接入点并收发消息。



#### 前提条件

- [安装1.8或以上版本JDK](https://www.oracle.com/java/technologies/javase-downloads.html)
- [安装2.5或以上版本Maven](http://maven.apache.org/download.cgi#)



#### 添加Java依赖库

在pom.xml中添加以下依赖。

```java
<dependency>
    <groupId>org.apache.kafka</groupId>
    <artifactId>kafka-clients</artifactId>
    <version>0.10.2.2</version>
</dependency>
```



#### 准备配置

- 创建消息队列Kafka版配置文件kafka.properties。

  ```
  ## 配置接入点，即控制台的实例详情页面显示的接入点。
  bootstrap.servers=xxxxxxxxxxxxxxxxxxxxx
  ## 配置Topic，可以在控制台上创建Topic。
  topic=ckafka-topic-demo
  ## 配置Consumer Group.
  group.id=ckafka-consumer-group-demo
  ```

- 创建配置文件加载程序CKafkaConfigurer.java。

  ```java
  public class CKafkaConfigurer {
  
      private static Properties properties;
  
      public synchronized static Properties getCKafkaProperties() {
          if (null != properties) {
              return properties;
          }
          //获取配置文件kafka.properties的内容。
          Properties kafkaProperties = new Properties();
          try {
              kafkaProperties.load(CKafkaProducerDemo.class.getClassLoader().getResourceAsStream("kafka.properties"));
          } catch (Exception e) {
              System.out.println("getCKafkaProperties error");
          }
          properties = kafkaProperties;
          return kafkaProperties;
      }
  }
  
  ```



#### 发送消息

- 编写生产消息程序CKafkaProducerDemo.java

  ```java
  public class CKafkaProducerDemo {
  
      public static void main(String args[]) {
          //加载kafka.properties。
          Properties kafkaProperties = CKafkaConfigurer.getCKafkaProperties();
  
          Properties properties = new Properties();
          //设置接入点，请通过控制台获取对应Topic的接入点。
          properties.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, kafkaProperties.getProperty("bootstrap.servers"));
  
          //消息队列Kafka版消息的序列化方式, 此处demo 使用的是StringSerializer。
          properties.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG,
                  "org.apache.kafka.common.serialization.StringSerializer");
          properties.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG,
                  "org.apache.kafka.common.serialization.StringSerializer");
          //请求的最长等待时间。
          properties.put(ProducerConfig.MAX_BLOCK_MS_CONFIG, 30 * 1000);
          //设置客户端内部重试次数。
          properties.put(ProducerConfig.RETRIES_CONFIG, 5);
          //设置客户端内部重试间隔。
          properties.put(ProducerConfig.RECONNECT_BACKOFF_MS_CONFIG, 3000);
          //构造Producer对象。
          KafkaProducer<String, String> producer = new KafkaProducer<>(properties);
  
          //构造一个消息队列Kafka版消息。
          String topic = kafkaProperties.getProperty("topic"); //消息所属的Topic，请在控制台申请之后，填写在这里。
          String value = "this is ckafka msg value"; //消息的内容。
  
          try {
              //批量获取Future对象可以加快速度, 但注意, 批量不要太大。
              List<Future<RecordMetadata>> futureList = new ArrayList<>(128);
              for (int i = 0; i < 10; i++) {
                  //发送消息，并获得一个Future对象。
                  ProducerRecord<String, String> kafkaMsg = new ProducerRecord<>(topic,
                          value + ": " + i);
                  Future<RecordMetadata> metadataFuture = producer.send(kafkaMsg);
                  futureList.add(metadataFuture);
  
              }
              producer.flush();
              for (Future<RecordMetadata> future : futureList) {
                  //同步获得Future对象的结果。
                  RecordMetadata recordMetadata = future.get();
                  System.out.println("produce send ok: " + recordMetadata.toString());
              }
          } catch (Exception e) {
              //客户端内部重试之后，仍然发送失败，业务要应对此类错误。
              System.out.println("error occurred");
          }
      }
  }
  ```

- 编译并运行CKafkaProducerDemo.java发送消息。

- 运行结果(输出)

```bash
Produce ok:ckafka-topic-demo-0@198
Produce ok:ckafka-topic-demo-0@199

```

#### 消费消息

- 创建单个Consumer订阅消息程序CKafkaConsumerDemo.java。

  ```java
  public class CKafkaConsumerDemo {
  
      public static void main(String args[]) {
          //加载kafka.properties。
          Properties kafkaProperties = CKafkaConfigurer.getCKafkaProperties();
  
          Properties props = new Properties();
          //设置接入点，请通过控制台获取对应Topic的接入点。
          props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, kafkaProperties.getProperty("bootstrap.servers"));
          //两次Poll之间的最大允许间隔。
          //消费者超过该值没有返回心跳，服务端判断消费者处于非存活状态，服务端将消费者从Consumer Group移除并触发Rebalance，默认30s。
          props.put(ConsumerConfig.SESSION_TIMEOUT_MS_CONFIG, 30000);
          //每次Poll的最大数量。
          //注意该值不要改得太大，如果Poll太多数据，而不能在下次Poll之前消费完，则会触发一次负载均衡，产生卡顿。
          props.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, 30);
          //消息的反序列化方式。
          props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG,
                  "org.apache.kafka.common.serialization.StringDeserializer");
          props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG,
                  "org.apache.kafka.common.serialization.StringDeserializer");
          //属于同一个组的消费实例，会负载消费消息。
          props.put(ConsumerConfig.GROUP_ID_CONFIG, kafkaProperties.getProperty("group.id"));
          //构造消费对象，也即生成一个消费实例。
          KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props);
          //设置消费组订阅的Topic，可以订阅多个。
          //如果GROUP_ID_CONFIG是一样，则订阅的Topic也建议设置成一样。
          List<String> subscribedTopics = new ArrayList<>();
          //如果需要订阅多个Topic，则在这里添加进去即可。
          //每个Topic需要先在控制台进行创建。
          String topicStr = kafkaProperties.getProperty("topic");
          String[] topics = topicStr.split(",");
          for (String topic : topics) {
              subscribedTopics.add(topic.trim());
          }
          consumer.subscribe(subscribedTopics);
  
          //循环消费消息。
          while (true) {
              try {
                  ConsumerRecords<String, String> records = consumer.poll(1000);
                  //必须在下次Poll之前消费完这些数据, 且总耗时不得超过SESSION_TIMEOUT_MS_CONFIG。
                  //建议开一个单独的线程池来消费消息，然后异步返回结果。
                  for (ConsumerRecord<String, String> record : records) {
                      System.out.println(
                              String.format("Consume partition:%d offset:%d", record.partition(), record.offset()));
                  }
              } catch (Exception e) {
                  System.out.println("consumer error!");
              }
          }
      }
  }
  ```
- 编译并运行CKafkaConsumerDemo.java 消费消息。

- 运行结果(输出)

```bash

Consume partition:0 offset:298
Consume partition:0 offset:299

```
  

