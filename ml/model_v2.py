"""
Neo-Dock — ml/model_v2.py
===========================
GINEConv tabanlı Graph Neural Network mimarisi.

Mimari:
  1. Atom embedding: Linear(node_dim → hidden)
  2. N× GINEConv katmanları (bağ özellikli mesaj iletimi)
  3. Global mean pooling → molekül temsili
  4. MLP regresyon başı → skaler pKd tahmini

~350K parametre (hidden=128, n_layers=4)

Referans: Xu et al. "How Powerful are Graph Neural Networks?" (ICLR 2019)
GINE variant: Hu et al. "Strategies for Pre-training Graph Neural Networks" (ICLR 2020)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GINEConv, global_mean_pool, global_max_pool


class NeoDockGNN(nn.Module):
    """
    GINEConv GNN — protein-ligand bağlanma afinitesi (pKd) tahmini.
    
    Args:
        hidden_dim:   Gizli boyut (varsayılan 128)
        n_lig_layers: GINEConv katman sayısı (varsayılan 4)
        dropout:      Dropout oranı (eğitimde 0.1, inferenceda 0.0)
        use_pocket:   Protein cep özelliklerini kullan (varsayılan False)
        node_dim:     Atom özellik boyutu (varsayılan 79)
        edge_dim:     Bağ özellik boyutu (varsayılan 10)
    """

    def __init__(
        self,
        hidden_dim:   int  = 128,
        n_lig_layers: int  = 4,
        dropout:      float = 0.1,
        use_pocket:   bool  = False,
        node_dim:     int  = 79,
        edge_dim:     int  = 10,
    ):
        super().__init__()

        self.hidden_dim   = hidden_dim
        self.n_lig_layers = n_lig_layers
        self.dropout      = dropout
        self.use_pocket   = use_pocket

        # ── Atom giriş projeksiyonu ─────────────────────────
        self.node_emb = nn.Sequential(
            nn.Linear(node_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
        )

        # ── GINEConv katmanları ──────────────────────────────
        self.convs = nn.ModuleList()
        self.norms = nn.ModuleList()
        for _ in range(n_lig_layers):
            mlp = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim * 2),
                nn.BatchNorm1d(hidden_dim * 2),
                nn.ReLU(),
                nn.Linear(hidden_dim * 2, hidden_dim),
            )
            self.convs.append(GINEConv(mlp, edge_dim=edge_dim))
            self.norms.append(nn.LayerNorm(hidden_dim))

        # ── Pooling sonrası MLP ──────────────────────────────
        pool_dim = hidden_dim * 2   # mean + max pooling concat
        self.regressor = nn.Sequential(
            nn.Linear(pool_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
        )

    def forward(self, data) -> torch.Tensor:
        """
        Args:
            data: PyG Batch nesnesi (x, edge_index, edge_attr, batch)
        Returns:
            pKd tahminleri: Tensor [batch_size, 1]
        """
        x          = data.x
        edge_index = data.edge_index
        edge_attr  = data.edge_attr
        batch      = data.batch

        # 1. Atom embedding
        h = self.node_emb(x)

        # 2. GINEConv + skip connections
        for conv, norm in zip(self.convs, self.norms):
            h_new = conv(h, edge_index, edge_attr)
            h_new = norm(h_new)
            h_new = F.relu(h_new)
            h_new = F.dropout(h_new, p=self.dropout, training=self.training)
            h     = h + h_new   # residual

        # 3. Global pooling (mean + max)
        h_mean = global_mean_pool(h, batch)
        h_max  = global_max_pool(h, batch)
        h_pool = torch.cat([h_mean, h_max], dim=-1)

        # 4. pKd tahmini
        out = self.regressor(h_pool)
        return out

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
