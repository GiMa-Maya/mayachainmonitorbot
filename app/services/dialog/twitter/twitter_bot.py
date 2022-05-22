import asyncio
import logging

import tweepy
from ratelimit import limits

from services.dialog.twitter.text_length import twitter_text_length, twitter_cut_text
from services.lib.config import Config
from services.lib.date_utils import DAY
from services.lib.utils import class_logger, random_hex
from services.notify.channel import MessageType, BoardMessage, MESSAGE_SEPARATOR


class TwitterBot:
    LIMIT_CHARACTERS = 280
    MAX_TWEETS_PER_DAY = 300

    def __init__(self, cfg: Config):
        self.cfg = cfg
        keys = cfg.get('twitter.bot')

        consumer_key = keys.as_str('consumer_key')
        consumer_secret = keys.as_str('consumer_secret')
        access_token = keys.as_str('access_token')
        access_token_secret = keys.as_str('access_token_secret')
        assert consumer_key and consumer_secret and access_token and access_token_secret

        self.auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        self.auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(self.auth)
        self.logger = class_logger(self)

    def verify_credentials(self):
        try:
            self.api.verify_credentials()
            self.logger.debug('Good!')
            return True
        except Exception as e:
            self.logger.debug(f'Bad: {e!r}!')
            return False

    def log_tweet(self, text, image):
        img_tag = "with image" if bool(image) else ""
        self.logger.info(f'🐦🐦🐦 Tweets: "\n{text}\n" [{twitter_text_length(text)} symbols]. 🐦🐦🐦 {img_tag}')

    @limits(calls=MAX_TWEETS_PER_DAY, period=DAY)
    def post_sync(self, text: str, image=None):
        if not text:
            return

        real_len = twitter_text_length(text)
        if real_len >= self.LIMIT_CHARACTERS:
            self.logger.warning(f'Too long text ({real_len} symbols): "{text}".')
            text = twitter_cut_text(text, self.LIMIT_CHARACTERS)

        self.log_tweet(text, image)

        if image:
            name = f'image-{random_hex()}.png'
            ret = self.api.media_upload(filename=name, file=image)

            # Attach media to tweet
            return self.api.update_status(media_ids=[ret.media_id_string], status=text)
        else:
            return self.api.update_status(text)

    async def post(self, text: str, image=None, executor=None, loop=None):
        if not text:
            return
        loop = loop or asyncio.get_event_loop()
        await loop.run_in_executor(executor, self.post_sync, text, image)

    async def multi_part_post(self, text: str, image=None, executor=None, loop=None):
        parts = text.split(MESSAGE_SEPARATOR, maxsplit=10)
        parts = list(filter(bool, map(str.strip, parts)))

        if not parts:
            return
        elif len(parts) >= 2:
            logging.info(f'Twitter multi part message: {len(parts) = }')

        loop = loop or asyncio.get_event_loop()

        for part in parts:
            await self.post(part, image, executor, loop)
            image = None  # attach image solely to the first post, then just nullify it

    async def safe_send_message(self, chat_id, msg: BoardMessage, **kwargs) -> bool:
        # Chat_id is not supported yet... only one single channel
        try:
            if msg.message_type == MessageType.TEXT:
                await self.multi_part_post(msg.text)
            elif msg.message_type == MessageType.PHOTO:
                await self.multi_part_post(msg.text, image=msg.photo)
            else:
                logging.warning(f'Type "{msg.message_type}" is not supported for Twitter.')
            return True
        except Exception:
            logging.exception(f'Twitter exception!', stack_info=True)
            return False


class TwitterBotMock(TwitterBot):
    def post_sync(self, text: str, image=None):
        self.log_tweet(text, image)
