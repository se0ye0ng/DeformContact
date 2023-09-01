import torch
import torch.optim as optim
from torch.utils.data import DataLoader
from dataloaders.everyday_deform_v2 import EverydayDeformDataset
from torch_geometric.data import Batch
from dataloaders.collate import collate_fn
from configs.config import Config
from models.model import GraphNet
from models.loss import GradientConsistencyLoss
from tensorboardX import SummaryWriter
import torch.nn as nn
import datetime
import os
import json

def train(config):
    # Create a unique directory name based on the current timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_dir = f'logs/{timestamp}/'
    os.makedirs(log_dir, exist_ok=True)
    
    # Save configuration for future reference
    with open(os.path.join(log_dir, 'config.json'), 'w') as f:
        json.dump(vars(config), f, indent=4)
    
    writer = SummaryWriter(log_dir)

    train_dataset = EverydayDeformDataset(root_dir=config.dataset["root_dir"], 
        obj_list=config.dataset["obj_list"], 
        n_points=config.dataset["n_points"],
        graph_method=config.dataset["graph_method"],
        radius=config.dataset["radius"],
        k=config.dataset["k"], split='train')
    
    val_dataset = EverydayDeformDataset(root_dir=config.dataset["root_dir"], 
        obj_list=config.dataset["obj_list"], 
        n_points=config.dataset["n_points"],
        graph_method=config.dataset["graph_method"],
        radius=config.dataset["radius"],
        k=config.dataset["k"], split='val')

    dataloader_train = DataLoader(
        train_dataset, 
        batch_size=config.dataloader["batch_size"], 
        shuffle=config.dataloader["shuffle"], 
        collate_fn=collate_fn
    )

    dataloader_val = DataLoader(
        val_dataset, 
        batch_size=config.dataloader["batch_size"], 
        shuffle=config.dataloader["shuffle"], 
        collate_fn=collate_fn
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = GraphNet(input_dims=config.network["input_dims"],
                     hidden_dim=config.network["hidden_dim"],
                     output_dim=config.network["output_dim"],
                     num_layers=config.network["num_layers"],  # Add the num_layers parameter
                     dropout_rate=config.network["dropout_rate"],  # Add the dropout_rate parameter
                     knn_k=config.network["knn_k"],  # Add the knn_k parameter
                     backbone=config.network["backbone"]).to(device)  # Add the backbone parameter
    optimizer = optim.Adam(model.parameters(), lr=config.training["learning_rate"])
    criterion_mse = nn.MSELoss()
    criterion_grad = GradientConsistencyLoss()
    lambda_gradient = config.training["lambda_gradient"]

    for epoch in range(config.training["n_epochs"]):
        model.train()
        for batch_idx, (obj_name, rest_graphs, def_graphs, meta_data, collider_graphs) in enumerate(dataloader_train):
            rest_graphs_batched = Batch.from_data_list(rest_graphs)
            collider_graphs_batched = Batch.from_data_list(collider_graphs)
            def_graphs_batched = Batch.from_data_list(def_graphs)
            

            rest_graphs_batched,collider_graphs_batched,def_graphs_batched = rest_graphs_batched.to(device),collider_graphs_batched.to(device),def_graphs_batched.to(device)

            # Forward
            predictions = model(rest_graphs_batched, collider_graphs_batched)
            
            # Compute the loss
            loss_mse = criterion_mse(predictions.pos, def_graphs_batched.pos)
            loss_consistency = criterion_grad(predictions, def_graphs_batched)
            loss = loss_mse + lambda_gradient * loss_consistency

            # Backpropagation
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        # Validation loop
        model.eval()  # Set the model to evaluation mode
        total_val_loss = 0.0
        with torch.no_grad():  # Disabling gradient calculation
            for batch_idx, (obj_name, rest_graphs, def_graphs, meta_data, collider_graphs) in enumerate(dataloader_val):
                rest_graphs_batched = Batch.from_data_list(rest_graphs)
                collider_graphs_batched = Batch.from_data_list(collider_graphs)
                def_graphs_batched = Batch.from_data_list(def_graphs)
                
                rest_graphs_batched,collider_graphs_batched,def_graphs_batched = rest_graphs_batched.to(device),collider_graphs_batched.to(device),def_graphs_batched.to(device)
                
                # Forward
                predictions = model(rest_graphs_batched, collider_graphs_batched)
                loss_mse = criterion_mse(predictions.pos, def_graphs_batched.pos)
                loss_consistency = criterion_grad(predictions, def_graphs_batched)
                loss_val = loss_mse + lambda_gradient * loss_consistency

                total_val_loss += loss_val.item()
        
        print(f"Epoch {epoch+1}/{config.training['n_epochs']} - Loss: {loss_mse.item()}")
        avg_val_loss = total_val_loss / len(dataloader_val)
        print(f"Epoch {epoch+1}/{config.training['n_epochs']} - Training Loss: {loss_mse.item()} - Validation Loss: {avg_val_loss}")
        
        # Logging validation loss to tensorboard
        writer.add_scalar('Validation Loss', avg_val_loss, epoch)

    torch.save(model.state_dict(), os.path.join(log_dir, 'model_weights.pth'))
    writer.close()
    return avg_val_loss

if __name__ == "__main__":
    config = Config()
    train(config)
