import open3d as o3d
import torch
import os
import numpy as np    

def _feature_rigid(meta_data,pos_enc): 
    contact_point_np = meta_data['deformer_collision_position'].detach().numpy()
    origin_point_np = meta_data['deformer_origin'].detach().numpy()    

    vector_lineset = o3d.geometry.LineSet()
    vector_lineset.points = o3d.utility.Vector3dVector([origin_point_np, contact_point_np])
    vector_lineset.lines = o3d.utility.Vector2iVector([[0, 1]])

    vector_lineset_np = np.asarray(vector_lineset.points)
    vector_diff = vector_lineset_np[1] - vector_lineset_np[0]
    vector_diff_t = torch.tensor(vector_diff, dtype=torch.float32)
    vector_broadcasted = vector_diff_t.repeat(pos_enc.shape[0], 1)

    features = torch.cat([vector_broadcasted, pos_enc], dim=1)
    return features

def _unity_to_open3d(vector_or_position):
    x, y, z = vector_or_position
    return [z,-x, y]

def _create_rigid_pointcloud(contact_point_np,rigid_radius):
    rigid_contact_mesh = o3d.geometry.TriangleMesh.create_sphere(radius=rigid_radius)
    rigid_contact_mesh.translate(contact_point_np)
    pcd_contact = o3d.geometry.PointCloud()
    pcd_contact.points = o3d.utility.Vector3dVector(np.array(rigid_contact_mesh.vertices))
    return rigid_contact_mesh


def _load_deformed_mesh(sample_path, meta_data,root_dir):
    soft_def_mesh = o3d.io.read_triangle_mesh(os.path.join(root_dir, sample_path + ".ply"))
    soft_def_mesh.translate(meta_data['object_rigid_pos'].detach().cpu().numpy())
    return soft_def_mesh
 

def _sample_nearest(rigid_mesh, soft_def_mesh, soft_rest_mesh, n_points, use_center_only=True):

    center = np.mean(np.asarray(rigid_mesh.vertices), axis=0)

    # 1. Build KDTree for the resting mesh
    pcd_rest = o3d.geometry.PointCloud()
    pcd_rest.points = o3d.utility.Vector3dVector(np.asarray(soft_rest_mesh.vertices))
    kdtree = o3d.geometry.KDTreeFlann(pcd_rest)

    # 2. Search KDTree for the k nearest neighbors to the center of the rigid_mesh
    _, idx, _ = kdtree.search_knn_vector_3d(center, n_points)
    idx_set = set(idx)  # Convert idx to a set for faster lookup

    # 3. Extract vertices using the indices
    soft_rest_vertices_np = np.asarray(pcd_rest.points)[idx]
    soft_def_vertices_np = np.asarray(soft_def_mesh.vertices)[idx]

    # 4. Extract triangle faces whose vertices are in the sampled set
    soft_def_triangles = np.asarray(soft_def_mesh.triangles)
    sampled_triangles = [tri for tri in soft_def_triangles if all(v in idx_set for v in tri)]

    # 5. Adjust the triangle face indices to correspond to the new vertex list
    index_map = {v: i for i, v in enumerate(idx)}
    sampled_triangles_adjusted = np.array([[index_map[v] for v in tri] for tri in sampled_triangles])

    # 6. Create new sampled meshes
    sampled_soft_rest_mesh = o3d.geometry.TriangleMesh()
    sampled_soft_rest_mesh.vertices = o3d.utility.Vector3dVector(soft_rest_vertices_np)
    sampled_soft_rest_mesh.triangles = o3d.utility.Vector3iVector(sampled_triangles_adjusted)

    sampled_soft_def_mesh = o3d.geometry.TriangleMesh()
    sampled_soft_def_mesh.vertices = o3d.utility.Vector3dVector(soft_def_vertices_np)
    sampled_soft_def_mesh.triangles = o3d.utility.Vector3iVector(sampled_triangles_adjusted)

    return sampled_soft_rest_mesh, sampled_soft_def_mesh
