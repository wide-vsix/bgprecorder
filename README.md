# bgp route collector

MRT formated bgp rib dump  to psql

```yaml
version: "3"
services:
  cron:
    image: ghcr.io/wide-vsix/simple-cron:latest
    environment:
      TZ: Asia/Tokyo
      CRON_OPTION: "0 3 * * *" # once a day
      CRON_COMMAND: |
        # rsync flom remote
        rsync -tvz -6 vsix@ex-collector:/var/log/gobgp/ribs/*.dump /backup"

        # delete 14 days age files
        find /var/log/gobgp/ribs/ -type f -name "*.dump*" -mtime +14 | xargs -I arg echo Dlete file: arg
        find /var/log/gobgp/ribs/ -type f -name "*.dump*" -mtime +14 | xargs -I arg rm arg
        # compress 7 days ages file
        find /var/log/gobgp/ribs/ -type f -name "*.dump" -mtime +7  | xargs -I arg echo Compress file: arg
        find /var/log/gobgp/ribs/ -type f -name "*.dump" -mtime +7  | xargs -I arg bzip2 arg

    volumes:
      - /var/log/gobgp:/var/log/gobgp
```


demo

```
bgprecorder=# select * from bgprib_202207122200 where inet '2001:200:e00::1' <<  bgprib_202207122200.nlri;
   id   |        time         | path_id |   type_name    | sequence |         from_ip         | from_as | originated | origin
 |       aspath        | nlri_type |     nlri      |             nexthop              | community  | large_community
--------+---------------------+---------+----------------+----------+-------------------------+---------+------------+-------
-+---------------------+-----------+---------------+----------------------------------+------------+-----------------
 154903 | 2022-07-12 23:00:32 |      16 | TABLE_DUMP2_AP |          | 2001:200:e00:300:dad::4 |       0 |            | IGP
 | 2500                |           | 2001:200::/32 | 2001:200:e00:a1:2500::1          | 4690:64500 |
 154904 | 2022-07-12 23:00:32 |      14 | TABLE_DUMP2_AP |          | 2001:200:e00:300:dad::5 |       0 |            | IGP
 | 7530 9607 2497 2500 |           | 2001:200::/32 | 2405:f000:0:4004:210:231:215:238 | 4690:64501 |

```