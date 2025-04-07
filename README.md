```
 $$$$$$\  $$\   $$\            $$$$$$\                      $$\             $$\     $$\                             $$\   $$\           $$\       
$$  __$$\ \__|  $$ |          $$  __$$\                     $$ |            $$ |    \__|                            $$ |  $$ |          $$ |      
$$ /  \__|$$\ $$$$$$\         $$ /  $$ |$$$$$$$\   $$$$$$\  $$ |$$\   $$\ $$$$$$\   $$\  $$$$$$$\  $$$$$$$\         $$ |  $$ |$$\   $$\ $$$$$$$\  
$$ |$$$$\ $$ |\_$$  _|$$$$$$\ $$$$$$$$ |$$  __$$\  \____$$\ $$ |$$ |  $$ |\_$$  _|  $$ |$$  _____|$$  _____|$$$$$$\ $$$$$$$$ |$$ |  $$ |$$  __$$\ 
$$ |\_$$ |$$ |  $$ |  \______|$$  __$$ |$$ |  $$ | $$$$$$$ |$$ |$$ |  $$ |  $$ |    $$ |$$ /      \$$$$$$\  \______|$$  __$$ |$$ |  $$ |$$ |  $$ |
$$ |  $$ |$$ |  $$ |$$\       $$ |  $$ |$$ |  $$ |$$  __$$ |$$ |$$ |  $$ |  $$ |$$\ $$ |$$ |       \____$$\         $$ |  $$ |$$ |  $$ |$$ |  $$ |
\$$$$$$  |$$ |  \$$$$  |      $$ |  $$ |$$ |  $$ |\$$$$$$$ |$$ |\$$$$$$$ |  \$$$$  |$$ |\$$$$$$$\ $$$$$$$  |        $$ |  $$ |\$$$$$$  |$$$$$$$  |
 \______/ \__|   \____/       \__|  \__|\__|  \__| \_______|\__| \____$$ |   \____/ \__| \_______|\_______/         \__|  \__| \______/ \_______/ 
                                                                $$\   $$ |                                                                        
                                                                \$$$$$$  |                                                                        
                                                                 \______/                                                                         
```
## Description
Git-Analytics-Hub is a tool that automates the collection, processing, and storage of GitHub Archive data, which provide a full record of GitHub activities for public repositories. It runs hourly to download raw data from GitHub Archive. Then, it processes the raw data and aggregates the processed data, both using DuckDB. All the data is stored in MinIO for further analytics.

## Architecture
Git-Analytics-Hub uses muti-tier architecture - the **Medallion Architecture** - which is a data lake design pattern that organises data into three zones:
- **Bronze Zone**: Containing raw, unprocessed data ingested from various sources.
- **Silver Zone**: Containing cleaned, conformed and potentially modeled data.
- **Gold Zone**: Containing aggregated and curated data ready for reporting, dashboards, and advanced analytics.

![Architecture](./images/medallion_architecture.png)

Each zone in Git-Analytics-Hub is responsible for the following:
- **Bronze Zone**: Stores raw data from [GitHub Archive](https://www.gharchive.org/) data in Minio.
- **Silver Zone**: Stores processed data as `.parquet` file. Data is processed by selecting only need fields using DuckDB
- **Gold Zone**: Stores aggregated data as `.parquet` files. Data is aggregated for each day using DuckDB, ready for downstream use.

The workflow is managed using Apache Airflow, ensuring automated and scheduled data processing.

![Architecture](./images/git-analytics-hub_architecture.png)

## Installation

### Prerequisites
Ensure you have the following installed:
- **Docker** (tested with version `28.0.1`)
- **Docker Compose** (tested with version `2.33.1`)
- **Python** (tested with version `3.10.15`)

### Setup
Clone the repository and navigate to the project directory:
```sh
git clone https://github.com/viethung1234q/git_analytics_hub.git
cd git_analytics_hub
```

## Usage

### First-time setup:
Initialize Airflow before running the services:
```sh
docker compose up airflow-init
```
Then, start the services:
```sh
docker compose up --build -d
```

### Subsequent runs:
For all future runs, simply use:
```sh
docker compose up -d
```

### Stop:
To stop services:
```sh
docker compose down
```

## Configuration

### Environment Variables
Environment variables are defined in the `.env` file:
```ini
AIRFLOW_UID=1000
AIRFLOW__WEBSERVER__EXPOSE_CONFIG=true
AIRFLOW__SCHEDULER__CATCHUP_BY_DEFAULT=false
...
```

### Project Configuration
Project-specific configurations are stored in `git_analytics_hub/src/config.ini`:
```ini
[minio]
access_key = minioadmin
secret_key = minioadmin
...
```

## Additional Notes
- Airflow DAGs are configured to run hourly, processing GitHub Archive data.
- Minio is used as object storage for raw and processed data.
- DuckDB serves as the query engine for data transformations.

For detailed documentation and contributions, refer to the official repository.


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
