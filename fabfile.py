from fabric.api import task, local


@task
def restart(name='sc', cache='true'):
    local('env $(cat settings.env | xargs) docker-compose -p {name} build {cache}'.format(
        name=name, cache='--no-cache' if cache == 'false' else '')
    )
    local('env $(cat settings.env | xargs) docker-compose -p {name} down'.format(name=name))
    local('env $(cat settings.env | xargs) docker-compose -p {name} up -d'.format(name=name))


@task
def up(name='sc'):
    local('env $(cat settings.env | xargs) docker-compose -p {name} up --build -d'.format(name=name))


@task
def down(name='sc'):
    local('env $(cat settings.env | xargs) docker-compose -p {name} down'.format(name=name))
