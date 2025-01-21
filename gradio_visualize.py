import gradio as gr
import open3d as o3d
from utils.visualization import (
    visualize_deformation_field,
    visualize_merged_graphs,
    visualize_deformations_normals_colors,
    save_visualization_as_image
)
import torch
from loaders.dataset_loader import load_dataset
from configs.config import Config
from torch_geometric.data import Batch


# Visualization Wrapper
def generate_visualization(batch_idx: int, viz_type: str):
    config = Config("configs/everyday.json")
    _, dataloader_val = load_dataset(config)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    with torch.no_grad():
        for idx, (obj_name, soft_rest_graphs, soft_def_graphs, meta_data, rigid_graphs) in enumerate(dataloader_val):
            if idx == batch_idx:
                soft_rest_graphs_batched = Batch.from_data_list(soft_rest_graphs).to(device)
                soft_def_graphs_batched = Batch.from_data_list(soft_def_graphs).to(device)
                rigid_graphs_batched = Batch.from_data_list(rigid_graphs).to(device)

                if viz_type == "Deformation Field":
                    visualize_deformation_field(
                        soft_rest_graphs[0].pos.cpu(),
                        soft_def_graphs_batched[0].pos.cpu(),
                        rigid_graphs[0].pos.cpu(),
                        meta_data["force_vector"][0],
                    )
                elif viz_type == "Merged Graphs":
                    visualize_merged_graphs(
                        soft_rest_graphs[0],
                        soft_def_graphs_batched[0],
                        rigid_graphs[0],
                        soft_def_graphs_batched[0],
                    )
                elif viz_type == "Deformations Normals Colors":
                    visualize_deformations_normals_colors(
                        soft_rest_graphs[0], soft_def_graphs_batched[0]
                    )
                else:
                    return "Invalid Visualization Type"

                # Return the saved image
                return "output.png"


# Gradio Interface
iface = gr.Interface(
    fn=generate_visualization,
    inputs=[
        gr.Number(label="Batch Index", value=0),
        gr.Dropdown(
            choices=["Deformation Field", "Merged Graphs", "Deformations Normals Colors"],
            label="Visualization Type",
        ),
    ],
    outputs=gr.Image(label="Visualization Output"),
    title="3D Deformation Visualization",
    description="Choose a visualization type and batch index to generate 3D visualizations.",
)

iface.launch(server_name="0.0.0.0", server_port=7860, share=True)
