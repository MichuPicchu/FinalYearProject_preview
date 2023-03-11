# database config
db_host = "182.61.5.68"
db_port = 3306
db_user = "jkzzz"
db_password = "9900"
db_name = "jkzzz"
db_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8"
SQLALCHEMY_DATABASE_URI = db_url
SQLALCHEMY_TRACK_MODIFICATIONS = True

# swagger config
SWAGGER_TITLE = "JKZZZ API"
SWAGGER_DESC = "API documentation for JKZZZ"
specs_route = "/"
version = '3.3.12'
OPENAPI_VERSION = '3.0.2'

# flask config
# HOST = "127.0.0.1"
# PORT = 5000
# DEBUG = True
