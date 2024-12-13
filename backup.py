import os
import yadisk
import datetime
import subprocess
from app.settings import DATABASES


YA_DISK_CONFIG = {
    "app_id": "XXX",
    "app_secret": "XXX",
    "token": "XXX",
    "backup_path": "cproject_backup"
}
PG_DUMP_BIN_PATH = r'"C:\Program Files\PostgreSQL\17\bin\pg_dump.exe"'


def get_dump(host: str, port: int, username: str, password: str, db_name: str):
    try:
        os.environ["PGPASSWORD"] = password
        return subprocess.check_output([
            r'pg_dump',
            "-h", host,
            "-p", str(port),
            "-U", username,
            db_name
        ])
    except subprocess.CalledProcessError as e:
        raise Exception(f"Can't create dump: {e}")


if __name__ == "__main__":
    cloud_client = yadisk.Client(YA_DISK_CONFIG['app_id'], YA_DISK_CONFIG['app_secret'], YA_DISK_CONFIG['token'])
    config = DATABASES['default']

    format_date = datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S')
    output_file = f"dump_{format_date}.sql"
    with open(output_file, "wb") as f:
        f.write(get_dump(config['HOST'], config['PORT'], config['USER'], config['PASSWORD'], config['NAME']))

    link = cloud_client.upload(output_file, f"{YA_DISK_CONFIG['backup_path']}/{output_file}")
    print("Dump successful uploaded to Yandex.Disk -> ", link.href)
    os.remove(output_file)
