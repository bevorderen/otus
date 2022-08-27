#!/usr/bin/env python
# -*- coding: utf-8 -*-
import collections
import glob
import gzip
import logging
import os
import sys
import time
from multiprocessing import Process, Queue
from optparse import OptionParser
# pip install python-memcached
from queue import Empty
from typing import List

import memcache

# brew install protobuf
# protoc  --python_out=. ./appsinstalled.proto
# pip install protobuf
import appsinstalled_pb2

NORMAL_ERR_RATE = 0.01
AppsInstalled = collections.namedtuple("AppsInstalled", ["dev_type", "dev_id", "lat", "lon", "apps"])
SOCKET_TIMEOUT = 5
DELAY = 1
RETRIES = 5
QUEUE_TIMEOUT = 0.1
CHUNK_SIZE = 500
END_FILE = "end_file"
SENTINEL = "stop"


class Worker(Process):
    def __init__(self, queue: Queue, memc_addr: str, dry_run: bool):
        super().__init__()
        self.queue = queue
        self.memc_addr = memc_addr
        self.dry_run = dry_run  # think
        self.client = memcache.Client([memc_addr], socket_timeout=SOCKET_TIMEOUT)

    def map_apps_to_dict(self, chunk: List):
        result = dict()
        for app in chunk:
            ua = appsinstalled_pb2.UserApps()
            ua.lat = app.lat
            ua.lon = app.lon
            key = "%s:%s" % (app.dev_type, app.dev_id)
            ua.apps.extend(app.apps)
            packed = ua.SerializeToString()
            result[key] = packed
        return result

    def set_multi(self, chunk: List):
        if self.dry_run:
            logging.debug(f"{self.memc_addr} set {len(chunk)} keys")
            return

        chunk_dict = self.map_apps_to_dict(chunk=chunk)
        bad_keys = self.client.set_multi(chunk_dict)
        current_try = RETRIES
        while bad_keys and current_try:
            new_chunk_dict = {k: v for k, v in chunk_dict if k in bad_keys}
            bad_keys = self.client.set_multi(new_chunk_dict)
            current_try = - 1
            time.sleep(DELAY*current_try)

        if bad_keys:
            logging.debug(f"Have bad keys size = {len(bad_keys)}. They skipped")

        def run(self) -> None:
            end = False
            chunk = []

            while end:
                try:
                    task = self.queue.get(timeout=QUEUE_TIMEOUT)
                except Empty:
                    continue

                is_end_file = task == END_FILE
                end = task == SENTINEL

                if not (is_end_file or end):
                    chunk.append(task)

                if len(chunk) == CHUNK_SIZE or is_end_file:
                    self.set_multi(chunk)
                    chunk = []

                if is_end_file:
                    logging.debug("end file")

            if chunk:
                self.set_multi(chunk)

    def stop(self):
        self.queue.put(SENTINEL)

def dot_rename(path):
    head, fn = os.path.split(path)
    # atomic in most cases
    os.rename(path, os.path.join(head, "." + fn))


def parse_appsinstalled(line):
    line_parts = line.strip().split("\t")
    if len(line_parts) < 5:
        return
    dev_type, dev_id, lat, lon, raw_apps = line_parts
    if not dev_type or not dev_id:
        return
    try:
        apps = [int(a.strip()) for a in raw_apps.split(",")]
    except ValueError:
        apps = [int(a.strip()) for a in raw_apps.split(",") if a.isidigit()]
        logging.info("Not all user apps are digits: `%s`" % line)
    try:
        lat, lon = float(lat), float(lon)
    except ValueError:
        logging.info("Invalid geo coords: `%s`" % line)
    return AppsInstalled(dev_type, dev_id, lat, lon, apps)


def main(options):
    device_memc = {
        "idfa": options.idfa,
        "gaid": options.gaid,
        "adid": options.adid,
        "dvid": options.dvid,
    }

    workers = {
        dev_type: Worker(queue=Queue(), memc_addr=memc_addr, dry_run=options.dry_run)
        for dev_type, memc_addr in device_memc.items()
    }

    for worker in workers.values():
        worker.start()

    for fn in glob.iglob(options.pattern):
        processed = errors = 0
        logging.info('Processing %s' % fn)
        fd = gzip.open(fn)
        try:
            for line in fd:
                line = line.decode("utf-8").strip()
                if not line:
                    continue

                appsinstalled = parse_appsinstalled(line)
                if not appsinstalled:
                    errors += 1
                    continue

                memc_addr = device_memc.get(appsinstalled.dev_type)
                if not memc_addr:
                    errors += 1
                    logging.error("Unknown device type: %s" % appsinstalled.dev_type)
                    continue

                processed += 1

                workers[appsinstalled.dev_type].queue.put(appsinstalled)

            for worker in workers.values():
                worker.queue.put(END_FILE)

            if processed:
                err_rate = float(errors) / processed
                if err_rate < NORMAL_ERR_RATE:
                    logging.info("Acceptable error rate (%s). Successful load" % err_rate)
                else:
                    logging.error("High error rate (%s > %s). Failed load" % (err_rate, NORMAL_ERR_RATE))

            # dot_rename(fn)
        finally:
            fd.close()
        # dot_rename(fn)
    for worker in workers.values():
        worker.stop()


def prototest():
    sample = "idfa\t1rfw452y52g2gq4g\t55.55\t42.42\t1423,43,567,3,7,23\ngaid\t7rfw452y52g2gq4g\t55.55\t42.42\t7423,424"
    for line in sample.splitlines():
        dev_type, dev_id, lat, lon, raw_apps = line.strip().split("\t")
        apps = [int(a) for a in raw_apps.split(",") if a.isdigit()]
        lat, lon = float(lat), float(lon)
        ua = appsinstalled_pb2.UserApps()
        ua.lat = lat
        ua.lon = lon
        ua.apps.extend(apps)
        packed = ua.SerializeToString()
        unpacked = appsinstalled_pb2.UserApps()
        unpacked.ParseFromString(packed)
        assert ua == unpacked


if __name__ == '__main__':
    op = OptionParser()
    op.add_option("-t", "--test", action="store_true", default=False)
    op.add_option("-l", "--log", action="store", default=None)
    op.add_option("--dry_run", action="store_true", default=False)
    op.add_option("--pattern", action="store", default="/data/appsinstalled/*.tsv.gz")
    op.add_option("--idfa", action="store", default="127.0.0.1:33013")
    op.add_option("--gaid", action="store", default="127.0.0.1:33014")
    op.add_option("--adid", action="store", default="127.0.0.1:33015")
    op.add_option("--dvid", action="store", default="127.0.0.1:33016")
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO if not opts.dry_run else logging.DEBUG,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    if opts.test:
        prototest()
        sys.exit(0)

    logging.info("Memc loader started with options: %s" % opts)

    try:
        main(opts)
    except Exception as e:
        logging.exception("Unexpected error: %s" % e)
        sys.exit(1)
