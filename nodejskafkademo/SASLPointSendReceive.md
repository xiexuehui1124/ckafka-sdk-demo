## 操作场景

该任务指导您在 VPC 环境下使用 Node.js SDK 接入 CKafka 的SASL接入点并使用PLAIN机制并收发消息。

## 前提条件

- [安装 GCC](https://gcc.gnu.org/install/)
- [安装 Node.js](https://nodejs.org/en/download/)
- [配置ACL策略](https://cloud.tencent.com/document/product/597/31528)

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
    'sasl_plain_username': 'ckafka-xxxxxxx#ckafkademo',
    'sasl_plain_password': 'ckafkademo123',
    'bootstrap_servers': ["xxx.ckafka.tencentcloudmq.com:6018"],
    'topic_name': 'xxx',
    'group_id': 'xxx'
}
```


| 参数              | 描述                                                                                    |
| ----------------- | --------------------------------------------------------------------------------------- |
| sasl_plain_username | 用户名，格式为 `实例 ID` + `#` + `用户名`。实例 ID 在 [CKafka 控制台](https://console.cloud.tencent.com/ckafka) 的实例详情页面的基本信息获取，用户在【用户管理】创建用户时设置 |
| sasl_plain_password | 用户密码，在CKafka控制台实例详情页面的【用户管理】创建用户时设置 |
| bootstrap_servers | SASL接入点，在CKafka控制台的实例详情页面的【基本信息】>【接入方式】获取 |
| topic_name | Topic名称，在CKafka控制台实例详情页面的【topic管理】创建和获取 |
| group_id | 消费者的组 Id，根据业务需求自定义 |

#### 发送消息

1. 编写生产消息程序 producer.js

    ```js
    const Kafka = require('node-rdkafka');
    const config = require('./setting');
    console.log("features:" + Kafka.features);
    console.log(Kafka.librdkafkaVersion);

    var producer = new Kafka.Producer({
        'api.version.request': 'true',
        'bootstrap.servers': config['bootstrap_servers'],
        'dr_cb': true,
        'dr_msg_cb': true,
        'security.protocol' : 'SASL_PLAINTEXT',
        'sasl.mechanisms' : 'PLAIN',
        'sasl.username' : config['sasl_plain_username'],
        'sasl.password' : config['sasl_plain_password']
    });

    var connected = false

    producer.setPollInterval(100);

    producer.connect();

    producer.on('ready', function() {
    connected = true
    console.log("connect ok")

    });

    function produce() {
    try {
        producer.produce(
        config['topic_name'],
        new Buffer('Hello CKafka SASL'),
        null,
        Date.now()
        );
    } catch (err) {
        console.error('Error occurred when sending message(s)');
        console.error(err);
    }
    }

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

    producer.on('delivery-report', function(err, report) {
        console.log("delivery-report: producer ok");
    });
    // Any errors we encounter, including connection errors
    producer.on('event.error', function(err) {
        console.error('event.error:' + err);
    })

    setInterval(produce,1000,"Interval");

    ```

2. 执行以下命令发送消息。

    ```bash
    node producer.js
    ```

3. 查看运行结果。

   ![](https://main.qcloudimg.com/raw/195f4aee06ba86755407b4a75812c256.png)

4. 在CKafka控制台【topic管理】页面，选择对应的 topic ， 点击【更多】>【消息查询】，查看刚刚发送的消息。

   ![](https://main.qcloudimg.com/raw/e20a0809942f90e0efd5fd1f217574b0.png)

#### 订阅消息

1. 创建消费消息程序consumer.js。

    ```js
    
    
    consumer.on('event.log', function(event) {
        console.log("event.log", event);
    });

    consumer.on('error', function(error) {
        console.log("error:" + error);
    });
    
    consumer.on('event', function(event) {
            console.log("event:" + event);
    });const Kafka = require('node-rdkafka');
    const config = require('./setting');
    console.log(Kafka.features);
    console.log(Kafka.librdkafkaVersion);
    console.log(config)
    
var consumer = new Kafka.KafkaConsumer({
        'api.version.request': 'true',
    'bootstrap.servers': config['bootstrap_servers'],
        'security.protocol' : 'SASL_PLAINTEXT',
        'sasl.mechanisms' : 'PLAIN',
        'message.max.bytes': 32000,
        'fetch.message.max.bytes': 32000,
        'max.partition.fetch.bytes': 32000,
    'sasl.username' : config['sasl_plain_username'],
        'sasl.password' : config['sasl_plain_password'],
        'group.id' : config['group_id']
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

3. 查看运行结果。

   ![](https://main.qcloudimg.com/raw/deecbf58c00e07531b4ea703c4046b46.png)

4. 在CKafka控制台【Consumer Group】页面，选择对应的消费组名称，在主题名称输入topic名称，点击【查询详情】，查看消费详情。

   ![](https://main.qcloudimg.com/raw/3020dcb5f8fd73e02949b20fef4f956f.png)