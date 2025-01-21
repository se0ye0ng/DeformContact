import open3d as o3d
import numpy as np

pcd = o3d.geometry.PointCloud()
pcd.points = o3d.utility.Vector3dVector(np.random.rand(100, 3))
o3d.io.write_point_cloud("test_pcd.ply", pcd)
print("Open3D and NumPy are correctly configured.")
