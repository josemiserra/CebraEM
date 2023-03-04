
"""
This file contains all the implementation that could potentially be integrated directly into the elf package
Some functions are copied here from the elf package and just changed slightly
"""

from copy import deepcopy
import numpy as np
import vigra
import multiprocessing
import nifty.graph.rag as nrag

from elf.segmentation.workflows import (
    FEATURE_NAMES,
    DEFAULT_RF_KWARGS,
    _compute_features
)
import elf.segmentation.learning as elf_learn

DEFAULT_NRF_KWARGS = {'n_estimators': 200, 'max_depth': 10}


def compute_edge_labels(rag, gt, ignore_label=None, n_threads=None, return_node_labels=False):
    """ Compute edge labels by mapping ground-truth segmentation to graph nodes.

    Arguments:
        rag [RegionAdjacencyGraph] - region adjacency graph
        gt [np.ndarray] - ground-truth segmentation
        ignore_label [int or np.ndarray] - label id(s) in ground-truth
            to ignore in learning (default: None)
        n_threads [int] - number of threads (default: None)
    """
    n_threads = multiprocessing.cpu_count() if n_threads is None else n_threads

    node_labels = nrag.gridRagAccumulateLabels(rag, gt, n_threads)
    uv_ids = rag.uvIds()

    edge_labels = (node_labels[uv_ids[:, 0]] != node_labels[uv_ids[:, 1]]).astype('uint8')

    if ignore_label is not None:
        mapped_uv_ids = node_labels[uv_ids]
        edge_mask = np.isin(mapped_uv_ids, ignore_label)
        edge_mask = edge_mask.sum(axis=1) == 0
        assert len(edge_labels) == len(edge_mask)
        return edge_labels, edge_mask

    if return_node_labels:
        return edge_labels, node_labels
    else:
        return edge_labels


def compute_node_features(input_map, segmentation, n_threads=None):
    """ Compute node features from input map accumulated over segmentation """

    stat_feature_names = ["Count", "Kurtosis", "Maximum", "Minimum", "Quantiles",
                          "RegionRadii", "Skewness", "Sum", "Variance"]
    node_features = vigra.analysis.extractRegionFeatures(input_map, segmentation, features=stat_feature_names)

    node_features = [node_features[fname] for fname in stat_feature_names]
    node_features = np.concatenate([feat[:, None] if feat.ndim == 1 else feat
                                    for feat in node_features], axis=1)

    print(f'node_features.shape = {node_features.shape}')
    return np.nan_to_num(node_features)


def _compute_node_and_edge_features_and_labels(
        raw, boundaries, watershed, labels, feature_names, n_threads,
        mask_zeros=False
):

    rag, edge_features = _compute_features(raw, boundaries, watershed, feature_names, False, n_threads=n_threads)
    # FIXME this is already computed in _compute_features: extract from there!
    node_features = compute_node_features(raw.astype('float32'), watershed.astype('uint32'), n_threads)

    edge_labels, node_labels = compute_edge_labels(rag, labels, n_threads=n_threads, return_node_labels=True)

    if mask_zeros:
        edge_mask = (rag.uvIds() != 0).any(axis=1)
        node_mask = [x != 0 for x in rag.nodes()]
        print(f'rag.nodes() = {rag.nodes()}')
        print(f'node_mask = {node_mask}')
    else:
        edge_mask = np.ones(len(edge_features), dtype='bool')
        node_mask = np.ones(len(node_features), dtype='bool')

    edge_features, edge_labels = edge_features[edge_mask], edge_labels[edge_mask]
    node_features, node_labels = node_features[node_mask], node_labels[node_mask]

    assert len(edge_features) == len(edge_labels)
    assert len(node_features) == len(node_labels)

    return edge_features, node_features, edge_labels, node_labels


def edge_and_node_training(
        raw, boundaries, labels, watershed, mask=None,
        feature_names=FEATURE_NAMES,
        learning_kwargs=DEFAULT_RF_KWARGS,
        node_learning_kwargs=DEFAULT_NRF_KWARGS,
        n_threads=None
):
    """ Train random forest classifier for edges and one for nodes """

    if mask is not None:
        print('Using masks for edge and node training!')

    # we store the ignore label(s) in the random forest kwargs,
    # but they need to be removed before this is passed to the rf implementation
    rf_kwargs = deepcopy(learning_kwargs)
    ignore_label = rf_kwargs.pop('ignore_label', None)
    nrf_kwargs = node_learning_kwargs

    # if the raw data is a numpy array, we assume that we have a single training set
    if isinstance(raw, np.ndarray):
        if (not isinstance(boundaries, np.ndarray)) or (not isinstance(labels, np.ndarray)):
            raise ValueError("Expect raw data, boundaries and labels to be either all numpy arrays or lists")
        if mask is not None and not isinstance(mask, np.ndarray):
            raise ValueError("Invalid mask")

        if mask is not None:
            watershed[np.logical_not(mask)] = 0

        print(f'Computing node and edge features')
        edge_features, node_features, edge_labels, node_labels = _compute_node_and_edge_features_and_labels(
            raw, boundaries, watershed,
            labels, feature_names, n_threads, mask_zeros=mask is not None,
        )

    # otherwise, we assume to get listlike data for raw data, boundaries and labels,
    # corresponding to multiple training data-sets
    else:
        if not (len(raw) == len(boundaries) == len(labels)):
            raise ValueError("Expect same number of raw data, boundary and label arrays")
        if watershed is not None and len(watershed) != len(raw):
            raise ValueError("Expect same number of watershed arrays as raw data")
        if mask is not None and not len(mask) == len(raw):
            raise ValueError("Expect same number of mask arrays as raw data")

        edge_features = []
        edge_labels = []
        node_features = []
        node_labels = []
        # compute features and labels for all training data-sets
        for train_id, (this_raw, this_boundaries, this_labels) in enumerate(zip(raw, boundaries, labels)):

            this_watershed = watershed[train_id]
            this_mask = None if mask is None else mask[train_id]

            if this_mask is not None:
                this_watershed[np.logical_not(this_mask)] = 0

            this_edge_features, this_node_features, this_edge_labels, this_node_labels = _compute_node_and_edge_features_and_labels(
                this_raw, this_boundaries, this_watershed,
                this_labels, feature_names, n_threads, mask_zeros=this_mask is not None
            )

            edge_features.append(this_edge_features)
            edge_labels.append(this_edge_labels)
            node_features.append(this_node_features)
            node_labels.append(this_node_labels)

        edge_features = np.concatenate(edge_features, axis=0)
        edge_labels = np.concatenate(edge_labels, axis=0)
        node_features = np.concatenate(node_features, axis=0)
        node_labels = np.concatenate(node_labels, axis=0)

    assert len(edge_features) == len(edge_labels), "%i, %i" % (len(edge_features), len(edge_labels))
    assert len(node_features) == len(node_labels), "%i, %i" % (len(node_features), len(node_labels))

    # train the random forest (2 separate random forests for in-plane and between plane edges for stacked 2d watersheds)
    print(f'rf_kwargs: {rf_kwargs}')
    rf = elf_learn.learn_edge_random_forest(edge_features, edge_labels, n_threads=n_threads, **rf_kwargs)

    # Binarize the node labels (background stays zero, all rest to 1)
    node_labels[node_labels > 0] = 1
    nrf = elf_learn.learn_edge_random_forest(node_features, node_labels, n_threads=n_threads, **nrf_kwargs)

    return rf, nrf

