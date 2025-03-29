# Git Analytics Hub


   _____ _ _                          _       _   _            _    _       _     
  / ____(_) |       /\               | |     | | (_)          | |  | |     | |    
 | |  __ _| |_     /  \   _ __   __ _| |_   _| |_ _  ___ ___  | |__| |_   _| |__  
 | | |_ | | __|   / /\ \ | '_ \ / _` | | | | | __| |/ __/ __| |  __  | | | | '_ \ 
 | |__| | | |_   / ____ \| | | | (_| | | |_| | |_| | (__\__ \ | |  | | |_| | |_) |
  \_____|_|\__| /_/    \_\_| |_|\__,_|_|\__, |\__|_|\___|___/ |_|  |_|\__,_|_.__/ 
                                         __/ |                                    
                                        |___/                                     

Minio
DuckDB
Gharchive
Hourly fetched data

Incrementally collecting the Github Archive datasets, which provide a full record of GitHub activities for public repositories, and enabling analytics on top of that data.

We will use Medallion architecture/multi-tier architecture for this project. 
The Medallion architecture is a data lake design pattern that organises data into three zones:
- Bronze Zone: Containing raw, unprocessed data ingested from various sources.
- Silver Zone: Containing cleaned, conformed and potentially modeled data.
- Gold Zone: Containing aggregated and curated data ready for reporting, dashboards, and advanced analytics.


python3 src/scripts/fetch_raw_data.py
python3 src/scripts/serialise_raw_data.py
python3 src/scripts/aggregate_tf_data.py


Lý do nên cài Airflow bằng Docker + Docker Compose trên WSL 2 thay vì cài trực tiếp bằng pip là vì:

1. Dễ dàng quản lý và triển khai
Tất cả thành phần của Airflow (Scheduler, Webserver, Database) được đóng gói trong Docker container, không cần cài đặt thủ công PostgreSQL/MySQL hay các dependency khác.
Khi cần di chuyển Airflow sang môi trường khác (server, cloud), chỉ cần pull Docker image về và chạy.
2. Tránh xung đột môi trường
Airflow có rất nhiều dependency (SQLAlchemy, Flask, Celery...) dễ gây lỗi nếu cài bằng pip trên môi trường local.
Nếu bạn cài Airflow trực tiếp trên WSL 2, có thể xảy ra xung đột giữa Python version hoặc package dependency với các thư viện khác.
3. Dễ dàng cập nhật và rollback
Với Docker, nếu có bản cập nhật Airflow, chỉ cần thay đổi image version và restart container, không lo về lỗi do cài đặt thủ công.
Nếu có lỗi, chỉ cần pull lại image cũ là xong.
4. Tích hợp dễ dàng với Minio và DuckDB
Bạn đang dùng Minio và DuckDB, có thể chạy chúng trong các container riêng và kết nối với Airflow qua Docker Compose mà không cần cài đặt riêng lẻ.

-> Kết luận: Cài đặt bằng Docker giúp bạn dễ quản lý, dễ mở rộng, không lo lỗi dependency, phù hợp để triển khai trên bất kỳ hệ thống nào. 🚀


curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.10.5/docker-compose.yaml'
mkdir -p ./airflow
mkdir -p ./airflow/dags ./airflow/logs ./airflow/config ./airflow/plugins
echo -e "AIRFLOW_UID=$(id -u)" > .env
docker compose up airflow-init
docker compose up --build -d


run 1 docker compose to start all service (airflow, minio)