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

## how to use

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

準備中
