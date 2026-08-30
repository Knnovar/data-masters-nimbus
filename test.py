from src.connectors.databricks_uploader import get_uploader
u=get_uploader()
print('host:', repr(u._host))
print('_url:', u._url("sql/statements"))
print('volume:', u._volume_path('x_parquet'))
print('files:', '{}/api/2.0/fs/files{}'.format(u._host, u._volume_path('x_parquet')))