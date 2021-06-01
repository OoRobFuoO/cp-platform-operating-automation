# cp-platform-operating-automation
Automation script to support Confluent Platform operation

## maintain_minisr.py

This script will help platform team to maintain topic min.insync.replica setting to support operating the platform at degraded mode by identify how many replicas do not have sufficient ISR due to too many brokers are offline.

This script will attempt to recover the topic min.insync.replica to a pre-defined health value from degraded mode when all the broker is online and replicas has sufficient ISR.

### Improvements

* Support defining broker properties from a file. Currently only support bootstrap-server
* Support inclusion and exclusion topic
* Support force apply mode
