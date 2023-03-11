from flasgger import Swagger
from flask import Flask

import config
from blueprints import rest_bp, user_bp, voucher_bp, community_bp
from exts import db

# init flask app and database
app = Flask(__name__)
app.config.from_object(config)

# init swagger
swagger_config = Swagger.DEFAULT_CONFIG
swagger_config['title'] = config.SWAGGER_TITLE
swagger_config['description'] = config.SWAGGER_DESC
swagger_config['specs_route'] = config.specs_route
swagger_config['version'] = config.version
swagger_config['openapi'] = config.OPENAPI_VERSION
swagger = Swagger(app, config=swagger_config)

# register blueprints
db.init_app(app)
app.register_blueprint(rest_bp)
app.register_blueprint(user_bp)
app.register_blueprint(voucher_bp)
app.register_blueprint(community_bp)


@app.route("/ping")
def ping():
    return "pong", 200


if __name__ == '__main__':
    app.run(debug=True)
