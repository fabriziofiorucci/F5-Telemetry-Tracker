import os
import sys
from clickhouse_driver import Client as ClickHouse

this = sys.modules[__name__]

this.ch_host=''
this.ch_port=0
this.ch_user=''
this.ch_pass=''
this.ch=''

# Initialization
def init(ch_host, ch_port, ch_user, ch_pass):
  this.ch_host=ch_host
  this.ch_port=ch_port
  this.ch_user=ch_user
  this.ch_pass=ch_pass

  print('Initializing ClickHouse [',this.ch_host,':',this.ch_port,']')
  try:
    connect()
    execute('create database if not exists f5tt')
    execute(' \
      create table if not exists f5tt.tracking (\
        `ts` DateTime CODEC(DoubleDelta), \
        `data` LowCardinality(String) \
      ) \
      ENGINE = MergeTree() \
      order by ts \
    ')
    close()
  except:
    sys.exit('ClickHouse exception')

  return True


# ClickHouse connection
def connect():
  this.ch = ClickHouse.from_url('clickhouse://'+this.ch_user+':'+this.ch_pass+'@'+this.ch_host+':'+this.ch_port)

# ClickHouse disconnection
def close():
  this.ch.disconnect()
  this.ch=''

# ClickHouse query
def execute(query):
  if this.ch != '':
    output = this.ch.execute(query);
    return output

  return None
