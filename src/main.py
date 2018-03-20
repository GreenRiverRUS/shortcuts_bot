import logging
import os

from wcpan.telegram import api, types
from tornado.ioloop import IOLoop
from tornado import web
from motor.motor_tornado import MotorClient

from bot_handler import BotHandler


logging.basicConfig(format='{levelname:8s} [{asctime}] {message}', style='{', level=logging.DEBUG)


class Bot:
    def __init__(self, api_token: str,
                 host: str, port: int = 8000,
                 certificate_path: str = None,
                 mongo_host: str = '127.0.0.1', mongo_port: int = 27017,
                 mongo_db: str = 'shortcuts_bot'):
        self.token = api_token
        self.host = host
        self.port = port
        if certificate_path:
            self.certificate = types.InputFile(certificate_path)
        else:
            self.certificate = None
        self.mongo_host = mongo_host
        self.mongo_port = mongo_port
        self.mongo_db = mongo_db

        self.loop = IOLoop.current()
        self.app = None

    async def create_agent(self):
        agent = api.BotAgent(self.token)
        result = await agent.client.set_webhook(
            url=self.host, certificate=self.certificate
        )
        logging.debug('Webhook set: {}'.format(result))
        return agent

    def run(self):
        agent = self.loop.run_sync(self.create_agent)
        db = MotorClient(self.mongo_host, self.mongo_port)[self.mongo_db]
        self.app = web.Application(
            handlers=[
                ('/', BotHandler),
            ],
            agent=agent,
            db=db
        )
        self.app.listen(self.port)
        logging.info('Listening on {}, port {}'.format(self.host, self.port))
        self.loop.start()


if __name__ == '__main__':
    Bot(
        api_token=os.environ['BOT_API_TOKEN'],
        host=os.environ['WEBHOOK_HOST'],
        certificate_path=os.environ.get('CERTIFICATE_PATH', None),
        mongo_host=os.environ['MONGO_HOST'],
        mongo_port=os.environ.get('MONGO_PORT', 27017),
        mongo_db=os.environ.get('MONGO_DB_NAME', 'shortcuts_bot')
    ).run()
