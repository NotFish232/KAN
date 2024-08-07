from pathlib import Path

import torch as T
from torch.utils.data import Dataset, TensorDataset

from utils import gaussian, partition_2d_graph
from utils.architecture import KAN_ARCHITECTURE, MLP_ARCHITECTURE
from utils.data_management import ExperimentDataType
from utils.experiment import run_experiment
from utils.training import TrainModelArguments

EXPERIMENT_NAME = Path(__file__).stem

NUM_PEAKS = 2
NUM_POINTS = 64
GAUSSIAN_STD_1 = 0.2
GAUSSIAN_STD_2 = 0.1

NUM_EPOCHS = 50


PARAMETER_COUNTS = [100, 1_000, 10_000]


def create_dataset(device: T.device) -> tuple[T.Tensor, T.Tensor]:
    axis = T.linspace(0, NUM_PEAKS, NUM_POINTS, device=device)
    X = T.cartesian_prod(axis, axis)
    Y = T.zeros((NUM_POINTS**2, 1), device=device)
    for i in range(NUM_PEAKS):
        for j in range(NUM_PEAKS):
            Y += T.cartesian_prod(
                gaussian(axis, i + 0.5, GAUSSIAN_STD_1),
                gaussian(axis, j + 0.5, GAUSSIAN_STD_2),
            ).sum(dim=-1, keepdim=True)

    return X, Y


def main() -> None:
    device = T.device("cuda" if T.cuda.is_available() else "cpu")

    X, Y = create_dataset(device)

    X_partitioned = list(partition_2d_graph(X, NUM_PEAKS))
    Y_partitioned = list(partition_2d_graph(Y, NUM_PEAKS))

    function_dataset = TensorDataset(X, Y)
    partitioned_datasets: list[Dataset] = []
    for X_batch, Y_batch in zip(X_partitioned, Y_partitioned):
        partitioned_datasets.append(TensorDataset(X_batch, Y_batch))

    run_experiment(
        EXPERIMENT_NAME,
        [(KAN_ARCHITECTURE[(2, 1)][p], p) for p in PARAMETER_COUNTS],
        [(MLP_ARCHITECTURE[(2, 1)][p], p) for p in PARAMETER_COUNTS],
        partitioned_datasets,
        {"eval": function_dataset},
        {"function": X},
        {"function": Y, "task": Y_partitioned},
        ExperimentDataType.function_2d,
        device=device,
        kan_kwargs={
            "grid_range": [0, NUM_PEAKS],
            "bias_trainable": False,
            "sp_trainable": False,
            "sb_trainable": False,
        },
        training_args=TrainModelArguments(num_epochs=NUM_EPOCHS),
    )


if __name__ == "__main__":
    main()
