## 操作场景

该任务指导您在 VPC 环境下使用 Node.js SDK 接入 CKafka 的默认接入点并收发消息。

## 前提条件

- [安装 GCC](https://gcc.gnu.org/install/)
- [安装 Node.js](https://nodejs.org/en/download/)

## 操作步骤

#### 步骤一：安装C++依赖库

1. 执行以下命令切换到yum源配置目录/etc/yum.repos.d/

   ```bash
   cd /etc/yum.repos.d/
   ```

1. 创建yum源配置文件confluent.repo。

   ```bash
   [Confluent.dist]
   name=Confluent repository (dist)
   baseurl=https://packages.confluent.io/rpm/5.1/7
   gpgcheck=1
   gpgkey=https://packages.confluent.io/rpm/5.1/archive.key
   enabled=1   
   [Confluent]
   name=Confluent repository
   baseurl=https://packages.confluent.io/rpm/5.1
   gpgcheck=1
   gpgkey=https://packages.confluent.io/rpm/5.1/archive.key
   enabled=1
   ```

1. 执行以下命令安装C++依赖库。

    ```bash
    yum install librdkafka-devel
    ```

#### 步骤二：安装Node.js依赖库

1. 执行以下命令为预处理器指定OpenSSL头文件路径。

    ```bash
    export CPPFLAGS=-I/usr/local/opt/openssl/include
    ```

1. 执行以下命令为连接器指定OpenSSL库路径。

    ```bash
    export LDFLAGS=-L/usr/local/opt/openssl/lib
    ```

1. 执行以下命令安装Node.js依赖库。

    ```bash
    npm install i --unsafe-perm node-rdkafka
    ```

#### 步骤三：准备配置
创建消息队列CKafka配置文件setting.js。

```js
module.exports = {
    'bootstrap_servers': ["xxx.ckafka.tencentcloudmq.com:6018"],
    'topic_name': 'xxx',
    'group_id': 'xxx'
}
```


| 参数              | 描述                                                         |
| ----------------- | ------------------------------------------------------------ |
| bootstrap_servers | 默认接入点，在CKafka控制台实例详情页面的【基本信息】>【接入方式】或【内网IP与端口】获取 |
| topic_name        | Topic名称，您可在消息队列CKafka控制台的Topic管理页面获取。   |
| group_id          | 消费者的组 Id，根据业务需求自定义                            |

#### 步骤四：发送消息

1. 编写生产消息程序 producer.js

    ```js
    const Kafka = require('node-rdkafka');
    const config = require('./setting');
    console.log("features:" + Kafka.features);
    console.log(Kafka.librdkafkaVersion);

    var producer = new Kafka.Producer({
        'api.version.request': 'true',
        // 设置入口服务，请通过控制台获取对应的服务地址。
        'bootstrap.servers': config['bootstrap_servers'],
        'dr_cb': true,
        'dr_msg_cb': true,

        // 请求发生错误时重试次数，建议将该值设置为大于0，失败重试最大程度保证消息不丢失
        'retries': '0',
        // 发送请求失败时到下一次重试请求之间的时间
        "retry.backoff.ms": 100,
        // producer 网络请求的超时时间。
        'socket.timeout.ms': 6000,
    });

    var connected = false

    producer.setPollInterval(100);

    producer.connect();
    
    producer.on('ready', function() {
    connected = true
    console.log("connect ok")
    });
    
    producer.on("disconnected", function() {
    connected = false;
    producer.connect();
    })
    
    producer.on('event.log', function(event) {
        console.log("event.log", event);
    });
    
    producer.on("error", function(error) {
        console.log("error:" + error);
    });
    
    function produce() {
        try {
            producer.produce(
            config['topic_name'],   
            null,      
            new Buffer('Hello CKafka Default'),      
            null,   
            Date.now()
            );
        } catch (err) {
            console.error('Error occurred when sending message(s)');
            console.error(err);
        }
    
    }
    
    producer.on('delivery-report', function(err, report) {
        console.log("delivery-report: producer ok");
    });
    
    producer.on('event.error', function(err) {
        console.error('event.error:' + err);
    })
    
    setInterval(produce, 1000, "Interval");
    
    ```

2. 执行以下命令发送消息。

    ```bash
    node producer.js
    ```

3. 查看运行结果。

   ![](https://main.qcloudimg.com/raw/195f4aee06ba86755407b4a75812c256.png)

4. 在CKafka控制台【topic管理】页面，选择对应的 topic ， 点击【更多】>【消息查询】，查看刚刚发送的消息。

   ![](https://main.qcloudimg.com/raw/e20a0809942f90e0efd5fd1f217574b0.png)

#### 步骤五：订阅消息

1. 创建消费消息程序consumer.js。

    ```js
    const Kafka = require('node-rdkafka');
    const config = require('./setting');
    console.log(Kafka.features);
    console.log(Kafka.librdkafkaVersion);
    console.log(config)

    var consumer = new Kafka.KafkaConsumer({
        'api.version.request': 'true',
        // 设置入口服务，请通过控制台获取对应的服务地址。
        'bootstrap.servers': config['bootstrap_servers'],
        'group.id' : config['group_id'],

        // 使用 Kafka 消费分组机制时，消费者超时时间。当 Broker 在该时间内没有收到消费者的心跳时，
        // 认为该消费者故障失败，Broker 发起重新 Rebalance 过程。
        'session.timeout.ms': 10000,
        // 客户端请求超时时间，如果超过这个时间没有收到应答，则请求超时失败
        'metadata.request.timeout.ms': 305000,
        // 设置客户端内部重试间隔。
        'reconnect.backoff.max.ms': 3000

    });

    consumer.connect();

    consumer.on('ready', function() {
    console.log("connect ok");
    consumer.subscribe([config['topic_name']]);
    consumer.consume();
    })

    consumer.on('data', function(data) {
    console.log(data);
    });
    
    consumer.on('event.log', function(event) {
        console.log("event.log", event);
    });
    
    consumer.on('error', function(error) {
        console.log("error:" + error);
    });
    
    consumer.on('event', function(event) {
            console.log("event:" + event);
    });
    ```

2. 执行以下命令消费消息。

   ```bash
   node consumer.js
   ```

3. 查看运行结果

   ![](https://main.qcloudimg.com/raw/deecbf58c00e07531b4ea703c4046b46.png)

4. 在CKafka控制台【Consumer Group】页面，选择对应的消费组名称，在主题名称输入topic名称，点击【查询详情】，查看消费详情。

   ![](https://main.qcloudimg.com/raw/3020dcb5f8fd73e02949b20fef4f956f.png)