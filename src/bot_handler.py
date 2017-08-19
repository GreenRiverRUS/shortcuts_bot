import logging
from typing import List, Dict

from bson import ObjectId
from wcpan.telegram import api, types

from phrases import PHRASES


logging.basicConfig(format='{levelname:8s} [{asctime}] {message}', style='{', level=logging.DEBUG)


# noinspection PyAbstractClass
class BotHandler(api.BotHookHandler):
    async def get_memory(self, user_id: int) -> Dict:
        db = self.settings['db']
        record = await db.memory.find_one(filter={'user_id': user_id}) or {}
        return record.get(
            'memory',
            {'state': 'create.shortcut_name', 'shortcut_title': None}  # default empty memory value
        )

    async def save_memory(self, user_id: int, memory: Dict) -> None:
        db = self.settings['db']
        await db.memory.update_one(filter={'user_id': user_id},
                                   update={'$set': {'memory': memory}},
                                   upsert=True)

    async def create_user_shortcut(self, user_id: int,
                                   shortcut_title: str, shortcut_content: str):
        db = self.settings['db']
        await db.shortcuts.insert_one({
            'user_id': user_id,
            'shortcut': {'title': shortcut_title, 'content': shortcut_content}
        })

    async def find_user_shortcut(self, user_id: int, shortcut_title: str):
        db = self.settings['db']
        record = await db.shortcuts.find_one(
            filter={'user_id': user_id,
                    'shortcut.title': shortcut_title}
        ) or {}
        return record.get('shortcut', None)

    async def delete_user_shortcut(self, user_id: int, shortcut_title: str):
        db = self.settings['db']
        result = await db.shortcuts.delete_one(filter={'user_id': user_id,
                                                       'shortcut.title': shortcut_title})
        return result.deleted_count > 0

    async def lookup_user_shortcuts(self, user_id: int, query: str):
        db = self.settings['db']
        cursor = db.shortcuts.find(
            filter={'user_id': user_id,
                    'shortcut.title': {'$regex': '^{}.*'.format(query), '$options': 'i'}}
        ).sort('shortcut.title')
        async for record in cursor.limit(50):  # 50 - maximum for telegram
            yield record['shortcut']['title'], record['shortcut']['content']

    @staticmethod
    def find_command(message: types.Message):
        entities = message.entities or []  # type: List[types.MessageEntity]
        commands = [entity for entity in entities if entity.type_ == 'bot_command']
        if len(commands):
            command = commands[0]
            command_name = message.text[command.offset:command.offset + command.length]
            command_args = message.text[command.offset + command.length:].strip()
            return command_name, command_args
        return None, None

    @staticmethod
    def get_username(user: types.User):
        if user.username is not None:
            return '@{}'.format(user.username)
        else:
            return user.first_name

    async def on_text(self, message: types.Message) -> None:
        if message.chat.type_ != 'private':
            # Ignore all non-private messages
            return
        client = self.application.settings['agent'].client  # type: api.BotClient
        logging.info('Message from {}: {}'.format(self.get_username(message.from_), message.text))

        user_id = message.from_.id_
        text = message.text
        command, command_args = self.find_command(message)

        memory = await self.get_memory(user_id)
        if command is not None:
            if command == '/start':
                memory['state'] = 'create.shortcut_name'
                memory['shortcut_title'] = None

                if len(command_args) and command_args != 'No_Na_Me':  # Skip switch_pm_parameter. See below
                    text = command_args
                else:
                    text = None
                    await client.send_message(user_id, PHRASES['create'])
            elif command == '/cancel':
                memory['state'] = 'create.shortcut_name'
                memory['shortcut_title'] = None

                text = None
                await client.send_message(user_id, PHRASES['cancel'])
            elif command == '/delete':
                memory['state'] = 'delete.shortcut_name'
                memory['shortcut_title'] = None

                if len(command_args):
                    text = command_args
                else:
                    text = None
                    await client.send_message(user_id, PHRASES['delete'])
            else:
                text = None
                await client.send_message(user_id, PHRASES['unknown_command'])

        if text is not None:
            if memory['state'] == 'create.shortcut_name':
                shortcut = await self.find_user_shortcut(user_id, text)
                if shortcut is not None:
                    await client.send_message(
                        user_id, PHRASES['shortcut_exist'].format(shortcut['title'])
                    )
                else:
                    memory['state'] = 'create.shortcut_content'
                    memory['shortcut_title'] = text

                    await client.send_message(
                        user_id, PHRASES['creating_shortcut'].format(text)
                    )
            elif memory['state'] == 'create.shortcut_content':
                memory['state'] = 'create.shortcut_name'
                shortcut_title, memory['shortcut_title'] = memory['shortcut_title'], None

                await self.create_user_shortcut(user_id, shortcut_title, text)

                await client.send_message(
                    user_id, PHRASES['shortcut_created'],
                    reply_markup=types.InlineKeyboardMarkup([[
                        types.InlineKeyboardButton(
                            text=PHRASES['return_back_button'],
                            switch_inline_query=shortcut_title
                        )
                    ]])
                )
            elif memory['state'] == 'delete.shortcut_name':
                memory['state'] = 'create.shortcut_name'
                memory['shortcut_title'] = None

                if await self.delete_user_shortcut(user_id, text):
                    await client.send_message(
                        user_id, PHRASES['shortcut_deleted'].format(text)
                    )
                else:
                    await client.send_message(
                        user_id, PHRASES['shortcut_unknown'].format(text)
                    )

        await self.save_memory(user_id, memory)

    async def on_inline_query(self, inline_query: types.InlineQuery) -> None:
        client = self.application.settings['agent'].client  # type: api.BotClient
        logging.info('Inline query from {}: {}'.format(
            self.get_username(inline_query.from_), inline_query.query
        ))

        user_id = inline_query.from_.id_
        results = []
        async for shortcut_title, shortcut_content in self.lookup_user_shortcuts(user_id, inline_query.query):
            results.append(types.InlineQueryResultArticle(
                id_=str(ObjectId()),
                title=shortcut_title,
                description=shortcut_content,
                input_message_content=types.InputTextMessageContent(shortcut_content)
            ))

        await client.answer_inline_query(
            inline_query.id_, results,
            cache_time=0, is_personal=True,
            switch_pm_text=PHRASES['create_shortcut_button'],
            switch_pm_parameter='No_Na_Me'
        )
