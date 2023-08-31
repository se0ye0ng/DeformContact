import torch


def collate_fn(batch):
    obj_names, rest_graphs, def_graphs, metas, collider_graphs = zip(*batch)
    
    # Collate simple data
    obj_names = [name for name in obj_names]

    # For meta data
    tensor_meta_keys = [key for key in metas[0].keys() if isinstance(metas[0][key], torch.Tensor)]
    scalar_meta_keys = [key for key in metas[0].keys() if not isinstance(metas[0][key], torch.Tensor)]

    collated_meta = {key: torch.stack([meta[key] for meta in metas]) for key in tensor_meta_keys}
    for key in scalar_meta_keys:
        collated_meta[key] = [meta[key] for meta in metas]

    return obj_names, rest_graphs, def_graphs, collated_meta, collider_graphs
