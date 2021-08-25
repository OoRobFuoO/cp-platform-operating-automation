# cp-platform-operating-automation
Automation script to support Confluent Platform operation

## Requirements

* Python 2.7 or above
* [Confluent Python Client](https://github.com/confluentinc/confluent-kafka-python)

## Starter guide

This project contains various assistance scripts (currently only 1) to automate Confluent Platform operation.

To use the script, update the `conf.json` with the appropriate client properties to connect to the target cluster. The default example only contains the following, which may work with most of the local cluster setup for trial and testing purpose:
```
{
  "bootstrap.servers": "localhost:9092"
}
```

## maintain_minisr.py

This script will help platform team to maintain topic min.insync.replica (min.ISR) setting to support operating the platform at degraded mode by identify how many replicas do not have sufficient ISR due to too many brokers are offline.

This script will attempt to recover the topic min.insync.replica to a pre-defined health value from degraded mode when all the broker is online and replicas has sufficient ISR.

The example will instruct the script to reduce topic min.ISR to 2 when there at degraded state to maintain availablity to producer and recover it back to 3 when all the brokers are online and all topic replicas are back to a healthy status.

```
python3 maintain_minisr.py 4 4 3 2
```

## Parameters explanation

* 1st parameter - Total number of brokers in the cluster when healthy
* 2nd parameter - Default replication factor
* 3rd parameter - min.insync.replica when the cluster is healthy
* 4th parameter - min.insync.replica when the cluster is at degraded state

### Improvements

* Support inclusion and exclusion topic
* Support force apply mode
