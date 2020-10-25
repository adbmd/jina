__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np
from collections import defaultdict
from typing import Iterable, Tuple, Dict

from .encode import BaseEncodeDriver
from .helper import pb2array, array2pb
from ..proto import jina_pb2


def _extract_doc_content(doc: 'jina_pb2.Document'):
    """Returns the content of the document with the following priority:
    If the document has an embedding, return it, otherwise return its content.
    """
    if doc.embedding.buffer:
        return pb2array(doc.embedding)
    else:
        return doc.text or doc.buffer or (doc.blob and pb2array(doc.blob))


def _extract_modalities_from_document(doc: 'jina_pb2.Document'):
    """Returns a dictionary of document content (embedding, text, blob or buffer) with `modality` as its key
    """
    doc_content = {}
    for chunk in doc.chunks:
        modality = chunk.modality
        if modality in doc_content.keys():
            return None
        else:
            doc_content[modality] = _extract_doc_content(chunk)
    return doc_content


class MultimodalDriver(BaseEncodeDriver):
    """Extract multimodal embeddings from different modalities.
    Input-Output ::
        Input:
        document:
                |- chunk: {modality: mode1}
                |
                |- chunk: {modality: mode2}
        Output:
        document: (embedding: multimodal encoding)
                |- chunk: {modality: mode1}
                |
                |- chunk: {modality: mode2}

    .. note::
        - It traverses on the ``documents`` for which we want to apply the ``multimodal`` embedding. This way
        we can use the `batching` capabilities for the `executor`.
        - It assumes that every ``chunk`` of a ``document`` belongs to a different modality.
    """

    def __init__(self,
                 traversal_paths: Tuple[str] = ('r',), *args, **kwargs):
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)

    @property
    def position_by_modality(self):
        if not getattr(self._exec, 'position_by_modality', None):
            raise RuntimeError('Could not know which position of the ndarray to load to each modality')
        return self._exec.position_by_modality

    def _get_executor_input_arguments(self, content_by_modality: Dict[str, 'np.ndarray'], num_modalities: int):
        """
            From a dictionary ``content_by_modality`` it returns the arguments in the proper order so that they can be
            passed to the executor.
        """
        input_args = [None] * num_modalities
        for modality in self.position_by_modality.keys():
            input_args[self.position_by_modality[modality]] = content_by_modality[modality]
        return input_args

    def _apply_all(
            self,
            docs: Iterable['jina_pb2.Document'],
            *args, **kwargs
    ) -> None:
        """
        :param docs: the docs for which a ``multimodal embedding`` will be computed
        :return:
        """
        # docs are documents whose chunks are multimodal
        # This is similar to ranking, needed to have batching?
        num_modalities = len(self.position_by_modality.keys())
        content_by_modality = defaultdict(list)  # array of num_rows equal to num_docs and num_columns equal to

        # num_modalities
        valid_docs = []
        for doc in docs:
            doc_content = _extract_modalities_from_document(doc)
            if doc_content:
                valid_docs.append(doc)
                for modality in self.position_by_modality.keys():
                    content_by_modality[modality].append(doc_content[modality])
            else:
                self.logger.warning(f'Invalid doc {doc.id}. Only one chunk per modality is accepted')

        if len(valid_docs) > 0:
            # I want to pass a variable length argument (one argument per array)
            for modality in self.position_by_modality.keys():
                content_by_modality[modality] = np.stack(content_by_modality[modality])

            # Guarantee that the arguments are provided to the executor in its desired order
            input_args = self._get_executor_input_arguments(content_by_modality, num_modalities)
            embeds = self.exec_fn(*input_args)
            if len(valid_docs) != embeds.shape[0]:
                self.logger.error(
                    f'mismatched {len(valid_docs)} docs from level {docs[0].granularity} '
                    f'and a {embeds.shape} shape embedding, the first dimension must be the same')
            for doc, embedding in zip(valid_docs, embeds):
                doc.embedding.CopyFrom(array2pb(embedding))
