import subprocess
import re
import os
import csv
from dateutil.parser import parse as parse_date
import datetime


class ZabbixSenderException(Exception):
    pass


class ZabbixSender(object):
    def __init__(self, sender_path, config_path):
        self.r_processed = re.compile('processed: (\d+);')
        self.r_failed = re.compile('failed: (\d+);')
        self.r_total = re.compile('total: (\d+);')
        self.sender_path = sender_path
        self.config_path = config_path

        self.last_command = None

    def _execute_sender(self, arguments):
        self.last_command = [self.sender_path, '-c', self.config_path] + arguments
        output, error = subprocess.Popen(
            self.last_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).communicate()
        if error: raise ZabbixSenderException(error)

        return output

    def _parse_output(self, output):
        processed_item_count = int(self.r_processed.search(str(output)).group(1))
        failed_item_count = int(self.r_failed.search(str(output)).group(1))
        total_item_count = int(self.r_total.search(str(output)).group(1))

        if failed_item_count:
            raise ZabbixSenderException('%i failed Items during %s' % (failed_item_count, self.last_command))
        if processed_item_count != total_item_count:
            raise ZabbixSenderException('Missmatching: %i != %i' % (processed_item_count, total_item_count))

    def send_item(self, name, value):
        self._parse_output(self._execute_sender(['-k', name, '-o', '%s' % value]))

        return '%s: %s' % (name, value)


class GpuStats(object):
    def __init__(self, eth_hashrate, temperature=None, fan_speed=None):
        self.eth_hashrate = eth_hashrate
        self.temperature = temperature
        self.fan_speed = fan_speed


class ClaymoreMinerStats(object):
    def __init__(self, json):
        self.version, runs_for_minutes, eth_mining_stats, eth_hashrates, dcr_mining_stats, dcr_hashrates, gpu_stats, \
        self.mining_pool, share_stats = json['result']

        eth_hashrates = eth_hashrates.split(';')
        stats = gpu_stats.split(';')
        if len(stats): assert (len(stats) == len(eth_hashrates) * 2)

        self.gpus = []
        for i, hashrate in enumerate(eth_hashrates):
            if stats:
                temperature = stats[i * 2]
                fan_speed = stats[i * 2 + 1]
                self.gpus.append(GpuStats(hashrate, temperature, fan_speed))
            else:
                self.gpus.append(GpuStats(hashrate))

        self.runs_for_minutes = int(runs_for_minutes)

        spl = eth_mining_stats.split(';')
        self.total_hashrate = int(spl[0])
        self.total_shares = int(spl[1])
        self.total_rejected_shares = int(spl[2])

        spl = share_stats.split(';')
        self.incorrect_shares = int(spl[0])


class Transaction(object):
    def __init__(self, transaction_id, some_data, timestamp, amount, fee=None):
        self.transaction_id = transaction_id
        self.some_data = some_data
        self.timestamp = timestamp
        self.amount = amount
        self.fee = fee

    def __repr__(self):
        return '<Transaction %s; %s; %s; %s; %s>' % (
            self.transaction_id, self.some_data, self.timestamp, self.amount, self.fee
        )

    def __eq__(self, other):
        return self.transaction_id == other.transaction_id \
               and self.some_data == other.some_data \
               and self.timestamp == other.timestamp \
               and self.amount == other.amount \
               and self.fee == other.fee


class Factory(object):
    @staticmethod
    def from_triple(triple, some_data):
        return Transaction(
            triple[2].get_text(),
            some_data,
            parse_date(triple[0].get_text()),
            triple[1].get_text()
        )

    @staticmethod
    def from_kraken(id, trade):
        return Transaction(
            id,
            trade['vol'],
            datetime.datetime.fromtimestamp(trade['closetm']),
            trade['cost'],
            trade['fee']
        )

    @staticmethod
    def from_csv(row):
        return Transaction(row[0], row[1], parse_date(row[2]), row[3], row[4] if len(row) > 4 else None)


def sync_to_csv(csv_filename, data):
    factory = Factory()
    if os.path.exists(csv_filename):
        for row in csv.reader(open(csv_filename, 'rb')):
            transaction = factory.from_csv(row)
            if transaction not in data:
                data.append(transaction)

    data = sorted(data, key=lambda elem: elem.timestamp)

    fp = csv.writer(open(csv_filename, 'wb'))
    for transaction in data:
        fp.writerow([
            transaction.transaction_id,
            transaction.some_data,
            transaction.timestamp,
            transaction.amount,
            transaction.fee if transaction.fee else ''
        ])
