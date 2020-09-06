# Summary

collect and analyze linux server resouce logs

# Detail

linux の 以下コマンドをログ出力するシェルと、そのログを解析するためのスクリプト(python)から成る
- vmstat ：1日1ファイル出力
- free   ：1日1ファイル出力
- top    ：1ファイルのみ出力
- iostat ：以下それぞれに対して1ファイルのみ出力
  - cpu
  - device
  - device (拡張情報)

## Collect linux server resouce logs

### how to use

`/collectTool/getstatlog.service` を `/etc/systemd/system` に配置

`/collectTool/getstatlog.sh` を `/root` に配置

- start
```
systemctl start getstatlog 
```

- stop
```
systemctl stop getstatlog
```

- auto start
```
systemctl enable getstatlog
```

## Analyze linux server resouce logs

### how to use

analyzerToolフォルダと同階層に inputフォルダ と outputフォルダを作成

inputフォルダに 上記shellにより出力されたログファイルを配置して、スクリプトを実行

- vmstat_analysis.py
  - input: vmstat_yyyymmdd.log
  - output: vmstat_result.csv

- free_analysis_py
  - input: free_yyyymmdd.log
  - output: free_result.csv and view graph

- top_analysis.py
  - input: top_yyyymmdd-.log
  - output: top_memory_result.csv, top_cpu_result.csv and view graph

- iostat_analysis.py
  - input: iostat_x_dev_yyyymmdd-.log
  - output: iostat_result.csv and view graph

option (common):

- `--startTime "YYYY/mm/dd HH:MM:ss"' : time filter. output data only after start time. 

- `--endTime "YYYY/mm/dd HH:MM:ss"` : time filter. output data only before end time.
