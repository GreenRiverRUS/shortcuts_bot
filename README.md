## Telegram shortcuts bot
This bot allows you to create a simple text shortcuts and post
them by choosing one in inline mode.

### Example


### How to start bot
- Clone repo
- Install Fabric: `pip(3) install Fabric3`
- Create your own `settings.env` by coping `settings.default.env`
- Place your telegram bot token into `settings.env`
- Run mongodb container with `MONGO_HOST` name
inside network with `NETWORK_NAME` as specified in `settings.env`

    For example:
    - `docker pull mongo`
    - `docker network create sc_default`
    - `docker run --restart=always --network=sc_default --name=mongo -d mongo`

- Specify your host name in `settings.env` _(your machine should have a public https domain)_
- Start: `fab up`
