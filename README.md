## Telegram shortcuts bot
This bot allows you to create a simple text shortcuts and post
them by choosing one in inline mode.

### How to start bot
- Clone repo
- Create your own `.env` by coping `.env.default`
- Place your telegram bot token into `.env`
- Run mongodb container with `MONGO_HOST` name
inside network with `NETWORK_NAME` as specified in `.env`

    For example:
    - `docker pull mongo`
    - `docker network create sc_default`
    - `docker run --restart=always --network=sc_default --name=mongo -d mongo`

- Specify your host name in `.env` _(your machine should have a public signed ssl host)_
- Start: `docker-compose -p sc up --build -d`
