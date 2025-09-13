import abc


class BaseHandler(abc.ABC):
    @abc.abstractmethod
    async def handle(event):
        pass

    async def callback(event):
        pass
