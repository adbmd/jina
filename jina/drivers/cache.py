from typing import Iterable, Any

from .index import BaseIndexDriver

if False:
    from ..proto import jina_pb2


class BaseCacheDriver(BaseIndexDriver):

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs) -> None:
        for d in docs:
            result = self.exec[d.id]
            if result is None:
                self.on_miss(d)
            else:
                self.on_hit(d, result)

    def on_miss(self, doc: 'jina_pb2.Document') -> None:
        """Function to call when doc is missing, the default behavior is add to cache when miss

        :param doc: the document in the request but missed in the cache
        """
        self.exec_fn(doc.id, doc.SerializeToString())

    def on_hit(self, req_doc: 'jina_pb2.Document', hit_result: Any) -> None:
        """ Function to call when doc is hit

        :param req_doc: the document in the request and hitted in the cache
        :param hit_result: the hit result returned by the cache
        :return:
        """
        pass
