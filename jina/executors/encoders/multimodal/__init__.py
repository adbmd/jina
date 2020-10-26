__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import List

import numpy as np

from ... import BaseExecutor


class BaseMultiModalEncoder(BaseExecutor):
    """
    :class:`BaseMultiModalEncoder` encodes data from multiple inputs (``text``, ``buffer``, ``blob`` or other ``embeddings``)
    into a single ``embedding``
    """

    def __init__(self,
                 position_by_modality: List[str] = [],
                 *args,
                 **kwargs):
        """
        :param position_by_modality: the list of arguments indicating in which order the modalities they need to come
        for the encoding method
        :return:
        """
        super().__init__(*args, **kwargs)
        self._position_by_modality = position_by_modality


    def encode(self, *data: 'np.ndarray', **kwargs) -> 'np.ndarray':
        """
        :param: data: M arguments of shape `B x (D)` numpy ``ndarray``, `B` is the size of the batch, `M` is the number of modalities
        :return: a `B x D` numpy ``ndarray``
        """
        raise NotImplementedError

    @property
    def position_by_modality(self) -> List[str]:
        """Get position per modality.
        :return: the list of strings representing the name and order of the modality.
        """
        if not self._position_by_modality:
            raise RuntimeError('Could not know which position of the ndarray to load to each modality')
        return self._position_by_modality
