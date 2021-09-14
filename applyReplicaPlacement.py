#!/usr/bin/env python
#
# Copyright 2018 Confluent Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from confluent_kafka.admin import AdminClient, NewTopic, NewPartitions, ConfigResource, ConfigSource
from confluent_kafka import KafkaException
import json
import sys
import threading
import logging

logging.basicConfig()

def delta_alter_configs(adminClient, resources):
    """
    The AlterConfigs Kafka API requires all configuration to be passed,
    any left out configuration properties will revert to their default settings.
    This example shows how to just modify the supplied configuration entries
    by first reading the configuration from the broker, updating the supplied
    configuration with the broker configuration (without overwriting), and
    then writing it all back.
    The async nature of futures is also show-cased, which makes this example
    a bit more complex than it needs to be in the synchronous case.
    """

    # Set up a locked counter and an Event (for signaling) to track when the
    # second level of futures are done. This is a bit of contrived example
    # due to no other asynchronous mechanism being used, so we'll need
    # to wait on something to signal completion.

    class WaitZero(object):
        def __init__(self, waitcnt):
            self.cnt = waitcnt
            self.lock = threading.Lock()
            self.event = threading.Event()

        def decr(self):
            """ Decrement cnt by 1"""
            with self.lock:
                assert self.cnt > 0
                self.cnt -= 1
            self.event.set()

        def wait(self):
            """ Wait until cnt reaches 0 """
            self.lock.acquire()
            while self.cnt > 0:
                self.lock.release()
                self.event.wait()
                self.event.clear()
                self.lock.acquire()
            self.lock.release()

        def __len__(self):
            with self.lock:
                return self.cnt

    wait_zero = WaitZero(len(resources))

    # Read existing configuration from cluster
    fs = adminClient.describe_configs(resources)

    def delta_alter_configs_done(fut, resource):
        e = fut.exception()
        if e is not None:
            print("Config update for {} failed: {}".format(resource, e))
        else:
            print("Config for {} updated".format(resource))
        wait_zero.decr()

    def delta_alter_configs(resource, remote_config):
        print("Updating {} supplied config entries {} with {} config entries read from cluster".format(
            len(resource), resource, len(remote_config)))
        # Only set configuration that is not default
        for k, entry in [(k, v) for k, v in remote_config.items() if not v.is_default]:
            resource.set_config(k, entry.value, overwrite=False)

        fs = adminClient.alter_configs([resource])
        fs[resource].add_done_callback(lambda fut: delta_alter_configs_done(fut, resource))

    # For each resource's future set up a completion callback
    # that in turn calls alter_configs() on that single resource.
    # This is ineffective since the resources can usually go in
    # one single alter_configs() call, but we're also show-casing
    # the futures here.
    for res, f in fs.items():
        f.add_done_callback(lambda fut, resource=res: delta_alter_configs(resource, fut.result()))

    # Wait for done callbacks to be triggered and operations to complete.
    print("Waiting for {} resource updates to finish".format(len(wait_zero)))
    wait_zero.wait()


def ApplyReplicaPlacement(adminClient, replicaPlacement, minISR, args):

    clusterInternalTopicOnly = 0

    # Apply to internal topic only
    if "--cluster-internal-only" in args:
        print("Applies to internal topics only...")
        clusterInternalTopicOnly = 1

    md = adminClient.list_topics(timeout=30)

    print("Cluster {} metadata (response from broker {}):".format(md.cluster_id, md.orig_broker_name))
    print("Replica Placement Strategy: {}".format(replicaPlacement))
    resources = []

    for t in iter(md.topics.values()):
        if t.error is not None:
            errstr = ": {}".format(t.error)
        else:
            errstr = ""

        if clusterInternalTopicOnly==1:
            if (str(t).startswith("__")):
                print("Internal topic found: {}".format(str(t)))
                r = ConfigResource("Topic", str(t))
                r.set_config("confluent.placement.constraints", replicaPlacement)
                r.set_config("min.insync.replicas", minISR)
                resources.append(r)
        else:
            print("Internal topic found: {}".format(str(t)))
            r = ConfigResource("Topic", str(t))
            r.set_config("confluent.placement.constraints", replicaPlacement)
            r.set_config("min.insync.replicas", minISR)
            resources.append(r)

    if len(resources) > 0:
        print("Applying replica placement to {} Topics...".format(len(resources)))
        delta_alter_configs(adminClient, resources)

if __name__ == '__main__':
    # if len(sys.argv) < 4:
    #      sys.stderr.write('Usage: %s {Replica Placement Strategy.json} {min.insync.replica}\n\n' % sys.argv[0])
    #      sys.exit(1)

    with open('conf.json', 'r') as admin_config:
        conf=admin_config.read()
    confObj = json.loads(conf)

    with open(sys.argv[1], 'r') as replica_placement_strategy:
        replicaPlacement=replica_placement_strategy.read()

    minISR = sys.argv[2]

    args = sys.argv[3:]

    # Create Admin client
    adminClient = AdminClient(confObj)

    ApplyReplicaPlacement(adminClient, replicaPlacement, minISR, args)
